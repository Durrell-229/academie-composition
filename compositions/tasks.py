import logging
import hashlib
from django.shortcuts import get_object_or_404
from .models import CompositionSession, Resultat
from ai_engine.multi_ai import multi_ai
from ai_engine.services import extract_text_from_file
from bulletins.services import BulletinService, link_callback
from io import BytesIO
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.core.files.base import ContentFile

from core.redis_tasks import redis_task

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
        session.statut = 'corrige'
        session.save()
        return f"Erreur: Aucun corrigé type pour {exam.titre}"
    
    # Vérifier que le fichier existe physiquement
    try:
        corrige_text = extract_text_from_file(corrige_file.fichier.path)
        # Hash du corrigé pour traçabilité
        corrige_hash = hashlib.sha256(corrige_text.encode('utf-8', errors='ignore')).hexdigest()[:16]
        corrige_doc_id = corrige_file.document_id  # ID unique du corrigé
        logger.info(f"[Correction] Corrigé type chargé: {corrige_file.fichier.path} (hash: {corrige_hash}, doc_id: {corrige_doc_id})")
    except Exception as e:
        logger.error(f"[Correction] Erreur lecture corrigé type: {e}")
        corrige_text = ""
    
    if not corrige_text.strip():
        logger.warning(f"[Correction] Corrigé type vide pour {exam.titre}")
    
    # ═══ 2. RÉCUPÉRATION DE LA COPIE DE L'ÉLÈVE ═══
    copie_text = ""
    submission_files = session.submission_files.all()
    files_info = []
    copie_doc_ids = []
    
    if submission_files.exists():
        for sub in submission_files:
            try:
                text = extract_text_from_file(sub.fichier.path)
                copie_text += text + "\n"
                doc_id = getattr(sub, 'document_id', f"COPIE-{sub.id.hex[:8]}")
                files_info.append({'file': str(sub.fichier.name), 'page': sub.page_number, 'document_id': doc_id})
                copie_doc_ids.append(doc_id)
                logger.info(f"[Correction] Copie page {sub.page_number} extraite: {sub.fichier.path} (doc_id: {doc_id})")
            except Exception as e:
                logger.warning(f"[Correction] Erreur extraction page {sub.page_number}: {e}")
    
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
    
    logger.info(f"[Correction] Appel IA avec corrigé ({len(corrige_text)} chars) et copie ({len(copie_text)} chars) — corrige:{corrige_doc_id} copie:{copie_doc_ids}")
    correction_result = multi_ai.correct_copy(corrige_text, copie_text, exam_info)

    # ═══ 4. ENREGISTREMENT DU RÉSULTAT ═══
    from django.utils import timezone
    note_finale = float(correction_result.get('note', 0))
    
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
            'corrige_at': timezone.now()
        }
    )
    
    logger.info(f"[Correction] Résultat enregistré: {note_finale}/{exam.note_maximale} - Mention: {mention}")
    
    # ═══ 5. GÉNÉRATION DU BULLETIN PDF ═══
    try:
        from bulletins.services import BulletinService
        from bulletins.coefficients_benin import get_coefficient as get_benin_coefficient
        from api.services.qr_service import QRService
        
        # Extraire la série de la classe de l'élève
        eleve = session.eleve
        classe = eleve.classe or ''
        serie = BulletinService._extract_serial(classe)
        
        # Obtenir le coefficient officiel
        matiere_nom = exam.matiere.nom if exam.matiere else ''
        coeff_officiel = get_benin_coefficient(matiere_nom, serie)

        from bulletins.services import get_logo_data_uri
        context = {
            'resultat': resultat,
            'annee_scolaire': '2025-2026',
            'serie': serie,
            'coefficient_officiel': coeff_officiel,
            'qr_data_uri': QRService.generate_composition_qr(resultat),
            'logo_data_uri': get_logo_data_uri(),
        }
        html = render_to_string('compositions/bulletin_composition_benin.html', context)
        pdf_file = BytesIO()
        pisa_status = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=pdf_file, link_callback=link_callback)
        
        if not pisa_status.err:
            pdf_content = pdf_file.getvalue()
            filename = f"bulletin_{session.eleve.last_name}_{exam.titre[:10]}.pdf"
            resultat.bulletin_pdf.save(filename, ContentFile(pdf_content), save=True)
            logger.info(f"[Correction] Bulletin PDF généré: {filename}")
    except Exception as e:
        logger.error(f"[Correction] Erreur génération bulletin PDF: {e}")

    # ═══ 6. MARQUER LA SESSION COMME CORRIGÉE ═══
    session.statut = 'corrige'
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
