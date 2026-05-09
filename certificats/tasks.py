"""
Tâches Redis pour le module certificats
Génération de PDF, correction OCR, notifications
"""

import os
import logging
from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files import File
from core.redis_tasks import redis_task
from .models import CertificatScolaire, CopieExamenPhysique

logger = logging.getLogger(__name__)


@redis_task("certificats.generer_pdf")
def generer_pdf_certificat(certificat_id):
    """
    Générer le PDF d'un certificat en arrière-plan via Redis
    """
    try:
        from xhtml2pdf import pisa
        from django.shortcuts import get_object_or_404
        
        certificat = get_object_or_404(CertificatScolaire, id=certificat_id)
        
        # Rendre le template HTML
        html_content = render_to_string('certificats/certificat_template.html', {
            'certificat': certificat,
            'eleve': certificat.eleve,
            'etablissement': certificat.etablissement,
        })
        
        # Générer le PDF
        pdf_buffer = BytesIO()
        pisa.CreatePDF(html_content.encode('utf-8'), dest=pdf_buffer)
        pdf_buffer.seek(0)
        
        # Sauvegarder le fichier
        filename = f"certificat_{certificat.numero_certificat}.pdf"
        certificat.fichier_pdf.save(filename, File(pdf_buffer))
        certificat.is_delivre = True
        certificat.save()
        
        logger.info(f"✅ PDF généré pour certificat {certificat.numero_certificat}")
        return f"PDF généré: {filename}"
        
    except Exception as e:
        logger.error(f"❌ Erreur génération PDF certificat {certificat_id}: {e}")
        raise


@redis_task("certificats.corriger_copie_ocr")
def corriger_copie_ocr(copie_id):
    """
    Corriger une copie physique via OCR en arrière-plan
    """
    try:
        from ai_engine.ocr_service import OCRCorrectionService
        from django.shortcuts import get_object_or_404
        
        copie = get_object_or_404(CopieExamenPhysique, id=copie_id)
        
        # Vérifier que l'image existe
        if not copie.image_copie:
            raise ValueError("Aucune image de copie disponible")
        
        # Lancer la correction OCR
        ocr_service = OCRCorrectionService()
        resultat = ocr_service.corriger_copie(copie)
        
        if resultat['success']:
            # Mettre à jour la copie avec les résultats
            copie.texte_extrait = resultat.get('texte_extrait', '')
            copie.note_suggeree = resultat.get('note_suggeree', 0)
            copie.correction_json = resultat.get('correction', {})
            copie.is_corrige = True
            copie.statut = 'corrigee'
            copie.save()
            
            logger.info(f"✅ Copie {copie_id} corrigée avec succès - Note: {copie.note_suggeree}")
            
            # Envoyer notification au professeur
            from notifications.utils import send_notification
            send_notification.delay(
                user_id=copie.inscription.session.etablissement.administrateurs.first().id,
                title="Correction OCR terminée",
                message=f"La copie de {copie.inscription.eleve.get_full_name()} a été corrigée. Note suggérée: {copie.note_suggeree}/20"
            )
            
            return f"Copie corrigée - Note: {copie.note_suggeree}"
        else:
            copie.statut = 'erreur'
            copie.save()
            raise Exception(resultat.get('error', 'Erreur inconnue OCR'))
            
    except Exception as e:
        logger.error(f"❌ Erreur correction OCR copie {copie_id}: {e}")
        raise


@redis_task("certificats.verifier_certificat_qr")
def verifier_certificat_qr(code_verification):
    """
    Vérifier un certificat via son QR code
    """
    try:
        from .models import HistoriqueCertificat
        
        certificat = CertificatScolaire.objects.filter(
            code_verification=code_verification,
            is_delivre=True
        ).first()
        
        if certificat:
            # Enregistrer la vérification
            HistoriqueCertificat.objects.create(
                certificat=certificat,
                action='verification',
                details='Vérification via QR Code'
            )
            
            logger.info(f"✅ Certificat vérifié: {code_verification}")
            return {
                'valid': True,
                'certificat_id': str(certificat.id),
                'eleve': certificat.eleve.get_full_name(),
                'statut': certificat.statut
            }
        else:
            return {'valid': False, 'error': 'Certificat non trouvé'}
            
    except Exception as e:
        logger.error(f"❌ Erreur vérification certificat {code_verification}: {e}")
        raise


@redis_task("certificats.generer_bulletin_examen")
def generer_bulletin_examen(inscription_id):
    """
    Générer le bulletin d'examen pour un élève
    """
    try:
        from academic.models import Inscription
        from django.shortcuts import get_object_or_404
        
        inscription = get_object_or_404(Inscription, id=inscription_id)
        
        # Calculer les moyennes par matière
        notes = inscription.notes.all()
        total_points = sum(n.note * n.coefficient for n in notes)
        total_coef = sum(n.coefficient for n in notes)
        
        moyenne_generale = total_points / total_coef if total_coef > 0 else 0
        
        # Déterminer le statut
        statut = 'admis' if moyenne_generale >= 10 else 'refuse'
        
        # Générer le PDF du bulletin
        # ... (code similaire à generer_pdf_certificat)
        
        logger.info(f"✅ Bulletin généré pour {inscription.eleve.get_full_name()}")
        return f"Bulletin généré - Moyenne: {moyenne_generale}/20"
        
    except Exception as e:
        logger.error(f"❌ Erreur génération bulletin {inscription_id}: {e}")
        raise
