from io import BytesIO
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.conf import settings
import hashlib
import os


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
    def generate_bulletin_administratif_pdf(bulletin):
        """Génère un bulletin administratif PDF (format officiel Ministère Bénin)."""
        lignes = list(bulletin.lignes.all())
        
        # Calculer total moy*coeff
        total_moy_coeff = sum(l.note * l.coefficient for l in lignes) if lignes else 0

        context = {
            'bulletin': bulletin,
            'eleve': bulletin.eleve,
            'classe': bulletin.classe,
            'periode': bulletin.get_periode_display(),
            'moyenne': bulletin.moyenne_generale,
            'rang': bulletin.rang,
            'effectif': bulletin.effectif_total,
            'appreciation': bulletin.appreciation_ia,
            'decision': bulletin.decision_conseil,
            'annee_scolaire': bulletin.annee_scolaire,
            'lignes': lignes,
            'verification_token': bulletin.verification_token,
            'signature': hashlib.sha256(f"{bulletin.id}{bulletin.verification_token}".encode()).hexdigest()[:16],
            # Nouveaux champs
            'retards': bulletin.retards,
            'minutes_retard': bulletin.minutes_retard,
            'absences': bulletin.absences,
            'heures_absences': bulletin.heures_absences,
            'comportement': bulletin.comportement,
            'observation': bulletin.observation_conseil or "Travail satisfaisant. Continue dans cette voie.",
            'total_moy_coeff': round(total_moy_coeff, 2),
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
        """Génère un bulletin QCM PDF (format officiel Ministère Bénin)."""
        qcm_resultat = bulletin.qcm_resultats.first()

        context = {
            'bulletin': bulletin,
            'eleve': bulletin.eleve,
            'classe': bulletin.classe,
            'periode': bulletin.get_periode_display(),
            'moyenne': bulletin.moyenne_generale,
            'rang': bulletin.rang,
            'effectif': bulletin.effectif_total,
            'appreciation': bulletin.appreciation_ia,
            'decision': bulletin.decision_conseil,
            'annee_scolaire': bulletin.annee_scolaire,
            'lignes': bulletin.lignes.all(),
            'verification_token': bulletin.verification_token,
            'signature': hashlib.sha256(f"{bulletin.id}{bulletin.verification_token}".encode()).hexdigest()[:16],
            'matiere': bulletin.lignes.first().matiere if bulletin.lignes.exists() else '',
            'coefficient': bulletin.lignes.first().coefficient if bulletin.lignes.exists() else 1,
            'bonnes_reponses': qcm_resultat.bonnes_reponses if qcm_resultat else '-',
            'total_questions': qcm_resultat.total_questions if qcm_resultat else '-',
        }

        html = render_to_string('bulletins/bulletin_qcm_pdf.html', context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)

        if not pdf.err:
            pdf_content = result.getvalue()
            from django.core.files.base import ContentFile
            filename = f"bulletin_qcm_{bulletin.eleve.last_name}_{bulletin.created_at.strftime('%Y%m%d')}.pdf"
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
