from io import BytesIO
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.conf import settings
from django.core.files.base import ContentFile
import hashlib
import os
import base64
import logging

from .coefficients_benin import get_coefficient as get_benin_coefficient
from .data_aggregator import BulletinDataAggregator
from .image_generator import ImageBulletinGenerator, BulletinImageValidator
from api.services.qr_service import QRService

logger = logging.getLogger(__name__)

_logo_cache = {}

def get_logo_data_uri(small=True):
    """Retourne le logo comme data URI base64 (small=True pour les PDFs)."""
    fname = 'logo_small.png' if small else 'logo.png'
    if fname in _logo_cache:
        return _logo_cache[fname]
    candidates = []
    for d in getattr(settings, 'STATICFILES_DIRS', []):
        candidates.append(os.path.join(str(d), 'img', fname))
    candidates.append(os.path.join(str(settings.STATIC_ROOT or ''), 'img', fname))
    candidates.append(os.path.join(str(settings.BASE_DIR), 'static', 'img', fname))
    for path in candidates:
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')
            _logo_cache[fname] = f"data:image/png;base64,{data}"
            return _logo_cache[fname]
    return ''


def link_callback(uri, rel):
    """Convert media/static URLs to absolute file paths for xhtml2pdf."""
    import urllib.parse
    import logging

    logger = logging.getLogger(__name__)

    if not uri:
        return uri

    # Skip external URLs (http, https, data URIs)
    if uri.startswith(('http://', 'https://', 'data:')):
        return uri

    # Decode URL-encoded characters (e.g. %20 for spaces)
    uri = urllib.parse.unquote(uri)

    # Handle media files
    if uri.startswith(settings.MEDIA_URL):
        rel_path = uri[len(settings.MEDIA_URL):]
        abs_path = os.path.join(str(settings.MEDIA_ROOT), rel_path)
        # Normalize path for Windows
        abs_path = os.path.normpath(abs_path)
        # Check if file exists
        if not os.path.exists(abs_path):
            logger.warning(f"[link_callback] File not found: {abs_path}")
        else:
            logger.debug(f"[link_callback] Resolved: {uri} -> {abs_path}")
        return abs_path

    # Handle static files
    if uri.startswith(settings.STATIC_URL):
        rel_path = uri[len(settings.STATIC_URL):]
        abs_path = os.path.join(str(settings.STATIC_ROOT), rel_path)
        abs_path = os.path.normpath(abs_path)
        if not os.path.exists(abs_path):
            logger.warning(f"[link_callback] Static file not found: {abs_path}")
        return abs_path

    # Handle relative paths starting with /media/ or /static/
    if uri.startswith('/media/'):
        rel_path = uri[7:]  # strip '/media/'
        abs_path = os.path.join(str(settings.MEDIA_ROOT), rel_path)
        abs_path = os.path.normpath(abs_path)
        if not os.path.exists(abs_path):
            logger.warning(f"[link_callback] File not found (/media/): {abs_path}")
        return abs_path

    if uri.startswith('/static/'):
        rel_path = uri[8:]  # strip '/static/'
        abs_path = os.path.join(str(settings.STATIC_ROOT), rel_path)
        abs_path = os.path.normpath(abs_path)
        if not os.path.exists(abs_path):
            logger.warning(f"[link_callback] Static file not found (/static/): {abs_path}")
        return abs_path

    # Already absolute path or other URL — return as-is
    return uri


class BulletinService:
    @staticmethod
    def build_professional_context(bulletin):
        """Construit le contexte pour le template professionnel bulletin.html"""
        from django.utils.dateformat import format as date_format
        from datetime import datetime

        eleve = bulletin.eleve
        classe = bulletin.classe or (eleve.classe if eleve else '')

        # Récupérer les données agrégées
        data = BulletinDataAggregator.aggregate_notes(
            eleve,
            classe,
            bulletin.periode,
            bulletin.annee_scolaire
        )

        matieres_formatted = []
        total_coef = 0
        total_moy_coef = 0
        moyennes_finales = []

        for mat in data.get('matieres', []):
            coef = mat.get('coefficient', 1)
            moy_finale = mat.get('moyenne_finale', 0)
            moy_coef = round(moy_finale * coef, 2) if moy_finale else 0

            matieres_formatted.append({
                'nom': mat.get('nom', ''),
                'coef': coef,
                'interro': mat.get('moy_interrogations', ''),
                'dev1': '',  # À adapter selon les données
                'dev2': '',
                'dev3': '',
                'moyenne': round(moy_finale, 2),
                'moy_coef': moy_coef,
                'rang': mat.get('rang', ''),
                'appreciation': mat.get('appreciation', ''),
            })

            total_coef += coef
            total_moy_coef += moy_coef
            moyennes_finales.append(moy_finale)

        moyenne_trimestre = round(sum(moyennes_finales) / len(moyennes_finales), 2) if moyennes_finales else 0

        # Déterminer la mention
        mention = ''
        if moyenne_trimestre >= 16:
            mention = 'Excellent'
        elif moyenne_trimestre >= 14:
            mention = 'Très Bien'
        elif moyenne_trimestre >= 12:
            mention = 'Bien'
        elif moyenne_trimestre >= 10:
            mention = 'Assez Bien'
        elif moyenne_trimestre >= 8:
            mention = 'Moyen'
        else:
            mention = 'Faible'

        # Avis du conseil
        avis = {
            'felicitations': moyenne_trimestre >= 16,
            'tableau_honneur': moyenne_trimestre >= 14,
            'encouragement': moyenne_trimestre >= 12 and moyenne_trimestre < 14,
            'avertissement': moyenne_trimestre < 8,
            'blame': False,
        }

        # Décision
        decision = 'passe' if moyenne_trimestre >= 8 else 'redouble'
        if getattr(bulletin, 'decision_conseil', '').lower() == 'exclu':
            decision = 'exclu'

        # Année scolaire
        annee_parts = (bulletin.annee_scolaire or '2025-2026').split('-')
        annee = {
            'debut': annee_parts[0][-2:] if len(annee_parts) > 0 else '25',
            'fin': annee_parts[1][-2:] if len(annee_parts) > 1 else '26',
        }

        # Infos élève
        eleve_info = {
            'nom_prenoms': f"{eleve.last_name or ''} {eleve.first_name or ''}".upper().strip(),
            'date_naissance': getattr(eleve, 'date_of_birth', None) or '',
            'lieu_naissance': getattr(eleve, 'place_of_birth', '') or '',
            'sexe': getattr(eleve, 'gender', 'M'),
            'classe': classe,
            'effectif': data.get('effectif', ''),
            'matricule': getattr(eleve, 'matricule', '') or '',
            'statut': 'Nouveau',
        }

        # Établissement (à adapter selon la configuration)
        etablissement = {
            'bp': '___',
            'tel': '___',
            'ville': 'Cotonou',
        }

        context = {
            'logo_benin': '',
            'etablissement': etablissement,
            'annee': annee,
            'trimestre': int(str(bulletin.periode)[0]) if bulletin.periode else 1,
            'eleve': eleve_info,
            'matieres': matieres_formatted,
            'totaux': {
                'coef': total_coef,
                'moy_coef': round(total_moy_coef, 2),
            },
            'moyenne_trimestre': round(moyenne_trimestre, 2),
            'resultats': {
                'moyenne': f"{round(moyenne_trimestre, 2)}".replace('.', ','),
                'rang': f"{data.get('rang_classe', '—')} / {data.get('effectif', '')}",
                'plus_forte': '—',
                'plus_faible': '—',
                'moyenne_classe': '—',
                'mention': mention,
            },
            'avis': avis,
            'decision': decision,
            'fait_a': 'Cotonou',
            'fait_le': date_format(datetime.now(), 'd/m/Y'),
        }

        return context

    @staticmethod
    def generate_bulletin_administratif_pdf(bulletin):
        """Génère un bulletin administratif PDF (format officiel Ministère Bénin)."""
        lignes = list(bulletin.lignes.all())
        eleve = bulletin.eleve
        
        # Déterminer la série depuis la classe de l'élève
        classe = bulletin.classe or (eleve.classe if eleve else '')
        serie = BulletinService._extract_serial(classe)
        
        # Appliquer les coefficients officiels béninois
        for ligne in lignes:
            coeff_officiel = get_benin_coefficient(ligne.matiere, serie)
            # Utiliser le coefficient officiel s'il est plus grand que celui défini
            if ligne.coefficient < coeff_officiel:
                ligne.coefficient = coeff_officiel
        
        # Calculer total moy*coeff
        total_moy_coeff = sum(l.note * l.coefficient for l in lignes) if lignes else 0
        total_coeffs = sum(l.coefficient for l in lignes) if lignes else 1
        moyenne_calculee = round(total_moy_coeff / total_coeffs, 2) if total_coeffs > 0 else bulletin.moyenne_generale

        context = {
            'bulletin': bulletin,
            'eleve': eleve,
            'classe': classe,
            'serie': serie,
            'periode': bulletin.get_periode_display(),
            'moyenne': bulletin.moyenne_generale,
            'moyenne_calculee': moyenne_calculee,
            'rang': bulletin.rang,
            'effectif': bulletin.effectif_total,
            'appreciation': bulletin.appreciation_ia,
            'decision': bulletin.decision_conseil,
            'annee_scolaire': bulletin.annee_scolaire,
            'lignes': lignes,
            'verification_token': bulletin.verification_token,
            'signature': hashlib.sha256(f"{bulletin.id}{bulletin.verification_token}".encode()).hexdigest()[:16],
            # Absences & comportement
            'retards': bulletin.retards,
            'minutes_retard': bulletin.minutes_retard,
            'absences': bulletin.absences,
            'heures_absences': bulletin.heures_absences,
            'absences_just': bulletin.absences,
            'heures_just': bulletin.heures_absences,
            'absences_nonjust': 0,
            'heures_nonjust': 0,
            'heures_perdues': bulletin.heures_absences,
            'comportement': bulletin.comportement,
            'comportement_assiduite': bulletin.comportement_assiduite,
            'comportement_discipline': bulletin.comportement_discipline,
            'comportement_travail': bulletin.comportement_travail,
            'comportement_presentation': bulletin.comportement_discipline,
            'comportement_ponctualite': bulletin.comportement_ponctualite,
            'observation': bulletin.observation_conseil or "Travail satisfaisant. Continue dans cette voie.",
            'total_moy_coeff': round(total_moy_coeff, 2),
            'total_coeffs': round(total_coeffs, 2),
            # QR Code
            'qr_data_uri': QRService.generate_bulletin_qr(bulletin),
            # Logo
            'logo_data_uri': get_logo_data_uri(),
        }

        html = render_to_string('bulletins/bulletin_administratif_pdf.html', context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)

        if not pdf.err:
            pdf_content = result.getvalue()
            from django.core.files.base import ContentFile
            filename = f"bulletin_admin_{bulletin.eleve.last_name}_{bulletin.periode}_{bulletin.annee_scolaire}.pdf"
            bulletin.file_pdf.save(filename, ContentFile(pdf_content), save=True)
            return pdf_content
        return None

    @staticmethod
    def generate_bulletin_professionnel_pdf(bulletin):
        """Génère un bulletin professionnel PDF (format entreprise/corporate)."""
        context = {
            'bulletin': bulletin,
            'eleve': bulletin.eleve,
            'classe': bulletin.classe,
            'periode': bulletin.get_periode_display(),
            'moyenne': bulletin.moyenne_generale,
            'rang': bulletin.rang,
            'effectif': bulletin.effectif_total,
            'appreciation': bulletin.appreciation_ia,
            'annee_scolaire': bulletin.annee_scolaire,
            'lignes': bulletin.lignes.all(),
            'verification_token': bulletin.verification_token,
            'signature': hashlib.sha256(f"{bulletin.id}{bulletin.verification_token}".encode()).hexdigest()[:16],
            'qr_data_uri': QRService.generate_bulletin_qr(bulletin),
        }

        html = render_to_string('bulletins/bulletin_professionnel_pdf.html', context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)

        if not pdf.err:
            pdf_content = result.getvalue()
            from django.core.files.base import ContentFile
            filename = f"bulletin_pro_{bulletin.eleve.last_name}_{bulletin.periode}_{bulletin.annee_scolaire}.pdf"
            bulletin.file_pdf.save(filename, ContentFile(pdf_content), save=True)
            return pdf_content
        return None

    @staticmethod
    def generate_bulletin_qcm_pdf(bulletin):
        """Génère un bulletin QCM PDF (format professionnel Bénin)."""
        from datetime import datetime

        qcm_resultat = bulletin.qcm_resultats.first()
        eleve = bulletin.eleve

        # Déterminer la série depuis la classe de l'élève
        classe = bulletin.classe or (eleve.classe if eleve else '')
        serie = BulletinService._extract_serial(classe)

        # Récupérer la matière et appliquer le coefficient officiel
        ligne = bulletin.lignes.first()
        matiere_nom = ligne.matiere if ligne else (qcm_resultat.matiere if qcm_resultat else '')
        coefficient_officiel = get_benin_coefficient(matiere_nom, serie)

        # Toujours appliquer le coefficient officiel s'il est plus grand que celui défini
        if ligne and coefficient_officiel > ligne.coefficient:
            ligne.coefficient = coefficient_officiel
            ligne.save(update_fields=['coefficient'])
            logger.info(f"[QCM Bulletin] Coefficient appliqué: {matiere_nom} ({serie}) = {coefficient_officiel}")

        # Calculer les valeurs mathématiques pour le template
        moyenne_pourcentage = float(bulletin.moyenne_generale) * 5

        # Calculer le taux de réussite
        br = qcm_resultat.bonnes_reponses if qcm_resultat else 0
        tq = qcm_resultat.total_questions if qcm_resultat else 0
        taux_reussite = round((br * 100 / tq), 2) if tq > 0 else 0

        # Format infos élève pour le template
        nom_parts = (eleve.last_name or '').split()
        prenom = eleve.first_name or ''

        # Date format
        now = datetime.now()

        context = {
            'annee_scolaire': bulletin.annee_scolaire or '2025-2026',
            'periode': bulletin.get_periode_display() or 'Trimestre 1',
            'eleve': {
                'nom': nom_parts[0].upper() if nom_parts else '',
                'prenoms': prenom.upper(),
                'matricule': getattr(eleve, 'matricule', '') or '',
                'classe': classe,
            },
            'matiere': {
                'nom': matiere_nom or 'QCM',
                'coef': coefficient_officiel or 1,
                'note': round(bulletin.moyenne_generale, 2) if bulletin.moyenne_generale else '',
                'observations': f"Taux de réussite: {taux_reussite}% ({br}/{tq})" if tq > 0 else '',
            },
            'moyenne_arrivage': f"{taux_reussite}%",
            'moyenne_arrivage_2': f"{round(bulletin.moyenne_generale, 2)}/20",
            'observations_classe': bulletin.observation_conseil or '',
            'date_jour': now.day,
            'date_mois': now.month,
            'date_annee': now.year,
            'signature_prof': '',
            'signature_chef': '',
        }

        html = render_to_string('bulletins/bulletin_qcm.html', context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)

        if not pdf.err:
            pdf_content = result.getvalue()
            from django.core.files.base import ContentFile
            filename = f"bulletin_qcm_{eleve.last_name}_{bulletin.created_at.strftime('%Y%m%d')}.pdf"
            bulletin.file_pdf.save(filename, ContentFile(pdf_content), save=True)
            return pdf_content
        return None

    @staticmethod
    def generate_bulletin_pdf(submission):
        """
        Génère un bulletin PDF à partir d'une soumission (CorrectionCopie).
        Méthode legacy pour compatibilité.
        """
        context = {
            'student': submission.student,
            'exam': submission.exam,
            'grade': submission.grade or "Non noté",
            'feedback': submission.corrected_text,
            'date': submission.created_at,
        }
        
        html = render_to_string('bulletins/bulletin_template.html', context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            return result.getvalue()
        return None

    @staticmethod
    def generate_pdf_from_bulletin(bulletin):
        """Alias pour compatibilité — génère un bulletin administratif PDF."""
        return BulletinService.generate_bulletin_administratif_pdf(bulletin)

    @staticmethod
    def _extract_serial(classe):
        """
        Extrait la série (A1, A2, B, C, D, E, G1, G2, G3) du nom de classe.
        Ne retourne JAMAIS "bepc" car ce n'est pas un examen.
        Exemples:
            "Terminale C" -> "C"
            "Terminale D" -> "D"
            "Terminale A1" -> "A1"
            "Terminale G2" -> "G2"
            "3ème" -> "Premier Cycle"
            "Terminale" sans série -> "Second Cycle"
        """
        if not classe:
            return "N/A"
        
        classe_upper = classe.upper().strip()
        
        # Si c'est une classe du premier cycle (6ème, 5ème, 4ème, 3ème, 2nde)
        premier_cycle = ["6EME", "5EME", "4EME", "3EME", "2NDE", "SECONDE"]
        if any(c in classe_upper for c in premier_cycle):
            return "Premier Cycle"
        
        # Pour le second cycle (1ère, Terminale), chercher la série
        # Ordre: plus long d'abord pour éviter G1 -> G
        series_ordered = ["G1", "G2", "G3", "A1", "A2", "C", "D", "E", "B"]
        for serie in series_ordered:
            if serie in classe_upper:
                return serie
        
        # Par défaut, Second Cycle (pas de série détectée mais classe du second cycle)
        return "Second Cycle"

    @staticmethod
    def generate_bulletin_from_image_pdf(bulletin):
        """
        Génère un bulletin PDF avec template HTML + image bulletin.png comme fond.
        Garantit positionnement précis et fidélité au format officiel.

        Args:
            bulletin: Modèle Bulletin Django

        Returns:
            bytes: PDF content ou None si erreur
        """
        logger = logging.getLogger(__name__)

        try:
            # 1. Valider que bulletin.png existe
            is_valid, msg = BulletinImageValidator.validate_image()
            if not is_valid:
                logger.error(f"Image bulletin invalide: {msg}")
                return None

            # 2. Agréger les données depuis toutes les sources
            data = BulletinDataAggregator.aggregate_notes(
                eleve=bulletin.eleve,
                classe=bulletin.classe or getattr(bulletin.eleve, 'classe', None),
                periode=bulletin.periode,
                annee_scolaire=bulletin.annee_scolaire
            )

            logger.info(f"Données agrégées pour bulletin {bulletin.id}: moy={data['moyenne_generale']}, rang={data['rang']}")

            # 3. Utiliser le template professionnel avec le contexte adapté
            context = BulletinService.build_professional_context(bulletin)

            # 4. Render le nouveau template professionnel
            html_content = render_to_string('bulletins/bulletin.html', context)

            # 5. Convertir HTML en PDF avec xhtml2pdf
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(
                html_content,
                pdf_buffer,
                link_callback=link_callback
            )

            if pisa_status.err:
                logger.error(f"Erreur xhtml2pdf: {pisa_status.err}")
                return None

            pdf_bytes = pdf_buffer.getvalue()

            if not pdf_bytes:
                logger.error(f"Erreur génération PDF pour bulletin {bulletin.id}")
                return None

            # 6. Sauvegarder le fichier PDF
            filename = f"bulletin_{bulletin.eleve.last_name}_{bulletin.periode}_{bulletin.annee_scolaire}.pdf"
            bulletin.file_pdf.save(filename, ContentFile(pdf_bytes), save=True)

            # 7. Mettre à jour le modèle Bulletin avec les données calculées
            bulletin.moyenne_generale = data['moyenne_generale']
            bulletin.rang = data['rang']
            bulletin.effectif_total = data['effectif']
            bulletin.save()

            logger.info(f"Bulletin {bulletin.id} généré avec succès (moy={data['moyenne_generale']:.2f})")
            return pdf_bytes

        except FileNotFoundError as e:
            logger.error(f"Fichier manquant: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur génération bulletin PDF: {e}", exc_info=True)
            return None
