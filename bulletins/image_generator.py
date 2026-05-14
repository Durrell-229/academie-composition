"""
Générateur de bulletin PDF par overlay sur l'image bulletin.png.
Utilise ReportLab pour placer les données précisément sur l'image.
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from PIL import Image
import os
from django.conf import settings


class ImageBulletinGenerator:
    """Génère un bulletin PDF en écrivant sur l'image bulletin.png."""

    # Dimensions en millimètres (pour convertir en reportlab units)
    PAGE_WIDTH = 210 * mm  # A4 width
    PAGE_HEIGHT = 297 * mm  # A4 height

    # Positions calibrées pour bulletin.png (768x1376 pixels = ~210x297mm)
    # Conversion: pixel → mm (768px = 210mm → factor = 0.273)
    PIXEL_TO_MM = 210 / 768  # ~0.273 mm/pixel

    # Coordonnées estimées sur l'image (en pixels, converties en mm plus bas)
    POSITIONS = {
        'identity': {
            'nom': (60, 180),  # (x_px, y_px de haut)
            'prenom': (60, 200),
            'matricule': (400, 180),
            'classe': (400, 200),
            'serie': (400, 220),
            'effectif': (400, 240),
        },
        'table': {
            'start_y_px': 290,  # Y du début du tableau (depuis le haut en pixels)
            'row_height_px': 20,  # Hauteur de chaque ligne
            'columns': {
                'matiere': (40, 'left'),  # (x_px, align)
                'coefficient': (200, 'center'),
                'moy_interro': (250, 'center'),
                'moy_devoir': (310, 'center'),
                'moy_finale': (370, 'center'),
                'rang': (450, 'center'),
                'appreciation': (520, 'left'),
            }
        },
        'results': {
            'moyenne_generale': (400, 1100),  # (x, y en pixels)
            'rang': (400, 1130),
            'effectif_display': (400, 1160),
            'observation': (60, 1220),
            'decision': (60, 1280),
        }
    }

    # Nombre maximum de matières par page
    MAX_MATIERES_PER_PAGE = 12

    @staticmethod
    def _px_to_mm(px):
        """Convertit pixels en millimètres pour ReportLab."""
        return px * ImageBulletinGenerator.PIXEL_TO_MM

    @staticmethod
    def _px_to_points(px):
        """Convertit pixels en points pour ReportLab."""
        mm_val = ImageBulletinGenerator._px_to_mm(px)
        return mm_val / mm  # Convertir en points

    @staticmethod
    def generate(bulletin, data):
        """
        Génère le bulletin PDF en écrivant sur bulletin.png.

        Args:
            bulletin: Modèle Bulletin Django
            data: dict avec structure retournée par BulletinDataAggregator.aggregate_notes()

        Returns:
            bytes: PDF prêt pour FileField
        """
        # Créer un buffer PDF
        pdf_buffer = BytesIO()

        # Créer un canvas ReportLab
        c = canvas.Canvas(pdf_buffer, pagesize=A4)

        # Charger et placer l'image bulletin.png comme fond
        bulletin_path = os.path.join(settings.BASE_DIR, 'bulletin.png')
        if not os.path.exists(bulletin_path):
            raise FileNotFoundError(f"bulletin.png non trouvé à {bulletin_path}")

        # Placer l'image de fond (full A4)
        c.drawImage(
            bulletin_path,
            0, 0,
            width=ImageBulletinGenerator.PAGE_WIDTH,
            height=ImageBulletinGenerator.PAGE_HEIGHT,
            preserveAspectRatio=False
        )

        # Écrire les données
        ImageBulletinGenerator._write_identity(c, data)
        ImageBulletinGenerator._write_table_notes(c, data)
        ImageBulletinGenerator._write_results(c, data)
        ImageBulletinGenerator._write_observations(c, bulletin)

        # Sauvegarder le PDF
        c.save()
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    @staticmethod
    def _write_identity(c, data):
        """Écrit les informations d'identité."""
        eleve = data.get('eleve', {})

        # Font
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)

        # Convertir positions (pixels) en positions ReportLab
        pos_nom = ImageBulletinGenerator.POSITIONS['identity']['nom']
        y_from_top = pos_nom[1]
        y_reportlab = ImageBulletinGenerator.PAGE_HEIGHT - ImageBulletinGenerator._px_to_mm(y_from_top)

        # Nom
        nom = eleve.get('nom', '').upper()
        c.drawString(
            ImageBulletinGenerator._px_to_mm(pos_nom[0]),
            y_reportlab,
            nom[:50] if nom else ''
        )

        # Prénom
        pos_prenom = ImageBulletinGenerator.POSITIONS['identity']['prenom']
        y_reportlab_prenom = ImageBulletinGenerator.PAGE_HEIGHT - ImageBulletinGenerator._px_to_mm(pos_prenom[1])
        prenom = eleve.get('prenom', '').upper()
        c.drawString(
            ImageBulletinGenerator._px_to_mm(pos_prenom[0]),
            y_reportlab_prenom,
            prenom[:50] if prenom else ''
        )

        # Matricule
        c.setFont("Helvetica", 9)
        pos_matricule = ImageBulletinGenerator.POSITIONS['identity']['matricule']
        y_reportlab_mat = ImageBulletinGenerator.PAGE_HEIGHT - ImageBulletinGenerator._px_to_mm(pos_matricule[1])
        matricule = eleve.get('matricule', '')
        c.drawString(
            ImageBulletinGenerator._px_to_mm(pos_matricule[0]),
            y_reportlab_mat,
            matricule[:30] if matricule else 'N/A'
        )

        # Classe
        pos_classe = ImageBulletinGenerator.POSITIONS['identity']['classe']
        y_reportlab_classe = ImageBulletinGenerator.PAGE_HEIGHT - ImageBulletinGenerator._px_to_mm(pos_classe[1])
        classe = eleve.get('classe', '')
        c.drawString(
            ImageBulletinGenerator._px_to_mm(pos_classe[0]),
            y_reportlab_classe,
            classe[:30] if classe else 'N/A'
        )

    @staticmethod
    def _write_table_notes(c, data):
        """Écrit le tableau de notes (matières, coefficients, moyennes)."""
        matieres = data.get('matieres', [])
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)

        table_config = ImageBulletinGenerator.POSITIONS['table']
        start_y_px = table_config['start_y_px']
        row_height_px = table_config['row_height_px']
        cols = table_config['columns']

        # Écrire chaque matière
        for idx, matiere in enumerate(matieres[:ImageBulletinGenerator.MAX_MATIERES_PER_PAGE]):
            y_px = start_y_px + (idx * row_height_px)
            y_reportlab = ImageBulletinGenerator.PAGE_HEIGHT - ImageBulletinGenerator._px_to_mm(y_px)

            # Matière (left-aligned)
            nom_mat = matiere.get('nom', '')[:25]
            x_mat = ImageBulletinGenerator._px_to_mm(cols['matiere'][0])
            c.drawString(x_mat, y_reportlab, nom_mat)

            # Coefficient
            coeff = matiere.get('coefficient', 1)
            x_coeff = ImageBulletinGenerator._px_to_mm(cols['coefficient'][0])
            c.drawRightString(x_coeff, y_reportlab, f"{coeff:.2f}")

            # Moyenne interrogations
            moy_int = matiere.get('moy_interrogations', 0)
            x_int = ImageBulletinGenerator._px_to_mm(cols['moy_interro'][0])
            c.drawRightString(x_int, y_reportlab, f"{moy_int:.2f}" if moy_int else "—")

            # Moyenne devoirs
            moy_dev = matiere.get('moy_devoirs', 0)
            x_dev = ImageBulletinGenerator._px_to_mm(cols['moy_devoir'][0])
            c.drawRightString(x_dev, y_reportlab, f"{moy_dev:.2f}" if moy_dev else "—")

            # Moyenne finale
            moy_fin = matiere.get('moyenne_finale', 0)
            x_fin = ImageBulletinGenerator._px_to_mm(cols['moy_finale'][0])
            c.drawRightString(x_fin, y_reportlab, f"{moy_fin:.2f}" if moy_fin else "—")

            # Rang (si disponible)
            # rang = matiere.get('rang', '—')
            # x_rang = ImageBulletinGenerator._px_to_mm(cols['rang'][0])
            # c.drawRightString(x_rang, y_reportlab, str(rang))

            # Appréciation
            apprec = matiere.get('appreciation', '')[:20]
            x_apprec = ImageBulletinGenerator._px_to_mm(cols['appreciation'][0])
            c.drawString(x_apprec, y_reportlab, apprec)

    @staticmethod
    def _write_results(c, data):
        """Écrit les résultats finaux (moyenne générale, rang, etc.)."""
        results_pos = ImageBulletinGenerator.POSITIONS['results']
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor('#008751'))  # Vert Bénin

        # Moyenne générale
        moy_gen = data.get('moyenne_generale', 0)
        y_moy = ImageBulletinGenerator.PAGE_HEIGHT - ImageBulletinGenerator._px_to_mm(results_pos['moyenne_generale'][1])
        x_moy = ImageBulletinGenerator._px_to_mm(results_pos['moyenne_generale'][0])
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x_moy, y_moy, f"{moy_gen:.2f}")

        # Rang
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        rang = data.get('rang', 0)
        y_rang = ImageBulletinGenerator.PAGE_HEIGHT - ImageBulletinGenerator._px_to_mm(results_pos['rang'][1])
        x_rang = ImageBulletinGenerator._px_to_mm(results_pos['rang'][0])
        c.drawString(x_rang, y_rang, f"{rang}")

        # Effectif
        effectif = data.get('effectif', 0)
        y_eff = ImageBulletinGenerator.PAGE_HEIGHT - ImageBulletinGenerator._px_to_mm(results_pos['effectif_display'][1])
        x_eff = ImageBulletinGenerator._px_to_mm(results_pos['effectif_display'][0])
        c.drawString(x_eff, y_eff, f"{effectif}")

    @staticmethod
    def _write_observations(c, bulletin):
        """Écrit les observations et décisions du conseil."""
        results_pos = ImageBulletinGenerator.POSITIONS['results']
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)

        # Observation
        observation = bulletin.observation_conseil or "Travail satisfaisant."
        y_obs = ImageBulletinGenerator.PAGE_HEIGHT - ImageBulletinGenerator._px_to_mm(results_pos['observation'][1])
        x_obs = ImageBulletinGenerator._px_to_mm(results_pos['observation'][0])

        # Découper le texte sur plusieurs lignes si trop long
        words = observation.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > 70:  # Limite de caractères par ligne
                lines.append(' '.join(current_line[:-1]))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))

        for idx, line in enumerate(lines[:3]):  # Max 3 lignes
            y = y_obs - (idx * 4 * mm)
            c.drawString(x_obs, y, line)

        # Décision
        decision = bulletin.decision_conseil or "ADMIS"
        y_dec = ImageBulletinGenerator.PAGE_HEIGHT - ImageBulletinGenerator._px_to_mm(results_pos['decision'][1])
        x_dec = ImageBulletinGenerator._px_to_mm(results_pos['decision'][0])
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor('#E8112D'))  # Rouge Bénin
        c.drawString(x_dec, y_dec, decision.upper())


class BulletinImageValidator:
    """Valide l'image bulletin.png."""

    @staticmethod
    def validate_image():
        """Vérifie que bulletin.png existe et est valide."""
        bulletin_path = os.path.join(settings.BASE_DIR, 'bulletin.png')

        if not os.path.exists(bulletin_path):
            return False, f"bulletin.png non trouvé à {bulletin_path}"

        try:
            img = Image.open(bulletin_path)
            if img.size != (768, 1376):
                return False, f"Dimensions incorrectes: {img.size} (attendu: 768x1376)"
            if img.mode != 'RGB':
                return False, f"Mode couleur incorrect: {img.mode} (attendu: RGB)"
            return True, "Image valide"
        except Exception as e:
            return False, f"Erreur ouverture image: {str(e)}"
