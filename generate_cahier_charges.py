#!/usr/bin/env python3
"""
Génération du Cahier des Charges — Académie Numérique
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Line, Polygon
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.piecharts import Pie
from reportlab.platypus.flowables import Flowable
import math

OUTPUT = "/home/user/academie-composition/Cahier_Charges_Academie_Numerique.pdf"

# ─── COULEURS ───────────────────────────────────────────────────────────────
VERT       = colors.HexColor("#007A5E")
VERT_CLAIR = colors.HexColor("#E8F5F0")
ROUGE      = colors.HexColor("#CE1126")
JAUNE      = colors.HexColor("#FCD116")
BLEU       = colors.HexColor("#1E40AF")
BLEU_CLAIR = colors.HexColor("#EFF6FF")
GRIS_FONCE = colors.HexColor("#1F2937")
GRIS_MOYEN = colors.HexColor("#6B7280")
GRIS_CLAIR = colors.HexColor("#F3F4F6")
BLANC      = colors.white
ORANGE     = colors.HexColor("#D97706")
VIOLET     = colors.HexColor("#7C3AED")
ROSE       = colors.HexColor("#DB2777")

# ─── STYLES ─────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, **kw)

TITRE_COUVERTURE = S("TitreCouv", fontSize=32, textColor=BLANC,
    alignment=TA_CENTER, fontName="Helvetica-Bold", leading=40, spaceAfter=10)
SOUS_TITRE_COUV  = S("SousTitreCouv", fontSize=16, textColor=JAUNE,
    alignment=TA_CENTER, fontName="Helvetica-Bold", leading=22, spaceAfter=6)
INFOS_COUV = S("InfosCouv", fontSize=11, textColor=BLANC,
    alignment=TA_CENTER, fontName="Helvetica", leading=18)

H1 = S("H1", fontSize=20, textColor=BLANC, fontName="Helvetica-Bold",
    leading=26, spaceAfter=4, spaceBefore=20,
    backColor=VERT, leftIndent=-1.5*cm, rightIndent=-1.5*cm,
    borderPad=(8, 20, 8, 20))
H2 = S("H2", fontSize=14, textColor=VERT, fontName="Helvetica-Bold",
    leading=20, spaceAfter=4, spaceBefore=14,
    borderPad=(0, 0, 4, 0))
H3 = S("H3", fontSize=12, textColor=BLEU, fontName="Helvetica-Bold",
    leading=16, spaceAfter=3, spaceBefore=8)
H4 = S("H4", fontSize=11, textColor=GRIS_FONCE, fontName="Helvetica-Bold",
    leading=14, spaceAfter=2, spaceBefore=6)

CORPS = S("Corps", fontSize=10, textColor=GRIS_FONCE, fontName="Helvetica",
    leading=15, spaceAfter=4, alignment=TA_JUSTIFY)
CORPS_SMALL = S("CorpsSmall", fontSize=9, textColor=GRIS_FONCE, fontName="Helvetica",
    leading=13, spaceAfter=3)
BULLET = S("Bullet", fontSize=10, textColor=GRIS_FONCE, fontName="Helvetica",
    leading=15, spaceAfter=3, leftIndent=0.5*cm,
    bulletIndent=0.2*cm)
BULLET_SMALL = S("BulletSmall", fontSize=9, textColor=GRIS_FONCE, fontName="Helvetica",
    leading=13, spaceAfter=2, leftIndent=1*cm, bulletIndent=0.5*cm)
CODE = S("Code", fontSize=8.5, textColor=colors.HexColor("#1E1E1E"),
    fontName="Courier", leading=13, backColor=GRIS_CLAIR,
    leftIndent=0.5*cm, rightIndent=0.5*cm, borderPad=6)
LEGENDE = S("Legende", fontSize=9, textColor=GRIS_MOYEN,
    fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceAfter=8)
NOTE = S("Note", fontSize=9, textColor=BLEU, fontName="Helvetica",
    leading=13, backColor=BLEU_CLAIR, leftIndent=0.5*cm,
    borderPad=6, spaceAfter=6)
BADGE = S("Badge", fontSize=9, textColor=BLANC, fontName="Helvetica-Bold",
    alignment=TA_CENTER)
TABLE_HEADER = S("TH", fontSize=9, textColor=BLANC, fontName="Helvetica-Bold",
    alignment=TA_CENTER, leading=12)
TABLE_CELL = S("TC", fontSize=9, textColor=GRIS_FONCE, fontName="Helvetica",
    leading=12, alignment=TA_LEFT)
TABLE_CELL_C = S("TCC", fontSize=9, textColor=GRIS_FONCE, fontName="Helvetica",
    leading=12, alignment=TA_CENTER)
PHASE_TITRE = S("PhaseTitre", fontSize=13, textColor=BLANC,
    fontName="Helvetica-Bold", leading=18, alignment=TA_CENTER)
NUMERO = S("Numero", fontSize=28, textColor=VERT, fontName="Helvetica-Bold",
    alignment=TA_CENTER, leading=34)

# ─── HELPERS ────────────────────────────────────────────────────────────────
def hr(color=VERT, thickness=1.5):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6)

def sp(h=6):
    return Spacer(1, h)

def p(text, style=CORPS):
    return Paragraph(text, style)

def h1(text):
    return p(f"  {text}", H1)

def h2(text):
    items = [sp(4), p(text, H2), hr(VERT, 1)]
    return items

def h3(text):
    return p(text, H3)

def h4(text):
    return p(text, H4)

def bullet(text, level=1):
    style = BULLET if level == 1 else BULLET_SMALL
    prefix = "• " if level == 1 else "◦ "
    return p(f"{prefix}{text}", style)

def note(text):
    return p(f"ℹ️  {text}", NOTE)

def tableau(data, col_widths, header_color=VERT, row_colors=None, spans=None):
    n_cols = len(data[0])
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR',  (0, 0), (-1, 0), BLANC),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, 0), 9),
        ('ALIGN',      (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID',       (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLANC, GRIS_CLAIR]),
        ('FONTNAME',   (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',  (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, header_color),
    ]
    if spans:
        for span in spans:
            style_cmds.append(('SPAN', span[0], span[1]))
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(style_cmds))
    return t

def boite(contenu_list, couleur=VERT_CLAIR, border_color=VERT):
    """Encadré coloré"""
    data = [[c] for c in contenu_list]
    t = Table([[item] for item in contenu_list],
              colWidths=[16*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), couleur),
        ('BOX', (0, 0), (-1, -1), 1.5, border_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t

# ─── DIAGRAMME CAS D'UTILISATION ────────────────────────────────────────────
class UseCaseDiagram(Flowable):
    def __init__(self, width=500, height=420):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        w, h = self.width, self.height

        # Fond
        c.setFillColor(colors.HexColor("#F8FAFC"))
        c.setStrokeColor(colors.HexColor("#CBD5E1"))
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=1)

        # Titre
        c.setFillColor(VERT)
        c.roundRect(10, h-36, w-20, 28, 4, fill=1, stroke=0)
        c.setFillColor(BLANC)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w/2, h-24, "Diagramme de Cas d'Utilisation — Académie Numérique")

        actors = [
            ("Élève",       30,  h/2 - 30, VERT),
            ("Professeur",  30,  h/2 + 80, BLEU),
            ("Admin",       30,  h/2 + 180, ROUGE),
            ("Conseiller",  30,  h/2 - 140, ORANGE),
            ("Parent",      30,  h/2 - 240, VIOLET),
        ]

        use_cases_left = [
            ("Passer un examen",         180, h-65),
            ("Faire un QCM",             180, h-100),
            ("Consulter bulletins",      180, h-135),
            ("Télécharger certificat",   180, h-170),
            ("Suivre progression/XP",    180, h-205),
            ("Messagerie",               180, h-240),
            ("Payer abonnement",         180, h-275),
        ]
        use_cases_right = [
            ("Créer épreuve",            340, h-65),
            ("Corriger avec IA",         340, h-100),
            ("Générer bulletins PDF",    340, h-135),
            ("Gérer cours/devoirs",      340, h-170),
            ("Détecter plagiat",         340, h-205),
            ("Gérer utilisateurs",       340, h-240),
            ("Valider examens nationaux",340, h-275),
            ("Config. établissement",    340, h-310),
            ("Voir tableau de bord",     340, h-345),
        ]

        system_x, system_y = 155, 50
        system_w, system_h = 235, h-110

        # Boîte système
        c.setFillColor(colors.HexColor("#EFF6FF"))
        c.setStrokeColor(BLEU)
        c.setLineWidth(1.5)
        c.rect(system_x, system_y, system_w, system_h, fill=1, stroke=1)
        c.setFillColor(BLEU)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(system_x + system_w/2, system_y + system_h - 14, "«système» Académie Numérique")

        # Dessiner les cas d'utilisation
        def draw_uc(label, x, y, col=VERT):
            c.setFillColor(BLANC)
            c.setStrokeColor(col)
            c.setLineWidth(1)
            ew, eh = 115, 16
            c.ellipse(x - ew/2, y - eh/2, x + ew/2, y + eh/2, fill=1, stroke=1)
            c.setFillColor(GRIS_FONCE)
            c.setFont("Helvetica", 7)
            c.drawCentredString(x, y - 3, label)

        for label, x, y in use_cases_left:
            draw_uc(label, x, y, VERT)
        for label, x, y in use_cases_right:
            draw_uc(label, x, y, BLEU)

        # Dessiner les acteurs
        def draw_actor(name, x, y, col=VERT):
            head_r = 10
            c.setFillColor(col)
            c.setStrokeColor(col)
            c.setLineWidth(1)
            c.circle(x, y + 30, head_r, fill=1, stroke=1)
            c.setLineWidth(1.5)
            c.line(x, y + 20, x, y - 5)
            c.line(x - 14, y + 10, x + 14, y + 10)
            c.line(x, y - 5, x - 10, y - 20)
            c.line(x, y - 5, x + 10, y - 20)
            c.setFillColor(GRIS_FONCE)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(x, y - 28, name)

        for name, x, y, col in actors:
            draw_actor(name, x, y, col)

        # Relations élève → cas
        c.setStrokeColor(VERT)
        c.setLineWidth(0.6)
        eleve_x, eleve_y = 30, h/2 - 30 + 5
        for label, ux, uy in use_cases_left[:5]:
            c.line(eleve_x + 20, eleve_y, ux - 58, uy)

        # Relations professeur → cas
        c.setStrokeColor(BLEU)
        prof_x, prof_y = 30, h/2 + 80 + 5
        for label, ux, uy in use_cases_right[:5]:
            c.line(prof_x + 20, prof_y, ux - 58, uy)

        # Relations admin → cas
        c.setStrokeColor(ROUGE)
        admin_x, admin_y = 30, h/2 + 180 + 5
        for label, ux, uy in use_cases_right[5:]:
            c.line(admin_x + 20, admin_y, ux - 58, uy)

        # Légende
        c.setFillColor(GRIS_CLAIR)
        c.roundRect(10, 5, 120, 42, 3, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(GRIS_FONCE)
        c.drawString(15, 40, "LÉGENDE")
        legend = [(VERT, "Élève / Conseiller"), (BLEU, "Professeur"), (ROUGE, "Administrateur")]
        for i, (col, label) in enumerate(legend):
            c.setFillColor(col)
            c.circle(20, 30 - i*11, 4, fill=1, stroke=0)
            c.setFillColor(GRIS_FONCE)
            c.setFont("Helvetica", 7)
            c.drawString(28, 27 - i*11, label)


# ─── DIAGRAMME ENTITÉ-RELATION ───────────────────────────────────────────────
class ERDiagram(Flowable):
    def __init__(self, width=500, height=480):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        w, h = self.width, self.height

        c.setFillColor(colors.HexColor("#F8FAFC"))
        c.setStrokeColor(colors.HexColor("#CBD5E1"))
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=1)

        c.setFillColor(VERT)
        c.roundRect(10, h-36, w-20, 28, 4, fill=1, stroke=0)
        c.setFillColor(BLANC)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w/2, h-24, "Modélisation — Diagramme Entité-Relation Principal")

        entities = [
            ("User", 250, h-90, VERT,   ["id (UUID)", "email", "role", "xp", "matricule"]),
            ("Exam", 80,  h-170, BLEU,  ["id (UUID)", "titre", "type_exam", "statut", "date_debut"]),
            ("CompositionSession", 250, h-200, ORANGE, ["id (UUID)", "statut", "mode", "cheat_count"]),
            ("Resultat", 420, h-160, ROUGE, ["id (UUID)", "note", "mention", "corrige_par_ia"]),
            ("AICorrection", 420, h-270, VIOLET, ["id (UUID)", "model_utilise", "statut", "note_proposee"]),
            ("Bulletin", 250, h-320, VERT,   ["id (UUID)", "periode", "moyenne_generale", "file_pdf"]),
            ("QCMExam",  80,  h-290, BLEU,  ["id (UUID)", "mode_notation", "melanger_questions"]),
            ("Matiere",  80,  h-400, GRIS_MOYEN, ["id (UUID)", "nom", "code", "couleur"]),
            ("Etablissement", 420, h-380, ROUGE, ["id (UUID)", "nom", "type", "devise"]),
            ("UserSubscription", 250, h-430, ORANGE, ["id (UUID)", "plan", "end_date", "is_active"]),
        ]

        def draw_entity(name, x, y, color, attrs):
            bw, bh = 130, 14 + len(attrs) * 12
            c.setFillColor(color)
            c.setStrokeColor(color)
            c.roundRect(x - bw/2, y - bh, bw, bh + 14, 4, fill=1, stroke=0)
            c.setFillColor(BLANC)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(x, y + 2, name)
            c.setFillColor(BLANC)
            c.setStrokeColor(colors.HexColor("#FFFFFF40"))
            c.setLineWidth(0.3)
            c.line(x - bw/2 + 4, y - 4, x + bw/2 - 4, y - 4)
            c.setFont("Helvetica", 7)
            c.setFillColor(colors.HexColor("#FFFFFF"))
            for i, attr in enumerate(attrs):
                c.drawString(x - bw/2 + 6, y - 16 - i*12, f"  {attr}")
            return (x, y - bh/2)

        centers = {}
        for (name, x, y, color, attrs) in entities:
            cx, cy = draw_entity(name, x, y, color, attrs)
            centers[name] = (x, y - (14 + len(attrs)*12)/2)

        relations = [
            ("User", "CompositionSession", "1..N", "compose"),
            ("Exam", "CompositionSession", "1..N", "génère"),
            ("CompositionSession", "Resultat", "1..1", "produit"),
            ("Resultat", "AICorrection", "1..1", "corrigé par"),
            ("CompositionSession", "Bulletin", "N..1", "intégré dans"),
            ("Exam", "QCMExam", "1..1", "configure"),
            ("Exam", "Matiere", "N..1", "appartient"),
            ("User", "UserSubscription", "1..1", "souscrit"),
        ]

        c.setLineWidth(0.8)
        for (a, b, mult, label) in relations:
            if a in centers and b in centers:
                ax, ay = centers[a]
                bx, by = centers[b]
                c.setStrokeColor(GRIS_MOYEN)
                c.setDash(3, 2)
                c.line(ax, ay, bx, by)
                c.setDash()
                mx, my = (ax+bx)/2, (ay+by)/2
                c.setFillColor(GRIS_FONCE)
                c.setFont("Helvetica", 6)
                c.drawCentredString(mx, my + 4, label)
                c.setFillColor(ROUGE)
                c.setFont("Helvetica-Bold", 6)
                c.drawCentredString(mx, my - 4, mult)


# ─── DIAGRAMME ARCHITECTURE ──────────────────────────────────────────────────
class ArchDiagram(Flowable):
    def __init__(self, width=500, height=320):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        w, h = self.width, self.height

        c.setFillColor(colors.HexColor("#0F172A"))
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=0)

        layers = [
            (h-50,  48, ROSE,   "COUCHE PRÉSENTATION",
             ["Templates Django (HTML/CSS/JS)", "Django Ninja API (REST JSON)", "WebSockets (Django Channels)"]),
            (h-120, 48, BLEU,   "COUCHE MÉTIER",
             ["25 Apps Django • Auth multi-rôles", "IA Engine (Groq/Gemini/NVIDIA)", "Anti-triche • QCM • Bulletins PDF"]),
            (h-190, 48, VERT,   "COUCHE DONNÉES",
             ["PostgreSQL (prod) / SQLite (dev)", "Redis (Channels + Cache)", "Cloudinary / S3 (médias)"]),
            (h-260, 48, ORANGE, "COUCHE INTÉGRATION",
             ["FedaPay (paiements XOF)", "Resend (emails)", "Google OAuth • Laravel SSO"]),
        ]

        for y, lh, col, title, items in layers:
            c.setFillColor(col)
            c.setStrokeColor(col)
            c.setLineWidth(0)
            c.roundRect(10, y - lh + 14, w - 20, lh, 4, fill=1, stroke=0)
            c.setFillColor(BLANC)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(20, y - 4, title)
            c.setFont("Helvetica", 7.5)
            for i, item in enumerate(items):
                c.drawString(20 + (w-40)//3 * i, y - 18, f"▸ {item}")

        # Flèches entre couches
        c.setStrokeColor(colors.HexColor("#FFFFFF40"))
        c.setLineWidth(1)
        for y_pos in [h-72, h-142, h-212]:
            c.setDash(2, 2)
            c.line(w/2 - 30, y_pos, w/2 - 30, y_pos - 10)
            c.line(w/2 + 30, y_pos, w/2 + 30, y_pos - 10)
        c.setDash()

        c.setFillColor(BLANC)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(w/2, h - 14, "Architecture 4 Couches — Académie Numérique")

        c.setFillColor(colors.HexColor("#FFFFFF60"))
        c.setFont("Helvetica", 7)
        c.drawCentredString(w/2, 8, "Déployé sur Render • WSGI (Gunicorn) + ASGI (Daphne) • Python 3 • Django 5.2")


# ─── DOCUMENT ────────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.8*cm, bottomMargin=1.8*cm,
        title="Cahier des Charges — Académie Numérique",
        author="Académie Numérique",
    )

    story = []
    W = 16 * cm  # largeur utile

    # ═══════════════════════════════════════════════════════════════════════
    # PAGE DE COUVERTURE
    # ═══════════════════════════════════════════════════════════════════════
    cover_data = [[
        Paragraph("ACADÉMIE NUMÉRIQUE", TITRE_COUVERTURE),
        Spacer(1, 8),
        Paragraph("Cahier des Charges Technique & Fonctionnel", SOUS_TITRE_COUV),
        Spacer(1, 16),
        Paragraph("Plateforme d'Éducation Numérique — Bénin, Afrique de l'Ouest", INFOS_COUV),
        Spacer(1, 8),
        Paragraph("Version 1.0 — Mai 2026", INFOS_COUV),
        Spacer(1, 20),
        Paragraph("Django 5.2 · Python 3 · PostgreSQL · Redis · Django Channels · FedaPay", INFOS_COUV),
    ]]
    cover_table = Table(cover_data, colWidths=[W + 3*cm])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), VERT),
        ('BOX',          (0, 0), (-1, -1), 3, JAUNE),
        ('TOPPADDING',   (0, 0), (-1, -1), 40),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 40),
        ('LEFTPADDING',  (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('ROUNDEDCORNERS', (0, 0), (-1, -1), [8, 8, 8, 8]),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 1*cm))

    # Badges résumé
    badges = [
        ("25 Apps", VERT),   ("Django 5.2", BLEU),  ("IA Multi-Provider", VIOLET),
        ("FedaPay XOF", ORANGE), ("WebSockets", ROUGE), ("Multi-Établissements", GRIS_FONCE),
    ]
    badge_style = ParagraphStyle("badge_s", fontSize=8, textColor=BLANC,
        fontName="Helvetica-Bold", alignment=TA_CENTER)
    badge_data = [[Paragraph(b, badge_style) for b, _ in badges]]
    bt = Table(badge_data, colWidths=[W/6]*6)
    bg_cmds = [('BACKGROUND', (idx, 0), (idx, 0), col) for idx, (_, col) in enumerate(badges)]
    bt.setStyle(TableStyle(bg_cmds + [
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(bt)
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # TABLE DES MATIÈRES
    # ═══════════════════════════════════════════════════════════════════════
    story.append(h1("TABLE DES MATIÈRES"))
    story.append(sp(10))

    toc_items = [
        ("1.", "Présentation du Projet", "3"),
        ("2.", "Objectifs & Périmètre", "3"),
        ("3.", "Acteurs & Rôles", "4"),
        ("4.", "Diagramme de Cas d'Utilisation", "5"),
        ("5.", "Architecture Technique", "6"),
        ("6.", "Stack Technologique Complet", "7"),
        ("7.", "Modélisation des Données", "9"),
        ("8.", "Fonctionnalités Détaillées", "11"),
        ("9.", "Plan d'Action — 8 Phases", "14"),
        ("10.", "Sécurité & Performance", "17"),
        ("11.", "Déploiement & Infrastructure", "18"),
        ("12.", "Critères de Qualité", "19"),
    ]
    for num, title, page in toc_items:
        toc_row = Table(
            [[Paragraph(f"<b>{num}</b> {title}", CORPS),
              Paragraph(f"<b>{page}</b>", ParagraphStyle("p", fontSize=10, alignment=TA_RIGHT))]],
            colWidths=[W * 0.85, W * 0.15]
        )
        toc_row.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(toc_row)
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # 1. PRÉSENTATION
    # ═══════════════════════════════════════════════════════════════════════
    story.append(h1("1. PRÉSENTATION DU PROJET"))
    story.append(sp(8))
    story += h2("1.1 Contexte")
    story.append(p("""L'Académie Numérique est une plateforme éducative complète conçue spécifiquement pour
    le contexte béninois et africain. Elle répond au besoin de modernisation du système éducatif
    en offrant une solution tout-en-un : gestion des examens, correction par intelligence artificielle,
    bulletins numériques officiels, paiements via Mobile Money et communication en temps réel."""))

    infos_data = [
        [p("<b>Champ</b>", TABLE_HEADER), p("<b>Valeur</b>", TABLE_HEADER)],
        [p("Nom du projet", CORPS_SMALL), p("Académie Numérique", CORPS_SMALL)],
        [p("Domaine", CORPS_SMALL), p("EdTech — Éducation Numérique", CORPS_SMALL)],
        [p("Zone géographique", CORPS_SMALL), p("Bénin (Afrique de l'Ouest) — exportable Africa", CORPS_SMALL)],
        [p("Langue principale", CORPS_SMALL), p("Français (+ Anglais, Espagnol, Arabe)", CORPS_SMALL)],
        [p("Monnaie", CORPS_SMALL), p("Franc CFA — XOF (+ extension multi-devise possible)", CORPS_SMALL)],
        [p("Framework", CORPS_SMALL), p("Django 5.2 (Python 3)", CORPS_SMALL)],
        [p("Déploiement", CORPS_SMALL), p("Render.com (cloud, auto-scaling)", CORPS_SMALL)],
        [p("URL production", CORPS_SMALL), p("academie-composition.onrender.com", CORPS_SMALL)],
        [p("Modèle économique", CORPS_SMALL), p("SaaS — Abonnements FREE / PRO / ELITE + Frais scolaires", CORPS_SMALL)],
    ]
    story.append(tableau(infos_data, [6*cm, 10*cm]))
    story.append(sp(8))

    story += h2("1.2 Vision")
    story.append(p("""Devenir la plateforme de référence pour la gestion scolaire numérique en Afrique francophone,
    en combinant intelligence artificielle, temps réel et paiements mobiles adaptés au contexte local."""))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # 2. OBJECTIFS
    # ═══════════════════════════════════════════════════════════════════════
    story.append(h1("2. OBJECTIFS & PÉRIMÈTRE"))
    story.append(sp(8))
    story += h2("2.1 Objectifs Fonctionnels")

    obj_data = [
        [p("<b>#</b>", TABLE_HEADER), p("<b>Objectif</b>", TABLE_HEADER), p("<b>Priorité</b>", TABLE_HEADER), p("<b>Statut</b>", TABLE_HEADER)],
        [p("OF-01", CORPS_SMALL), p("Gestion complète des examens (création, planification, attribution)", CORPS_SMALL), p("🔴 Critique", CORPS_SMALL), p("✅ Implémenté", CORPS_SMALL)],
        [p("OF-02", CORPS_SMALL), p("Compositions en ligne avec surveillance anti-triche", CORPS_SMALL), p("🔴 Critique", CORPS_SMALL), p("✅ Implémenté", CORPS_SMALL)],
        [p("OF-03", CORPS_SMALL), p("Correction automatique par IA multi-provider (Groq/Gemini/NVIDIA)", CORPS_SMALL), p("🔴 Critique", CORPS_SMALL), p("✅ Implémenté", CORPS_SMALL)],
        [p("OF-04", CORPS_SMALL), p("Génération de bulletins PDF officiels (format Ministère Bénin)", CORPS_SMALL), p("🔴 Critique", CORPS_SMALL), p("✅ Implémenté", CORPS_SMALL)],
        [p("OF-05", CORPS_SMALL), p("QCM interactif avec banque de questions et notation avancée", CORPS_SMALL), p("🟠 Haute", CORPS_SMALL), p("✅ Implémenté", CORPS_SMALL)],
        [p("OF-06", CORPS_SMALL), p("Examens nationaux (BEPC, CEP, Baccalauréat toutes séries)", CORPS_SMALL), p("🔴 Critique", CORPS_SMALL), p("✅ Implémenté", CORPS_SMALL)],
        [p("OF-07", CORPS_SMALL), p("Paiements Mobile Money via FedaPay (MTN, Orange, Wave)", CORPS_SMALL), p("🟠 Haute", CORPS_SMALL), p("✅ Implémenté", CORPS_SMALL)],
        [p("OF-08", CORPS_SMALL), p("Gamification : XP, badges, leaderboard, streaks", CORPS_SMALL), p("🟡 Normale", CORPS_SMALL), p("✅ Implémenté", CORPS_SMALL)],
        [p("OF-09", CORPS_SMALL), p("Notifications temps réel (WebSockets, Django Channels)", CORPS_SMALL), p("🟠 Haute", CORPS_SMALL), p("✅ Implémenté", CORPS_SMALL)],
        [p("OF-10", CORPS_SMALL), p("Certifications numériques vérifiables (token QR)", CORPS_SMALL), p("🟡 Normale", CORPS_SMALL), p("✅ Implémenté", CORPS_SMALL)],
        [p("OF-11", CORPS_SMALL), p("Détection de plagiat entre copies", CORPS_SMALL), p("🟡 Normale", CORPS_SMALL), p("🔄 En cours", CORPS_SMALL)],
        [p("OF-12", CORPS_SMALL), p("Gestion multi-établissements (campus, classes, niveaux)", CORPS_SMALL), p("🟠 Haute", CORPS_SMALL), p("✅ Implémenté", CORPS_SMALL)],
    ]
    story.append(tableau(obj_data, [1.5*cm, 7.5*cm, 2.5*cm, 2.5*cm]))
    story.append(sp(8))

    story += h2("2.2 Objectifs Non-Fonctionnels")
    onf = [
        ("Performance", "Réponse < 200ms pour 95% des requêtes, support 500+ utilisateurs simultanés"),
        ("Sécurité", "HTTPS obligatoire, CSRF, XSS protection, audit trail complet"),
        ("Disponibilité", "99.9% uptime (SLA Render), déploiement sans interruption"),
        ("Accessibilité", "Responsive mobile-first, compatible réseau lent (Afrique)"),
        ("Maintenabilité", "Code Django standard, tests unitaires, documentation inline"),
        ("Internationalisation", "Français/Anglais/Arabe/Espagnol via Django i18n"),
    ]
    for cat, desc in onf:
        story.append(bullet(f"<b>{cat}</b> : {desc}"))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # 3. ACTEURS & RÔLES
    # ═══════════════════════════════════════════════════════════════════════
    story.append(h1("3. ACTEURS & RÔLES"))
    story.append(sp(8))

    roles_data = [
        [p("<b>Rôle</b>", TABLE_HEADER), p("<b>Description</b>", TABLE_HEADER), p("<b>Permissions Clés</b>", TABLE_HEADER), p("<b>Accès</b>", TABLE_HEADER)],
        [p("👨‍💼 Admin", CORPS_SMALL), p("Super-administrateur de la plateforme", CORPS_SMALL),
         p("• Gérer tous les utilisateurs\n• Valider examens nationaux\n• Config. établissements\n• Rapports financiers", CORPS_SMALL),
         p("is_staff + is_superuser", CORPS_SMALL)],
        [p("🎓 Conseiller\nPédagogique", CORPS_SMALL), p("Coordinateur académique, superviseur des enseignants", CORPS_SMALL),
         p("• Approuver les épreuves\n• Voir tous les résultats\n• Gérer les classes\n• Tableau de bord complet", CORPS_SMALL),
         p("Role: conseiller", CORPS_SMALL)],
        [p("👨‍🏫 Professeur", CORPS_SMALL), p("Enseignant créateur d'épreuves et correcteur", CORPS_SMALL),
         p("• Créer examens/devoirs\n• Uploader corrigés types\n• Valider corrections IA\n• Générer QCM", CORPS_SMALL),
         p("Role: professeur", CORPS_SMALL)],
        [p("👨‍🎓 Élève", CORPS_SMALL), p("Apprenant, utilisateur final principal", CORPS_SMALL),
         p("• Passer examens/QCM\n• Voir bulletins\n• Télécharger certificats\n• Suivre XP et badges", CORPS_SMALL),
         p("Role: eleve", CORPS_SMALL)],
        [p("👨‍👩‍👧 Parent", CORPS_SMALL), p("Tuteur légal, accès lecture seule sur l'élève", CORPS_SMALL),
         p("• Voir bulletins enfant\n• Voir résultats\n• Payer frais scolaires\n• Recevoir notifications", CORPS_SMALL),
         p("App: parents", CORPS_SMALL)],
    ]
    story.append(tableau(roles_data, [2.8*cm, 3.5*cm, 5.5*cm, 3.2*cm]))
    story.append(sp(6))
    story.append(note("Le modèle User utilise UUID comme clé primaire et génère automatiquement un matricule au format ROL-YYYY-00001 à la création."))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # 4. DIAGRAMME DE CAS D'UTILISATION
    # ═══════════════════════════════════════════════════════════════════════
    story.append(h1("4. DIAGRAMME DE CAS D'UTILISATION"))
    story.append(sp(10))
    d = UseCaseDiagram(width=500, height=430)
    story.append(d)
    story.append(p("Figure 1 — Diagramme de cas d'utilisation simplifié de l'Académie Numérique", LEGENDE))
    story.append(sp(10))

    story += h2("4.1 Cas d'Utilisation Étendus — Élève")
    uc_eleve = [
        ("UC-E01", "Passer un examen en ligne", "Épreuve en mode plein écran, caméra activée, anti-triche temps réel"),
        ("UC-E02", "Soumettre copie papier", "Upload photo de la copie → OCR → Correction IA"),
        ("UC-E03", "Participer à un QCM", "Questions mélangées, timer, résultat immédiat ou différé"),
        ("UC-E04", "Consulter son bulletin", "Accès bulletin PDF officiel avec signature numérique"),
        ("UC-E05", "Télécharger certificat", "Certificat PDF avec QR code de vérification unique"),
        ("UC-E06", "Voir progression XP", "Dashboard gamifié : niveau, badges, classement mondial/national"),
    ]
    uc_data = [[p("<b>ID</b>", TABLE_HEADER), p("<b>Cas d'Utilisation</b>", TABLE_HEADER), p("<b>Description</b>", TABLE_HEADER)]]
    for uc_id, uc_name, uc_desc in uc_eleve:
        uc_data.append([p(uc_id, CORPS_SMALL), p(f"<b>{uc_name}</b>", CORPS_SMALL), p(uc_desc, CORPS_SMALL)])
    story.append(tableau(uc_data, [1.8*cm, 4.5*cm, 9.7*cm]))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # 5. ARCHITECTURE
    # ═══════════════════════════════════════════════════════════════════════
    story.append(h1("5. ARCHITECTURE TECHNIQUE"))
    story.append(sp(10))
    arch = ArchDiagram(width=500, height=300)
    story.append(arch)
    story.append(p("Figure 2 — Architecture 4 couches de l'Académie Numérique", LEGENDE))
    story.append(sp(10))

    story += h2("5.1 Structure des Apps Django (25 applications)")
    apps_data = [
        [p("<b>App</b>", TABLE_HEADER), p("<b>Responsabilité</b>", TABLE_HEADER), p("<b>Modèles Principaux</b>", TABLE_HEADER)],
        [p("core", CORPS_SMALL), p("Modèles et utilitaires partagés", CORPS_SMALL), p("Matiere, Classe, Feedback, CalendarEvent", CORPS_SMALL)],
        [p("accounts", CORPS_SMALL), p("Authentification & profils utilisateurs", CORPS_SMALL), p("User, Profile, Referral, Leaderboard", CORPS_SMALL)],
        [p("schools", CORPS_SMALL), p("Gestion multi-établissements", CORPS_SMALL), p("Etablissement, Campus, NiveauScolaire, Classe", CORPS_SMALL)],
        [p("exams", CORPS_SMALL), p("Épreuves et examens nationaux", CORPS_SMALL), p("Exam, ExamFile, ExamenNational, ExamenComposition", CORPS_SMALL)],
        [p("compositions", CORPS_SMALL), p("Sessions de composition en ligne/papier", CORPS_SMALL), p("CompositionSession, StudentAnswer, Resultat, AntiCheatLog", CORPS_SMALL)],
        [p("correction", CORPS_SMALL), p("Correction de copies uploadées", CORPS_SMALL), p("CorrectionCopie", CORPS_SMALL)],
        [p("ai_engine", CORPS_SMALL), p("Moteur IA multi-provider (Groq/Gemini/NVIDIA)", CORPS_SMALL), p("AICorrection, CorrectionDetail", CORPS_SMALL)],
        [p("bulletins", CORPS_SMALL), p("Génération bulletins officiels PDF", CORPS_SMALL), p("Bulletin, BulletinLigne", CORPS_SMALL)],
        [p("qcm", CORPS_SMALL), p("QCM interactif avec banque de questions", CORPS_SMALL), p("QuestionBank, QCMExam, QCMAnswer, QCMResultat", CORPS_SMALL)],
        [p("payments", CORPS_SMALL), p("Paiements scolaires et abonnements FedaPay", CORPS_SMALL), p("FraisScolaire, Paiement, AbonnementEleve, PaiementAbonnement", CORPS_SMALL)],
        [p("gamification", CORPS_SMALL), p("XP, badges, classement, streaks", CORPS_SMALL), p("Badge, UserBadge, GlobalLeaderboard, XPAction, StreakRecord", CORPS_SMALL)],
        [p("notifications", CORPS_SMALL), p("Notifications in-app et emails", CORPS_SMALL), p("Notification, EmailQueue, GlobalAnnouncement", CORPS_SMALL)],
        [p("certifications", CORPS_SMALL), p("Certificats numériques vérifiables", CORPS_SMALL), p("Certificate (QR + token)", CORPS_SMALL)],
        [p("plagiat", CORPS_SMALL), p("Détection de plagiat entre copies", CORPS_SMALL), p("PlagiatReport", CORPS_SMALL)],
        [p("realtime", CORPS_SMALL), p("WebSockets temps réel", CORPS_SMALL), p("Consumers Django Channels", CORPS_SMALL)],
        [p("audittrail", CORPS_SMALL), p("Journal d'audit complet", CORPS_SMALL), p("AuditLog", CORPS_SMALL)],
        [p("subscriptions", CORPS_SMALL), p("Plans d'abonnement plateforme", CORPS_SMALL), p("SubscriptionPlan, UserSubscription", CORPS_SMALL)],
        [p("cours / devoirs", CORPS_SMALL), p("Ressources pédagogiques", CORPS_SMALL), p("Cours, Devoir, Ressource", CORPS_SMALL)],
        [p("parents", CORPS_SMALL), p("Portail parents/tuteurs", CORPS_SMALL), p("Accès lecture bulletins élève", CORPS_SMALL)],
        [p("attendance / cahier", CORPS_SMALL), p("Présences et cahier de textes", CORPS_SMALL), p("Presence, CahierTexte", CORPS_SMALL)],
        [p("messaging", CORPS_SMALL), p("Messagerie interne", CORPS_SMALL), p("Message, Conversation", CORPS_SMALL)],
        [p("library", CORPS_SMALL), p("Bibliothèque numérique", CORPS_SMALL), p("Document, Resource", CORPS_SMALL)],
        [p("analytics", CORPS_SMALL), p("Tableaux de bord & statistiques", CORPS_SMALL), p("StatSnapshot, Report", CORPS_SMALL)],
        [p("webhooks", CORPS_SMALL), p("Réception webhooks externes (FedaPay)", CORPS_SMALL), p("WebhookEvent", CORPS_SMALL)],
    ]
    story.append(tableau(apps_data, [2.8*cm, 5.5*cm, 7.7*cm]))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # 6. STACK TECHNOLOGIQUE
    # ═══════════════════════════════════════════════════════════════════════
    story.append(h1("6. STACK TECHNOLOGIQUE COMPLET"))
    story.append(sp(8))

    story += h2("6.1 Backend")
    stack_back = [
        [p("<b>Technologie</b>", TABLE_HEADER), p("<b>Version</b>", TABLE_HEADER), p("<b>Rôle</b>", TABLE_HEADER)],
        [p("Django", CORPS_SMALL), p("5.2.13", CORPS_SMALL), p("Framework web principal — ORM, templates, admin", CORPS_SMALL)],
        [p("Python", CORPS_SMALL), p("3.11+", CORPS_SMALL), p("Langage de programmation", CORPS_SMALL)],
        [p("Django Ninja", CORPS_SMALL), p("1.6.2", CORPS_SMALL), p("API REST moderne typée (OpenAPI auto-généré)", CORPS_SMALL)],
        [p("Django Channels", CORPS_SMALL), p("4.0.0", CORPS_SMALL), p("WebSockets et communications temps réel", CORPS_SMALL)],
        [p("Daphne", CORPS_SMALL), p("4.0.0", CORPS_SMALL), p("Serveur ASGI pour WebSockets", CORPS_SMALL)],
        [p("Gunicorn", CORPS_SMALL), p("25.3.0", CORPS_SMALL), p("Serveur WSGI pour requêtes HTTP classiques", CORPS_SMALL)],
        [p("Celery / Redis", CORPS_SMALL), p("redis 5.0.1", CORPS_SMALL), p("Queue tâches asynchrones (sans Celery — natif Redis)", CORPS_SMALL)],
        [p("WhiteNoise", CORPS_SMALL), p("6.12.0", CORPS_SMALL), p("Service fichiers statiques en production", CORPS_SMALL)],
    ]
    story.append(tableau(stack_back, [4*cm, 2.5*cm, 9.5*cm]))
    story.append(sp(8))

    story += h2("6.2 Intelligence Artificielle")
    stack_ia = [
        [p("<b>Provider</b>", TABLE_HEADER), p("<b>Modèle</b>", TABLE_HEADER), p("<b>Usage</b>", TABLE_HEADER), p("<b>Priorité</b>", TABLE_HEADER)],
        [p("Groq", CORPS_SMALL), p("LLaMA 3 / Mixtral", CORPS_SMALL), p("Correction IA rapide, génération QCM", CORPS_SMALL), p("1 (primary)", CORPS_SMALL)],
        [p("Google Gemini", CORPS_SMALL), p("gemini-pro", CORPS_SMALL), p("Fallback correction, analyse pédagogique", CORPS_SMALL), p("2 (fallback)", CORPS_SMALL)],
        [p("Mistral AI", CORPS_SMALL), p("mistral-large", CORPS_SMALL), p("Correction multilingue", CORPS_SMALL), p("3 (fallback)", CORPS_SMALL)],
        [p("DeepSeek", CORPS_SMALL), p("deepseek-chat", CORPS_SMALL), p("Analyse mathématiques et sciences", CORPS_SMALL), p("4 (fallback)", CORPS_SMALL)],
        [p("NVIDIA NeMo", CORPS_SMALL), p("nemotron-4-340b", CORPS_SMALL), p("OCR avancé + correction haute précision", CORPS_SMALL), p("5 (premium)", CORPS_SMALL)],
        [p("Tesseract OCR", CORPS_SMALL), p("0.3.13", CORPS_SMALL), p("Reconnaissance texte copies papier (local)", CORPS_SMALL), p("Démo/local", CORPS_SMALL)],
        [p("PyMuPDF", CORPS_SMALL), p("1.27.2", CORPS_SMALL), p("Extraction texte PDF", CORPS_SMALL), p("Utilitaire", CORPS_SMALL)],
    ]
    story.append(tableau(stack_ia, [3*cm, 3*cm, 6*cm, 2.5*cm], header_color=VIOLET))
    story.append(sp(8))

    story += h2("6.3 Base de Données & Stockage")
    stack_db = [
        [p("<b>Composant</b>", TABLE_HEADER), p("<b>Usage</b>", TABLE_HEADER), p("<b>Config</b>", TABLE_HEADER)],
        [p("SQLite", CORPS_SMALL), p("Base de données développement local", CORPS_SMALL), p("DB_ENGINE=sqlite3", CORPS_SMALL)],
        [p("PostgreSQL", CORPS_SMALL), p("Base de données production (Render)", CORPS_SMALL), p("dj_database_url + DATABASE_URL", CORPS_SMALL)],
        [p("MySQL", CORPS_SMALL), p("Option hébergement alternatif", CORPS_SMALL), p("DB_ENGINE=mysql, utf8mb4", CORPS_SMALL)],
        [p("Redis", CORPS_SMALL), p("Channels layer + Cache + Queue", CORPS_SMALL), p("REDIS_URL, channels-redis", CORPS_SMALL)],
        [p("Cloudinary", CORPS_SMALL), p("Stockage médias cloud (images, PDF)", CORPS_SMALL), p("USE_CLOUDINARY_STORAGE=true", CORPS_SMALL)],
        [p("AWS S3", CORPS_SMALL), p("Alternative stockage cloud (DigitalOcean Spaces)", CORPS_SMALL), p("USE_S3_STORAGE=true", CORPS_SMALL)],
        [p("Local FileSystem", CORPS_SMALL), p("Médias en développement", CORPS_SMALL), p("MEDIA_ROOT", CORPS_SMALL)],
    ]
    story.append(tableau(stack_db, [3.5*cm, 7*cm, 5.5*cm], header_color=BLEU))
    story.append(sp(8))

    story += h2("6.4 Paiements & Intégrations Externes")
    stack_pay = [
        [p("<b>Service</b>", TABLE_HEADER), p("<b>Usage</b>", TABLE_HEADER), p("<b>Détails</b>", TABLE_HEADER)],
        [p("FedaPay", CORPS_SMALL), p("Paiements Mobile Money (Bénin)", CORPS_SMALL), p("MTN MoMo, Orange Money, Wave — XOF — Sandbox + Production", CORPS_SMALL)],
        [p("Resend", CORPS_SMALL), p("Envoi emails transactionnels", CORPS_SMALL), p("3000 emails/jour gratuit — SMTP api.resend.com", CORPS_SMALL)],
        [p("Google OAuth", CORPS_SMALL), p("Connexion Google (SSO)", CORPS_SMALL), p("GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET", CORPS_SMALL)],
        [p("Laravel SSO", CORPS_SMALL), p("Authentification inter-plateforme", CORPS_SMALL), p("LaravelAuthBackend custom — laravel_id/token sur User", CORPS_SMALL)],
        [p("Cloudinary API", CORPS_SMALL), p("Upload/transformation images", CORPS_SMALL), p("cloudinary://KEY:SECRET@CLOUD_NAME", CORPS_SMALL)],
    ]
    story.append(tableau(stack_pay, [3*cm, 4*cm, 9*cm], header_color=ORANGE))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # 7. MODÉLISATION
    # ═══════════════════════════════════════════════════════════════════════
    story.append(h1("7. MODÉLISATION DES DONNÉES"))
    story.append(sp(10))
    er = ERDiagram(width=500, height=480)
    story.append(er)
    story.append(p("Figure 3 — Diagramme Entité-Relation principal (modèles clés)", LEGENDE))
    story.append(sp(10))

    story += h2("7.1 Description des Entités Principales")

    entites = [
        ("User (accounts)", VERT, [
            "id: UUID (PK)", "email: EmailField (unique)", "role: choices(admin|conseiller|professeur|eleve)",
            "niveau: choices(primaire|secondaire|universitaire|...)", "xp: PositiveIntegerField",
            "matricule: CharField (auto-généré ROL-YYYY-NNNNN)", "laravel_id: FK SSO Laravel",
            "dark_mode: BooleanField", "preferred_language: CharField",
        ]),
        ("Exam (exams)", BLEU, [
            "id: UUID (PK)", "titre: CharField(300)", "type_exam: choices(composition|examen|devoir|concours)",
            "matiere: FK → core.Matiere", "classe: FK → core.Classe", "createur: FK → User",
            "date_debut/fin: DateTimeField", "statut: choices(brouillon|publie|en_cours|termine)",
            "anti_cheat_active: BooleanField", "approval_status: choices(pending|approved|rejected)",
        ]),
        ("CompositionSession (compositions)", ORANGE, [
            "id: UUID (PK)", "exam: FK → Exam", "eleve: FK → User",
            "mode: choices(en_ligne|sur_papier)", "statut: choices(en_attente|en_cours|soumis|corrige|exclu)",
            "cheat_count: PositiveIntegerField", "cheat_logs: JSONField",
            "qr_code: ImageField", "ip_address, user_agent: tracking",
        ]),
        ("Resultat (compositions)", ROUGE, [
            "id: UUID (PK)", "session: OneToOne → CompositionSession",
            "note: DecimalField(5,2)", "note_sur: DecimalField (défaut 20.00)",
            "mention: choices(excellent|tres_bien|bien|...)", "details_correction: JSONField",
            "corrige_par_ia: BooleanField", "corrige_par_humain: BooleanField",
            "bulletin_pdf: FileField",
        ]),
        ("ExamenNational (exams)", VIOLET, [
            "id: UUID (PK)", "type_examen: choices(bepc|cep|bac_a1|bac_a2|bac_b|bac_c|bac_d|...)",
            "annee_scolaire: CharField", "coefficients_par_matiere: JSONField",
            "classes: M2M → core.Classe", "matieres: M2M → core.Matiere",
            "statut: choices(brouillon|programme_publie|en_cours|termine)",
        ]),
    ]
    for (nom, col, champs) in entites:
        story += h2(f"7.1.x {nom}")
        ent_data = [[p("<b>Champ</b>", TABLE_HEADER), p("<b>Type / Contrainte</b>", TABLE_HEADER)]]
        for champ in champs:
            parts = champ.split(": ", 1)
            ent_data.append([p(parts[0], CORPS_SMALL), p(parts[1] if len(parts) > 1 else "", CORPS_SMALL)])
        story.append(tableau(ent_data, [5*cm, 11*cm], header_color=col))
        story.append(sp(6))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # 8. FONCTIONNALITÉS DÉTAILLÉES
    # ═══════════════════════════════════════════════════════════════════════
    story.append(h1("8. FONCTIONNALITÉS DÉTAILLÉES"))
    story.append(sp(8))

    story += h2("8.1 Module Examens & Compositions")
    fonc_exams = [
        ("Création d'épreuve", "Professeur", [
            "Formulaire de création avec titre, matière, classe, durée, dates",
            "Upload fichier épreuve (PDF) et corrigé type",
            "Activation optionnelle anti-triche (caméra, plein écran obligatoire)",
            "Mode de composition : en ligne ou sur papier",
            "Workflow d'approbation (pending → approved par conseiller/admin)",
        ]),
        ("Composition en ligne", "Élève", [
            "Interface plein écran obligatoire avec détection sortie",
            "Caméra surveillance (détection multi-visages)",
            "Suivi changements d'onglets (cheat_count)",
            "Timer countdown avec alerte 15min / 5min",
            "Sauvegarde automatique réponses (auto-save toutes les 30s)",
            "Soumission finale avec QR code de confirmation",
        ]),
        ("Correction IA", "Système", [
            "OCR de la copie papier (Tesseract/NVIDIA NeMo)",
            "Extraction texte corrigé type (PDF → text via PyMuPDF)",
            "Prompt IA structuré avec barème et critères",
            "Fallback automatique : Groq → Gemini → Mistral → DeepSeek → NVIDIA",
            "Note proposée + détail par question + points forts/erreurs",
            "Validation humaine obligatoire avant publication",
        ]),
    ]
    for (titre_fonc, acteur, items) in fonc_exams:
        story.append(h3(f"{titre_fonc} — Acteur : {acteur}"))
        for item in items:
            story.append(bullet(item))
        story.append(sp(4))

    story += h2("8.2 Module Bulletins")
    story.append(p("""Le système génère automatiquement des bulletins PDF au format officiel du Ministère de
    l'Éducation du Bénin. Un signal Django <b>post_save</b> sur le modèle Resultat déclenche la génération."""))
    bull_items = [
        "Périodes : T1, T2, T3, S1, S2, Annuel, QCM",
        "Types : Administratif (Ministère), Professionnel, QCM",
        "Données incluses : notes par matière, coefficient, moyenne, rang, effectif, comportement, absences",
        "Appréciation pédagogique générée par IA (synthèse contextualisée)",
        "Signature numérique + token de vérification unique",
        "Export PDF avec WeasyPrint / ReportLab",
        "Envoi email automatique aux parents via Resend",
    ]
    for item in bull_items:
        story.append(bullet(item))
    story.append(sp(8))

    story += h2("8.3 Module QCM")
    qcm_items = [
        "Banque de questions réutilisable par matière et difficulté (facile/moyen/difficile)",
        "Génération automatique de QCM par IA à partir d'un cours uploadé",
        "Modes de notation : classique, avec pénalité, partielle",
        "Mélange questions et choix (anti-triche)",
        "Résultat immédiat ou différé configurable",
        "Feedback IA détaillé par question avec explications",
        "Intégration au bulletin (QCMResultat → BulletinLigne)",
        "Contexte béninois : QCM spécifiques programmes Bénin/BEPC/BAC",
    ]
    for item in qcm_items:
        story.append(bullet(item))
    story.append(sp(8))

    story += h2("8.4 Module Paiements (FedaPay)")
    pay_items = [
        "Frais scolaires : inscription, scolarité, examen, uniforme, transport, cantine...",
        "Paiement en espèces, Mobile Money (MTN/Orange/Wave), virement, carte",
        "Abonnements plateforme : Basique / Standard / Premium / Élite",
        "Échéanciers de paiement avec rappels automatiques (3j, 1j avant)",
        "Bourses scolaires (excellence, mérite, sociale, sportive)",
        "Rapports financiers PDF (mensuel, trimestriel, annuel)",
        "Codes promo avec réduction % ou montant fixe",
        "Configuration FedaPay par établissement (sandbox ↔ production)",
    ]
    for item in pay_items:
        story.append(bullet(item))
    story.append(PageBreak())

    story += h2("8.5 Module Gamification")
    gami_items = [
        "Système XP : points gagnés à chaque action (examen, QCM, connexion...)",
        "Badges par catégorie : académique, participation, excellence, progression, social, spécial",
        "Rareté des badges : commun, rare, épique, légendaire",
        "Classement mondial et national avec périodes jour/semaine/mois/année/all-time",
        "Streaks : série de jours consécutifs d'activité",
        "Niveau calculé à partir des XP accumulés",
        "Système de parrainage (Referral) avec bonus XP",
    ]
    for item in gami_items:
        story.append(bullet(item))
    story.append(sp(8))

    story += h2("8.6 Module Temps Réel (WebSockets)")
    rt_items = [
        "Django Channels 4.0 + Redis Layer pour les connexions WebSocket",
        "Notifications push instantanées (nouvelle note, bulletin disponible, message)",
        "Tableau de bord temps réel des résultats d'examens",
        "Chat/messagerie en temps réel entre professeur et élèves",
        "Mise à jour live du leaderboard durant les examens",
        "Surveillance anti-triche en temps réel (alertes immédiates)",
    ]
    for item in rt_items:
        story.append(bullet(item))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # 9. PLAN D'ACTION — 8 PHASES
    # ═══════════════════════════════════════════════════════════════════════
    story.append(h1("9. PLAN D'ACTION — 8 PHASES"))
    story.append(sp(8))
    story.append(p("""Ce plan est séquentiel. Chaque phase doit être validée (tests + démo) avant de passer à la suivante.
    Les phases 1-3 constituent le MVP (Minimum Viable Product)."""))
    story.append(sp(8))

    phases = [
        (1, "FONDATIONS", "2 semaines", VERT, [
            ("Environnement", [
                "Créer le virtualenv Python et installer Django 5.2",
                "Configurer le projet Django : academie_numerique/settings.py",
                "Configurer .env avec toutes les variables (SECRET_KEY, DB, etc.)",
                "Configurer la base de données PostgreSQL (prod) et SQLite (dev)",
                "Initialiser Git, créer la structure de branches (main/develop)",
            ]),
            ("Apps de base", [
                "Créer l'app `core` : Matiere, Classe, Parametre",
                "Créer l'app `accounts` : User custom (UUID, rôles, matricule auto)",
                "Configurer AUTH_USER_MODEL = 'accounts.User'",
                "Créer les migrations initiales et appliquer",
                "Créer un superuser admin de test",
            ]),
            ("Authentification", [
                "Implémenter les vues login/logout/register",
                "Configurer LaravelAuthBackend (SSO externe)",
                "Implémenter Google OAuth (callback, token, création user)",
                "Créer les templates auth (login.html, register.html)",
                "Tester : connexion email/password + Google OAuth",
            ]),
        ]),
        (2, "EXAMENS & COMPOSITIONS", "3 semaines", BLEU, [
            ("App exams", [
                "Créer modèles : Exam, ExamFile, ExamAssignment",
                "Créer modèles examens nationaux : ExamenNational, ExamenNationalMatiere",
                "Vues CRUD examens (create/list/detail/delete)",
                "Formulaires de création avec upload fichier PDF",
                "Workflow approbation (pending → approved par conseiller)",
                "Tester création et publication d'une épreuve",
            ]),
            ("App compositions", [
                "Créer modèles : CompositionSession, StudentAnswer, StudentSubmissionFile",
                "Créer modèles : Resultat, AntiCheatLog",
                "Vue 'salle d'examen' en ligne (plein écran, timer)",
                "Implémentation anti-triche JS (tab change, fullscreen exit, copy-paste)",
                "Système d'upload de copie papier (photo → serveur)",
                "Signal post_save Resultat → trigger bulletin",
                "Tester un cycle complet examen en ligne",
            ]),
        ]),
        (3, "IA & CORRECTION", "3 semaines", VIOLET, [
            ("App ai_engine", [
                "Créer modèles : AICorrection, CorrectionDetail",
                "Implémenter le service multi-AI avec fallback automatique",
                "Intégrer Groq API (provider principal)",
                "Intégrer Google Gemini (fallback 1)",
                "Intégrer Mistral AI (fallback 2)",
                "Intégrer NVIDIA NeMo (premium OCR)",
            ]),
            ("OCR & Correction", [
                "Implémenter extraction texte PDF (PyMuPDF)",
                "Implémenter OCR Tesseract pour copies papier",
                "Implémenter OCR NVIDIA NeMo (haute précision)",
                "Construire le prompt de correction (barème + critères)",
                "Parser la réponse IA en JSON structuré",
                "Vue validation humaine de la correction IA",
                "Tester correction complète : upload copie → note IA → validation",
            ]),
        ]),
        (4, "QCM & BULLETINS", "2 semaines", ORANGE, [
            ("App qcm", [
                "Créer modèles : QuestionBank, Choice, QCMExam, QCMAnswer, QCMResultat",
                "Interface de création de questions (professeur)",
                "Génération automatique de questions par IA (depuis cours)",
                "Interface de passage du QCM (élève) avec timer",
                "Calcul notes : classique, pénalité, partielle",
                "Feedback IA post-QCM (explications détaillées)",
            ]),
            ("App bulletins", [
                "Créer modèles : Bulletin, BulletinLigne",
                "Service BulletinService.generate_pdf_from_bulletin()",
                "Template PDF officiel (format Ministère Bénin)",
                "Génération PDF avec WeasyPrint ou ReportLab",
                "Signature numérique + token de vérification QR",
                "Vue élève : télécharger son bulletin",
                "Envoi email automatique (Resend)",
                "Tester génération bulletin complet T1",
            ]),
        ]),
        (5, "PAIEMENTS & ABONNEMENTS", "2 semaines", ROUGE, [
            ("FedaPay", [
                "Créer modèles payments : FraisScolaire, Paiement, EcheancierPaiement",
                "Créer modèles abonnements : PlanAbonnementScolaire, AbonnementEleve, PaiementAbonnement",
                "Créer ConfigurationFedaPay par établissement",
                "Intégrer FedaPay SDK (initiation transaction)",
                "Implémenter webhook FedaPay (confirmation paiement)",
                "Pages paiement Mobile Money (MTN, Orange, Wave)",
                "Génération reçu PDF post-paiement",
                "Rappels automatiques d'échéances (3j, 1j)",
                "Tester cycle complet paiement sandbox → production",
            ]),
        ]),
        (6, "TEMPS RÉEL & NOTIFICATIONS", "2 semaines", GRIS_FONCE, [
            ("WebSockets", [
                "Configurer Django Channels avec Redis Layer",
                "Configurer ASGI (asgi.py) + routage WebSocket",
                "Créer consumers : NotificationConsumer, ExamConsumer",
                "Implémenter connexion WebSocket côté client (JS)",
                "Notifications push : nouvelle note, bulletin dispo, message reçu",
                "Dashboard temps réel (résultats live pendant examens)",
            ]),
            ("Notifications", [
                "Créer modèles : Notification, EmailQueue, GlobalAnnouncement",
                "Service d'envoi email via Resend API",
                "Notifications in-app (cloche + badge unread)",
                "File d'attente emails (EmailQueue + worker Redis)",
                "Tester : notification temps réel + email",
            ]),
        ]),
        (7, "GAMIFICATION & MODULES ANNEXES", "2 semaines", VERT, [
            ("Gamification", [
                "Créer modèles : Badge, UserBadge, GlobalLeaderboard, XPAction, StreakRecord",
                "Système d'attribution XP automatique (post-examen, QCM, connexion)",
                "Calcul et mise à jour du leaderboard mondial/national",
                "Attribution automatique de badges selon conditions",
                "Gestion des streaks (série jours consécutifs)",
                "Interface élève : mon niveau, mes badges, mon classement",
            ]),
            ("Modules complémentaires", [
                "App cours : upload et gestion des cours par matière",
                "App devoirs : assignation et remise de devoirs",
                "App attendance : saisie des présences/absences",
                "App cahier : cahier de textes numérique",
                "App library : bibliothèque numérique",
                "App parents : portail accès lecture parents",
                "App certifications : certificats PDF avec QR code vérifiable",
                "App plagiat : détection similitude entre copies",
            ]),
        ]),
        (8, "DÉPLOIEMENT & OPTIMISATION", "1 semaine", ROUGE, [
            ("Déploiement Render", [
                "Configurer render.yaml (web service + worker)",
                "Configurer PostgreSQL sur Render (DATABASE_URL)",
                "Configurer Redis sur Render (REDIS_URL)",
                "Configurer Cloudinary pour les médias (USE_CLOUDINARY_STORAGE=true)",
                "Variables d'environnement production (toutes les clés API)",
                "Configurer HTTPS / HSTS / Security Headers",
                "Configurer Daphne pour ASGI (WebSockets en prod)",
                "Tester le déploiement complet",
            ]),
            ("Optimisation & Sécurité", [
                "Activer cache Redis (CACHE_BACKEND = django-redis)",
                "Optimiser requêtes ORM (select_related, prefetch_related)",
                "Configurer Content-Security-Policy headers",
                "Audit trail : logger toutes les actions sensibles",
                "Rate limiting sur API et authentification",
                "Tests de charge (500+ utilisateurs simultanés)",
                "Documentation API Swagger/OpenAPI (Django Ninja auto)",
                "Configurer sauvegardes automatiques DB (Render backup)",
            ]),
        ]),
    ]

    for (num, titre, duree, col, tasks) in phases:
        phase_header = Table(
            [[Paragraph(f"PHASE {num}", PHASE_TITRE),
              Paragraph(titre, PHASE_TITRE),
              Paragraph(f"⏱ {duree}", PHASE_TITRE)]],
            colWidths=[3*cm, 9*cm, 4*cm]
        )
        phase_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), col),
            ('BOX', (0, 0), (-1, -1), 1, BLANC),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), [6, 6, 0, 0]),
        ]))
        story.append(phase_header)

        all_tasks_data = []
        task_num = 1
        for (cat_name, task_list) in tasks:
            all_tasks_data.append([
                Paragraph(f"<b>{cat_name}</b>", ParagraphStyle("cn",
                    fontSize=9, textColor=col, fontName="Helvetica-Bold",
                    backColor=GRIS_CLAIR, leading=12)),
                Paragraph("", CORPS_SMALL),
                Paragraph("", CORPS_SMALL),
            ])
            for task in task_list:
                all_tasks_data.append([
                    Paragraph(f"{task_num:02d}", ParagraphStyle("tn",
                        fontSize=9, textColor=BLANC, fontName="Helvetica-Bold",
                        backColor=col, alignment=TA_CENTER, leading=12)),
                    Paragraph(task, CORPS_SMALL),
                    Paragraph("☐", ParagraphStyle("chk", fontSize=12,
                        alignment=TA_CENTER, textColor=VERT)),
                ])
                task_num += 1

        task_table = Table(all_tasks_data, colWidths=[1.2*cm, 13*cm, 1.8*cm])
        task_style = [
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ]
        for i, (cat_name, _) in enumerate(tasks):
            row_idx = sum(len(tl) + 1 for _, tl in tasks[:tasks.index((cat_name, _))])
            task_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), GRIS_CLAIR))
            task_style.append(('SPAN', (0, row_idx), (-1, row_idx)))
        task_table.setStyle(TableStyle(task_style))
        story.append(task_table)
        story.append(sp(12))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # 10. SÉCURITÉ
    # ═══════════════════════════════════════════════════════════════════════
    story.append(h1("10. SÉCURITÉ & PERFORMANCE"))
    story.append(sp(8))

    story += h2("10.1 Mesures de Sécurité Implémentées")
    secu_data = [
        [p("<b>Mesure</b>", TABLE_HEADER), p("<b>Implémentation</b>", TABLE_HEADER), p("<b>Statut</b>", TABLE_HEADER)],
        [p("CSRF Protection", CORPS_SMALL), p("CsrfViewMiddleware actif sur toutes les vues POST", CORPS_SMALL), p("✅ Actif", CORPS_SMALL)],
        [p("XSS Protection", CORPS_SMALL), p("SECURE_BROWSER_XSS_FILTER + Content-Security-Policy header", CORPS_SMALL), p("✅ Actif", CORPS_SMALL)],
        [p("Clickjacking", CORPS_SMALL), p("X_FRAME_OPTIONS = 'DENY'", CORPS_SMALL), p("✅ Actif", CORPS_SMALL)],
        [p("HTTPS / HSTS", CORPS_SMALL), p("SECURE_SSL_REDIRECT + HSTS 1 an en production", CORPS_SMALL), p("✅ Prod", CORPS_SMALL)],
        [p("Permissions-Policy", CORPS_SMALL), p("Désactivation caméra/micro/geo non autorisés", CORPS_SMALL), p("✅ Actif", CORPS_SMALL)],
        [p("Session sécurisée", CORPS_SMALL), p("SESSION_COOKIE_SECURE + HTTPONLY + 7 jours", CORPS_SMALL), p("✅ Actif", CORPS_SMALL)],
        [p("Mot de passe", CORPS_SMALL), p("Validators Django : longueur min 8, communs, numériques", CORPS_SMALL), p("✅ Actif", CORPS_SMALL)],
        [p("Audit Trail", CORPS_SMALL), p("App audittrail : log toutes actions sensibles", CORPS_SMALL), p("✅ Actif", CORPS_SMALL)],
        [p("Anti-triche", CORPS_SMALL), p("Tab change, fullscreen exit, multi-face, copy-paste detection", CORPS_SMALL), p("✅ Actif", CORPS_SMALL)],
        [p("Rate Limiting", CORPS_SMALL), p("À implémenter sur login et API endpoints", CORPS_SMALL), p("🔄 Planifié", CORPS_SMALL)],
        [p("2FA", CORPS_SMALL), p("À implémenter (TOTP via django-otp)", CORPS_SMALL), p("🔄 Planifié", CORPS_SMALL)],
    ]
    story.append(tableau(secu_data, [4*cm, 8*cm, 3*cm]))
    story.append(sp(8))

    story += h2("10.2 Variables d'Environnement Requises")
    story.append(p(code := """
DJANGO_SECRET_KEY=...         # Clé secrète Django (50+ chars)
DEBUG=False                   # TOUJOURS False en production
DATABASE_URL=postgres://...   # URL PostgreSQL Render
REDIS_URL=redis://...         # URL Redis Render
GROQ_API_KEY=gsk_...          # Provider IA principal
GEMINI_API_KEY=...            # Fallback IA 1
MISTRAL_API_KEY=...           # Fallback IA 2
NVIDIA_API_KEY=...            # OCR premium
RESEND_API_KEY=re_...         # Emails transactionnels
GOOGLE_CLIENT_ID=...          # OAuth Google
GOOGLE_CLIENT_SECRET=...      # OAuth Google
USE_CLOUDINARY_STORAGE=true   # Stockage médias cloud
CLOUDINARY_URL=cloudinary://KEY:SECRET@CLOUD
SITE_URL=https://academie-composition.onrender.com
""", CODE))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # 11. DÉPLOIEMENT
    # ═══════════════════════════════════════════════════════════════════════
    story.append(h1("11. DÉPLOIEMENT & INFRASTRUCTURE"))
    story.append(sp(8))

    story += h2("11.1 Configuration Render (render.yaml)")
    story.append(p("""
services:
  - type: web
    name: academie-numerique
    env: python
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic
    startCommand: daphne -b 0.0.0.0 -p $PORT academie_numerique.asgi:application
    envVars: [...toutes les variables ci-dessus...]

  - type: worker
    name: academie-worker
    startCommand: python manage.py process_tasks  # ou daphne worker

databases:
  - name: academie-db
    databaseName: academie_numerique
    plan: starter

  - name: academie-redis
    plan: starter
""", CODE))
    story.append(sp(8))

    story += h2("11.2 Procfile (backup)")
    story.append(p("web: daphne -b 0.0.0.0 -p $PORT academie_numerique.asgi:application\nworker: python manage.py process_tasks", CODE))
    story.append(sp(8))

    deploy_data = [
        [p("<b>Étape</b>", TABLE_HEADER), p("<b>Commande</b>", TABLE_HEADER)],
        [p("1. Installer dépendances", CORPS_SMALL), p("pip install -r requirements.txt", CODE)],
        [p("2. Variables d'env", CORPS_SMALL), p("cp .env.example .env && éditer", CODE)],
        [p("3. Migrations DB", CORPS_SMALL), p("python manage.py migrate", CODE)],
        [p("4. Collecter statiques", CORPS_SMALL), p("python manage.py collectstatic --noinput", CODE)],
        [p("5. Créer superuser", CORPS_SMALL), p("python manage.py createsuperuser", CODE)],
        [p("6. Lancer dev", CORPS_SMALL), p("python manage.py runserver 0.0.0.0:8000", CODE)],
        [p("7. Lancer prod (ASGI)", CORPS_SMALL), p("daphne -b 0.0.0.0 -p 8000 academie_numerique.asgi:application", CODE)],
    ]
    story.append(tableau(deploy_data, [5*cm, 11*cm], header_color=GRIS_FONCE))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # 12. CRITÈRES DE QUALITÉ
    # ═══════════════════════════════════════════════════════════════════════
    story.append(h1("12. CRITÈRES DE QUALITÉ & VALIDATION"))
    story.append(sp(8))

    story += h2("12.1 Critères de Validation par Phase")
    valid_data = [
        [p("<b>Phase</b>", TABLE_HEADER), p("<b>Critère de Validation</b>", TABLE_HEADER), p("<b>Test</b>", TABLE_HEADER)],
        [p("Phase 1", CORPS_SMALL), p("Un utilisateur peut s'inscrire, se connecter et accéder à son dashboard", CORPS_SMALL), p("Manuel", CORPS_SMALL)],
        [p("Phase 2", CORPS_SMALL), p("Un élève peut passer un examen en ligne de bout en bout", CORPS_SMALL), p("Manuel", CORPS_SMALL)],
        [p("Phase 3", CORPS_SMALL), p("Une copie uploadée est corrigée par l'IA avec une note valide", CORPS_SMALL), p("Manuel", CORPS_SMALL)],
        [p("Phase 4", CORPS_SMALL), p("Un bulletin PDF est généré et téléchargeable après un examen", CORPS_SMALL), p("Manuel", CORPS_SMALL)],
        [p("Phase 5", CORPS_SMALL), p("Un paiement Mobile Money FedaPay sandbox se complète correctement", CORPS_SMALL), p("Sandbox", CORPS_SMALL)],
        [p("Phase 6", CORPS_SMALL), p("Une notification temps réel est reçue en < 1 seconde", CORPS_SMALL), p("Automatisé", CORPS_SMALL)],
        [p("Phase 7", CORPS_SMALL), p("Un badge est attribué après une action et le XP est incrémenté", CORPS_SMALL), p("Manuel", CORPS_SMALL)],
        [p("Phase 8", CORPS_SMALL), p("L'app répond en < 200ms pour 95% des requêtes en production", CORPS_SMALL), p("Load test", CORPS_SMALL)],
    ]
    story.append(tableau(valid_data, [2*cm, 10*cm, 3*cm]))
    story.append(sp(8))

    story += h2("12.2 Checklist Finale")
    checklist = [
        "✅ Toutes les migrations appliquées sans erreur",
        "✅ Admin Django accessible et fonctionnel",
        "✅ Authentification email + Google OAuth opérationnelle",
        "✅ Cycle complet examen : création → composition → correction IA → bulletin PDF",
        "✅ QCM : création questions → passage → résultat → feedback IA",
        "✅ Paiement FedaPay sandbox → webhook → activation abonnement",
        "✅ WebSockets : notifications temps réel opérationnelles",
        "✅ Gamification : XP + badges fonctionnels",
        "✅ HTTPS actif, security headers configurés",
        "✅ Fichiers statiques servis par WhiteNoise",
        "✅ Médias stockés sur Cloudinary",
        "✅ Logs Django configurés (console + fichier)",
        "✅ Variables d'environnement sécurisées (pas de secret en dur)",
        "✅ Application déployée et accessible sur Render",
    ]
    for item in checklist:
        story.append(bullet(item))

    story.append(sp(20))
    story.append(hr(VERT, 2))
    story.append(sp(6))
    footer_data = [[
        Paragraph("Académie Numérique", ParagraphStyle("f1", fontSize=11, fontName="Helvetica-Bold", textColor=VERT, alignment=TA_CENTER)),
        Paragraph("Cahier des Charges v1.0", ParagraphStyle("f2", fontSize=9, fontName="Helvetica", textColor=GRIS_MOYEN, alignment=TA_CENTER)),
        Paragraph("Mai 2026 — Bénin, Afrique", ParagraphStyle("f3", fontSize=9, fontName="Helvetica", textColor=GRIS_MOYEN, alignment=TA_CENTER)),
    ]]
    ft = Table(footer_data, colWidths=[W/3]*3)
    ft.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,-1), VERT_CLAIR),
        ('BOX', (0,0), (-1,-1), 1, VERT),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(ft)

    # ─── CALLBACKS DE PAGE ──────────────────────────────────────────────────
    def header_footer(canvas, doc):
        canvas.saveState()
        # Header
        if doc.page > 1:
            canvas.setFillColor(VERT)
            canvas.rect(1.5*cm, A4[1]-1.3*cm, A4[0]-3*cm, 0.5*cm, fill=1, stroke=0)
            canvas.setFillColor(BLANC)
            canvas.setFont("Helvetica-Bold", 8)
            canvas.drawString(1.7*cm, A4[1]-1.1*cm, "ACADÉMIE NUMÉRIQUE")
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(A4[0]-1.7*cm, A4[1]-1.1*cm, "Cahier des Charges Technique & Fonctionnel v1.0")
        # Footer
        canvas.setFillColor(GRIS_CLAIR)
        canvas.rect(1.5*cm, 0.8*cm, A4[0]-3*cm, 0.5*cm, fill=1, stroke=0)
        canvas.setFillColor(GRIS_MOYEN)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(1.7*cm, 0.9*cm, "© 2026 Académie Numérique — Bénin, Afrique de l'Ouest")
        canvas.drawRightString(A4[0]-1.7*cm, 0.9*cm, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"✅ PDF généré : {OUTPUT}")

if __name__ == "__main__":
    build()
