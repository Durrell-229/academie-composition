import segno
import os
import io
import base64
from django.conf import settings

class QRService:
    @staticmethod
    def generate_access_qr(token, context="exam"):
        """
        Génère un QR code pour l'accès à une salle d'examen ou autre.
        """
        # Création du QR Code
        qr = segno.make(token, error='h')
        
        # Nom du fichier
        filename = f"qr_{context}_{token[:8]}.png"
        output_path = os.path.join(settings.MEDIA_ROOT, 'qr_codes', filename)
        
        # Créer le dossier s'il n'existe pas
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Sauvegarde
        qr.save(output_path, scale=10, dark='#6366F1')
        
        return os.path.join('qr_codes', filename)

    @staticmethod
    def generate_bulletin_qr(bulletin):
        """
        Génère un QR code SVG (data URI) pour un bulletin.
        Le QR contient l'URL publique de téléchargement du bulletin PDF.
        Retourne un data URI SVG utilisable directement dans un <img> HTML.
        """
        # Construire l'URL de téléchargement
        site_url = getattr(settings, 'SITE_URL', 'https://academie.onrender.com')
        download_url = f"{site_url}/bulletins/verify/{bulletin.verification_token}/download/"
        
        # Générer le QR code
        qr = segno.make(download_url, error='h')
        
        # Exporter en SVG
        svg_buffer = io.BytesIO()
        qr.save(svg_buffer, kind='svg', scale=10, dark='#000000', light='#ffffff')
        svg_bytes = svg_buffer.getvalue()
        
        # Convertir en data URI base64
        svg_b64 = base64.b64encode(svg_bytes).decode('utf-8')
        return f"data:image/svg+xml;base64,{svg_b64}"

    @staticmethod
    def generate_composition_qr(resultat):
        """
        Génère un QR code SVG (data URI) pour un bulletin de composition.
        Le QR contient l'URL publique de téléchargement du bulletin PDF.
        """
        site_url = getattr(settings, 'SITE_URL', 'https://academie.onrender.com')
        download_url = f"{site_url}/compositions/bulletin/{resultat.id}/download/"
        
        qr = segno.make(download_url, error='h')
        
        svg_buffer = io.BytesIO()
        qr.save(svg_buffer, kind='svg', scale=10, dark='#000000', light='#ffffff')
        svg_bytes = svg_buffer.getvalue()
        
        svg_b64 = base64.b64encode(svg_bytes).decode('utf-8')
        return f"data:image/svg+xml;base64,{svg_b64}"
