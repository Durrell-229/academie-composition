import logging
import hashlib
import os
import tempfile
from django.shortcuts import get_object_or_404
from .models import CompositionSession, Resultat
from ai_engine.multi_ai import multi_ai
from ai_engine.nvidia_ocr import nvidia_ocr_service
from ai_engine.services import extract_text_from_file
from io import BytesIO
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.core.files.base import ContentFile
from django.conf import settings

from core.redis_tasks import redis_task


def _get_local_path(field_file):
    """
    Retourne un chemin local utilisable pour l'OCR.
    - Stockage local : retourne field_file.path directement.
    - Cloudinary / S3 : télécharge dans un fichier temporaire et retourne son chemin.
    Lève une exception si le téléchargement échoue.
    """
    try:
        path = field_file.path
        if os.path.exists(path):
            return path, False  # (chemin, is_temp)
    except (NotImplementedError, AttributeError, ValueError):
        pass

    # Fichier distant (Cloudinary / S3) — téléchargement
    import requests as req
    url = field_file.url
    resp = req.get(url, timeout=30)
    resp.raise_for_status()
    ext = os.path.splitext(field_file.name)[1] or '.bin'
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(resp.content)
    tmp.close()
    return tmp.name, True  # (chemin, is_temp)


def link_callback(uri, rel):
    """
    Résout les URIs (fichiers statiques / media) pour xhtml2pdf lors
    de la génération du bulletin PDF.
    """
    # Fichiers statiques
    static_root = getattr(settings, 'STATIC_ROOT', '') or ''
    static_url = getattr(settings, 'STATIC_URL', '/static/')
    media_root = getattr(settings, 'MEDIA_ROOT', '') or ''
    media_url = getattr(settings, 'MEDIA_URL', '/media/')

    if uri.startswith(media_url):
        path = os.path.join(media_root, uri[len(media_url):])
    elif uri.startswith(static_url):
        path = os.path.join(static_root, uri[len(static_url):])
    else:
        return uri

    if not os.path.isfile(path):
        return uri
    return path

logger = logging.getLogger(__name__)


@redis_task('process_ia_correction')
def process_ia_correction(session_id):
    """Correction asynchrone via IA avec chaîne de vérification stricte."""
    try:
        session = CompositionSession.objects.get(id=session_id)
    except CompositionSession.DoesNotExist:
        logger.error(f"Session {session_id} introuvable.")
        return f"Erreur: Session {session_id} introuvable."
    
    exam = session.exam
    logger.info(f"[Correction] Début pour session {session_id}, examen: {exam.titre}")

    # Marquer la session comme en cours de correction IA
    session.statut = CompositionSession.Statut.EN_CORRECTION
    session.save(update_fields=['statut'])

    # ═══ 1. VÉRIFICATION STRICTE DU CORRIGÉ TYPE ═══
    corrige_file = exam.files.filter(type_fichier='corrige_type').first()
    corrige_text = ""
    corrige_hash = ""
    corrige_doc_id = ""
    
    if not corrige_file:
        logger.error(f"[Correction] AUCUN CORRIGÉ TYPE pour l'examen {exam.id} - {exam.titre}")
        # Créer un résultat avec erreur explicite
        Resultat.objects.update_or_create(
            session=session,
            defaults={
                'note': 0,
                'note_sur': exam.note_maximale,
                'mention': '',
                'appreciation': f"ERREUR : Aucun corrigé type n'a été fourni pour cet examen par l'administration. Veuillez contacter un professeur ou administrateur pour régulariser.",
                'corrige_par_ia': False,
                'details_correction': {'error': 'no_corrige_type', 'exam_id': str(exam.id)},
            }
        )
        session.statut = CompositionSession.Statut.CORRIGE
        session.save()
        return f"Erreur: Aucun corrigé type pour {exam.titre}"
    
    # Charger le corrigé type (local ou Cloudinary/S3)
    corrige_local_path = None
    corrige_is_temp = False
    try:
        corrige_local_path, corrige_is_temp = _get_local_path(corrige_file.fichier)
        corrige_text = extract_text_from_file(corrige_local_path)
        corrige_hash = hashlib.sha256(corrige_text.encode('utf-8', errors='ignore')).hexdigest()[:16]
        corrige_doc_id = corrige_file.document_id
        logger.info(f"[Correction] Corrigé type chargé (hash: {corrige_hash}, doc_id: {corrige_doc_id})")
    except Exception as e:
        logger.error(f"[Correction] Erreur lecture corrigé type: {e}")
        corrige_text = ""
    finally:
        if corrige_is_temp and corrige_local_path and os.path.exists(corrige_local_path):
            os.unlink(corrige_local_path)
    
    if not corrige_text.strip():
        logger.warning(f"[Correction] Corrigé type vide pour {exam.titre}")
    
    # ═══ 2. RÉCUPÉRATION DE LA COPIE DE L'ÉLÈVE ═══
    copie_text = ""
    submission_files = session.submission_files.all()
    files_info = []
    copie_doc_ids = []
    
    image_paths = []
    temp_paths_to_cleanup = []
    if submission_files.exists():
        for sub in submission_files:
            try:
                doc_id = getattr(sub, 'document_id', f"COPIE-{sub.id.hex[:8]}")
                files_info.append({'file': str(sub.fichier.name), 'page': sub.page_number, 'document_id': doc_id})
                copie_doc_ids.append(doc_id)

                local_path, is_temp = _get_local_path(sub.fichier)
                image_paths.append(local_path)
                if is_temp:
                    temp_paths_to_cleanup.append(local_path)
                try:
                    # OCR via nemotron-ocr-v1 (haute précision)
                    ocr_result = nvidia_ocr_service.extract_text_from_image(local_path)
                    if ocr_result.get('success') and ocr_result.get('text', '').strip():
                        copie_text += ocr_result['text'] + "\n"
                        logger.info(f"[Correction] OCR Nemotron page {sub.page_number}: {len(ocr_result['text'])} chars (conf: {ocr_result.get('confidence', 0):.0f}%)")
                    else:
                        # Fallback Tesseract si Nemotron OCR échoue
                        text = extract_text_from_file(local_path)
                        if text.strip():
                            copie_text += text + "\n"
                            logger.info(f"[Correction] Fallback Tesseract page {sub.page_number}: {len(text)} chars")
                except Exception as e_ocr:
                    logger.warning(f"[Correction] Erreur OCR page {sub.page_number}: {e_ocr}")
            except Exception as e:
                logger.warning(f"[Correction] Erreur page {sub.page_number}: {e}")
    
    # Réponses texte directes (TinyMCE)
    answers = session.answers.all()
    if answers.exists():
        for answer in answers:
            copie_text += f"\nQuestion {answer.question_number}: {answer.content}\n"
        logger.info(f"[Correction] {answers.count()} réponses texte trouvées")

    if not copie_text.strip() and not submission_files.exists():
        logger.warning(f"[Correction] Copie vide pour {session.eleve.full_name}")

    # ═══ 3. APPEL AU SERVICE IA ═══
    exam_info = {
        'titre': exam.titre,
        'matiere': exam.matiere.nom if exam.matiere else 'Non spécifiée',
        'note_maximale': float(exam.note_maximale),
        'niveau': exam.matiere.niveau if hasattr(exam.matiere, 'niveau') else 'Secondaire',
        'corrige_doc_id': corrige_doc_id,
        'copie_doc_ids': copie_doc_ids,
        'session_id': str(session.id),
    }
    
    logger.info(f"[Correction] Appel NVIDIA vision: {len(image_paths)} image(s) + corrigé {len(corrige_text)} chars — corrige:{corrige_doc_id} copie:{copie_doc_ids}")
    correction_result = {}
    try:
        correction_result = multi_ai.correct_copy(corrige_text, copie_text, exam_info, image_paths=image_paths)
    except Exception as e:
        logger.error(f"[Correction] Erreur appel IA: {e}")
        correction_result = {
            'note': 0,
            'appreciation': f"Erreur lors de la correction automatique : {e}",
            'details': [],
            'points_forts_global': '',
            'axes_amelioration': '',
        }
    finally:
        for _tmp_path in temp_paths_to_cleanup:
            try:
                if os.path.exists(_tmp_path):
                    os.unlink(_tmp_path)
            except Exception:
                pass

    # ═══ 4. ENREGISTREMENT DU RÉSULTAT ═══
    from django.utils import timezone

    # Détecter une erreur technique (IA indisponible ou note null)
    note_brute = correction_result.get('note')
    erreur_technique = correction_result.get('erreur_technique', False) or note_brute is None

    if erreur_technique or note_brute is None:
        # Pas de note valide : marquer comme erreur, ne pas mettre 0
        Resultat.objects.update_or_create(
            session=session,
            defaults={
                'note': 0,
                'note_sur': exam.note_maximale,
                'mention': '',
                'appreciation': correction_result.get('appreciation', 'Erreur technique lors de la correction. Veuillez réessayer ou contacter un administrateur.'),
                'corrige_par_ia': False,
                'details_correction': {
                    'erreur': True,
                    'message': correction_result.get('appreciation', ''),
                    'conseil': 'Vérifiez les clés API dans le fichier .env et relancez la correction.',
                },
            }
        )
        session.statut = CompositionSession.Statut.EN_ATTENTE
        session.save()
        logger.error(f"[Correction] Erreur technique pour session {session_id} — note non attribuée")
        return f"Erreur technique correction — session {session_id}"

    note_finale = float(note_brute)

    # Validation de la note
    if note_finale < 0:
        note_finale = 0
    if note_finale > exam_info['note_maximale']:
        note_finale = exam_info['note_maximale']

    # Calcul de la mention
    mention = ''
    if note_finale >= 16: mention = 'excellent'
    elif note_finale >= 14: mention = 'tres_bien'
    elif note_finale >= 12: mention = 'bien'
    elif note_finale >= 10: mention = 'assez_bien'
    elif note_finale >= 8: mention = 'passable'
    else: mention = 'insuffisant'
    
    # ═══ 4a. VÉRIFICATION D'ACCÈS PAYWALL ═══
    from .access import verifier_acces_correction, construire_apercu
    a_acces, raison_acces = verifier_acces_correction(session.eleve, session)
    apercu = construire_apercu(correction_result, float(exam.note_maximale))
    logger.info(f"[Correction] Accès paywall: {a_acces} ({raison_acces}) — élève {session.eleve.id}")

    resultat, created = Resultat.objects.update_or_create(
        session=session,
        defaults={
            'note': note_finale,
            'note_sur': exam.note_maximale,
            'mention': mention,
            'appreciation': correction_result.get('appreciation', ''),
            'corrige_par_ia': True,
            'details_correction': {
                'details': correction_result.get('details', []),
                'points_forts': correction_result.get('points_forts_global', ''),
                'axes_amelioration': correction_result.get('axes_amelioration', ''),
                'corrige_hash': corrige_hash,
                'corrige_doc_id': corrige_doc_id,
                'copie_doc_ids': copie_doc_ids,
                'files_info': files_info,
                'nb_files': submission_files.count(),
                'has_text_answer': answers.exists(),
            },
            'corrige_at': timezone.now(),
            'correction_complete': a_acces,    # True ssi abonné ou déjà payé
            'apercu_correction': apercu,       # toujours stocké pour le paywall
        }
    )

    logger.info(f"[Correction] Résultat enregistré: {note_finale}/{exam.note_maximale} - Mention: {mention} - Paywall: {not a_acces}")

    # ═══ 5. GÉNÉRATION DU BULLETIN PDF ═══
    try:
        eleve = session.eleve
        classe_str = eleve.classe or ''

        # Coefficient officiel (extraction de la série si dispo)
        serie = ''
        for token in classe_str.upper().split():
            if token in ('A', 'B', 'C', 'D', 'E', 'F', 'G'):
                serie = token
                break

        coeff_officiel = float(exam.coefficient or 1)
        matiere_nom = exam.matiere.nom if exam.matiere else exam.titre

        context = {
            'resultat': resultat,
            'annee_scolaire': '2025-2026',
            'serie': serie,
            'coefficient_officiel': coeff_officiel,
            'matiere_nom': matiere_nom,
            'qr_data_uri': None,
            'logo_data_uri': None,
        }

        # Tenter le QR optionnel
        try:
            from api.services.qr_service import QRService
            context['qr_data_uri'] = QRService.generate_composition_qr(resultat)
        except Exception:
            pass

        from compositions.views import _get_bulletin_template, _build_composition_bulletin_context
        bulletin_template = _get_bulletin_template(exam.type_exam)
        html = render_to_string(bulletin_template, _build_composition_bulletin_context(resultat))
        pdf_file = BytesIO()
        pisa_status = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=pdf_file, link_callback=link_callback)

        if not pisa_status.err:
            pdf_content = pdf_file.getvalue()
            filename = f"bulletin_{eleve.last_name}_{exam.titre[:10]}.pdf"
            resultat.bulletin_pdf.save(filename, ContentFile(pdf_content), save=True)
            logger.info(f"[Correction] Bulletin PDF généré: {filename}")
    except Exception as e:
        logger.error(f"[Correction] Erreur génération bulletin PDF: {e}")

    # ═══ 6. STATUT SESSION ═══
    session.statut = CompositionSession.Statut.CORRIGE if a_acces else CompositionSession.Statut.BLOQUE
    session.save()
    
    # ═══ 7. GAMIFICATION (XP) ═══
    try:
        from gamification.models import XPAction
        XPAction.objects.create(
            user=session.eleve,
            action='EXAM_COMPLETE',
            points_gagnes=50,
            description=f"Examen terminé : {exam.titre}"
        )
    except Exception as e:
        logger.warning(f"[Correction] Erreur gamification: {e}")

    # ═══ 8. NOTIFICATION ═══
    try:
        from notifications.utils import send_notification
        send_notification(
            user=session.eleve,
            title="Correction Terminée !",
            message=f"Votre copie pour l'examen '{exam.titre}' a été corrigée par l'IA. Note : {correction_result.get('note', 0)}/{exam.note_maximale}",
            type='BULLETIN'
        )
    except Exception as e:
        logger.warning(f"[Correction] Erreur notification: {e}")

    # ═══ 9. CERTIFICAT AUTOMATIQUE (excellence) ═══
    try:
        if note_finale >= 16:
            from certifications.models import Certificate
            cert = Certificate.objects.create(
                eleve=session.eleve,
                type_certificat='excellence' if note_finale >= 18 else 'mention',
                titre=f"Certificat d'Excellence - {exam.titre}",
                description=f"Note exceptionnelle de {note_finale}/{exam.note_maximale} en {exam.matiere.nom if exam.matiere else exam.titre}",
                examen=session,
                note_obtenue=note_finale,
                note_sur=exam.note_maximale,
                mention=resultat.mention,
                matiere=exam.matiere,
                institution=session.eleve.classe or 'Académie Numérique',
            )
            cert.generate_code_verification()
            cert.generate_signature()
            cert.save()
            from certifications.tasks import generate_certificate_pdf
            generate_certificate_pdf.delay(str(cert.id))
            logger.info(f"[Correction] Certificat généré: {cert.id}")
    except Exception as e:
        logger.warning(f"[Correction] Erreur certificat: {e}")
    
    return f"Correction terminée pour {session.eleve.email} — Note: {note_finale}/{exam.note_maximale}"
