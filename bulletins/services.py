from io import BytesIO
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.conf import settings
import hashlib

class BulletinService:
    @staticmethod
    def generate_bulletin_administratif_pdf(bulletin):
        """Génère un bulletin administratif PDF (format officiel Ministère)."""
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
        }
        
        html = render_to_string('bulletins/bulletin_administratif_pdf.html', context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
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
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
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
        # Récupérer le QCMResultat lié
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
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

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
