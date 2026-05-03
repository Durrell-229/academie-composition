"""
Générateur de Bulletin Scolaire — Style Examen National du Bénin
Utilise reportlab pour un contrôle précis du PDF.
Compatible Django : retourne bytes via io.BytesIO
"""

import io
import os
import segno
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter


# ─── COULEURS ────────────────────────────────────────────────────────────────
VERT_ETAT  = colors.HexColor("#007A5E")   # vert Bénin
ROUGE_ETAT = colors.HexColor("#CE1126")   # rouge Bénin
JAUNE_ETAT = colors.HexColor("#FCD116")   # jaune Bénin
BLEU_TITRE = colors.HexColor("#003399")
GRIS_THEAD = colors.HexColor("#d9d9d9")
ROUGE_MOY  = colors.HexColor("#cc0000")
NOIR       = colors.black
BLANC      = colors.white


def generer_bulletin_examen(data: dict) -> bytes:
    """
    Génère un bulletin d'examen national PDF et retourne les bytes.

    Paramètre `data` attendu :
    {
        "type_examen": "BEPC" | "Baccalauréat C" | "CEP" | "Devoir National",
        "annee_scolaire": "2025-2026",
        "eleve": {
            "nom": "DIOUF",
            "prenom": "BADARA",
            "sexe": "M",
            "matricule": "ELE-2025-00001",
            "classe": "Terminale C",
            "serie": "C",
            "effectif": 42,
            "avatar_url": "/media/profiles/...",  # optionnel
        },
        "semestre": "SESSION 2025" | "SEMESTRE 1",
        "matieres": [
            {
                "discipline": "Mathématiques",
                "devoir": 12.00,       # note de devoir (optionnel)
                "compose": 14.00,      # note d'examen
                "moy_mat": 13.00,      # moyenne matière
                "coeff": 7,
                "moy_coeff": 91.00,
                "rang": 5,
                "appreciation": "Bon travail",
            },
            ...
        ],
        "totaux": {
            "moy_generale": 13.45,
            "rang": 5,
            "retard": 0,
            "absence": 0,
            "justifie": 0,
            "non_justifie": 0,
        },
        "observations_jury": [
            {"label": "Félicitations du jury", "valeur": ""},
            {"label": "Encouragements",        "valeur": ""},
            {"label": "Admis",                 "valeur": ""},
            {"label": "Ajourné",               "valeur": ""},
        ],
        "observations_profs": "Continue tes efforts.",
        "decision": "ADMIS",
        "verification_token": "uuid-here",
    }
    """
    buffer = io.BytesIO()
    page_width, page_height = A4
    c = canvas.Canvas(buffer, pagesize=A4)

    marge_g = 15 * mm
    marge_d = page_width - 15 * mm
    largeur = marge_d - marge_g
    y = page_height - 10 * mm

    eleve = data["eleve"]
    totaux = data["totaux"]
    type_examen = data.get("type_examen", "Examen National")

    # ─── HELPER ──────────────────────────────────────────────────────────────
    def texte(x, yy, txt, taille=8, gras=False, couleur=NOIR, align="left"):
        c.setFillColor(couleur)
        nom_font = "Helvetica-Bold" if gras else "Helvetica"
        c.setFont(nom_font, taille)
        if align == "center":
            c.drawCentredString(x, yy, str(txt))
        elif align == "right":
            c.drawRightString(x, yy, str(txt))
        else:
            c.drawString(x, yy, str(txt))

    def ligne_h(y1, x1=None, x2=None, epaisseur=0.5, couleur=NOIR):
        c.setStrokeColor(couleur)
        c.setLineWidth(epaisseur)
        c.line(x1 or marge_g, y1, x2 or marge_d, y1)

    def rect_fill(x, y_bas, w, h, fill_color, stroke_color=None):
        c.setFillColor(fill_color)
        if stroke_color:
            c.setStrokeColor(stroke_color)
            c.rect(x, y_bas, w, h, fill=1, stroke=1)
        else:
            c.rect(x, y_bas, w, h, fill=1, stroke=0)

    # ═══════════════════════════════════════════════════════════════════════
    # BLOC 1 — EN-TÊTE ÉTAT (Drapeau Bénin)
    # ═══════════════════════════════════════════════════════════════════════
    # Barre drapeau (Vert-Jaune-Rouge)
    bar_h = 6 * mm
    rect_fill(marge_g, y - bar_h, largeur / 3, bar_h, VERT_ETAT)
    rect_fill(marge_g + largeur / 3, y - bar_h, largeur / 3, bar_h, JAUNE_ETAT)
    rect_fill(marge_g + 2 * largeur / 3, y - bar_h, largeur / 3, bar_h, ROUGE_ETAT)
    y -= bar_h + 4 * mm

    texte(page_width / 2, y, "RÉPUBLIQUE DU BÉNIN", taille=9, gras=True, couleur=VERT_ETAT, align="center")
    y -= 5 * mm
    texte(page_width / 2, y, "MINISTÈRE DE L'ENSEIGNEMENT SECONDAIRE,", taille=7.5, couleur=VERT_ETAT, align="center")
    y -= 4 * mm
    texte(page_width / 2, y, "TECHNIQUE ET DE LA FORMATION PROFESSIONNELLE", taille=7.5, couleur=VERT_ETAT, align="center")
    y -= 6 * mm

    # Nom établissement
    texte(page_width / 2, y, "ACADÉMIE NUMÉRIQUE INTELLIGENTE", taille=13, gras=True, couleur=BLEU_TITRE, align="center")
    y -= 5 * mm
    texte(page_width / 2, y, f"Année scolaire : {data['annee_scolaire']}", taille=8, align="center")

    # Ligne séparatrice
    y -= 3 * mm
    ligne_h(y, epaisseur=1.5, couleur=VERT_ETAT)
    y -= 5 * mm

    # ═══════════════════════════════════════════════════════════════════════
    # BLOC 2 — INFOS ÉLÈVE (2 colonnes)
    # ═══════════════════════════════════════════════════════════════════════
    col_g = marge_g
    col_m = page_width / 2 + 5 * mm
    line_h = 4.8 * mm

    def info_ligne(label, valeur, x, yy, larg_label=22*mm):
        texte(x, yy, label, taille=7.5, gras=True)
        texte(x + larg_label, yy, valeur, taille=7.5)

    # Colonne gauche
    info_ligne("Niveau :", eleve.get("classe", ""), col_g, y)
    y -= line_h
    info_ligne("Série :", eleve.get("serie", ""), col_g, y)
    y -= line_h
    info_ligne("Sexe :", eleve.get("sexe", ""), col_g, y)
    y -= line_h
    info_ligne("Effectif :", str(eleve.get("effectif", "")), col_g, y)

    # Colonne droite
    y_reset = y + 3 * line_h
    info_ligne("Matricule :", eleve.get("matricule", ""), col_m, y_reset)
    y_reset -= line_h
    info_ligne("Classe :", eleve.get("classe", ""), col_m, y_reset)

    y -= 4 * mm

    # Nom complet élève
    y -= 3 * mm
    texte(page_width / 2, y, f"Nom : {eleve['nom']}   Prénom : {eleve.get('prenom', '')}", taille=9, gras=True, align="center")

    # Ligne séparatrice
    y -= 3 * mm
    ligne_h(y, epaisseur=1, couleur=VERT_ETAT)
    y -= 5 * mm

    # ═══════════════════════════════════════════════════════════════════════
    # BLOC 3 — TITRE BULLETIN
    # ═══════════════════════════════════════════════════════════════════════
    texte(page_width / 2, y, f"BULLETIN DE {type_examen} — {data['semestre']}",
          taille=11, gras=True, couleur=BLEU_TITRE, align="center")
    y -= 8 * mm

    # ═══════════════════════════════════════════════════════════════════════
    # BLOC 4 — TABLEAU DES MATIÈRES
    # ═══════════════════════════════════════════════════════════════════════
    cols = {
        "discipline":   {"label": "DISCIPLINES",        "w": 48 * mm, "align": "left"},
        "coeff":        {"label": "COEF",               "w": 12 * mm, "align": "center"},
        "devoir":       {"label": "DEVOIR",             "w": 16 * mm, "align": "center"},
        "compose":      {"label": "COMPOSÉ",            "w": 16 * mm, "align": "center"},
        "moy_mat":      {"label": "MOY.MAT",            "w": 16 * mm, "align": "center"},
        "moy_coeff":    {"label": "MOY×COEF",           "w": 18 * mm, "align": "center"},
        "rang":         {"label": "RANG",               "w": 12 * mm, "align": "center"},
        "appreciation": {"label": "APPRÉCIATIONS",      "w": 30 * mm, "align": "left"},
    }

    row_h = 6.5 * mm
    head_h = 7 * mm
    x_start = marge_g

    x_positions = {}
    cx = x_start
    for key, col in cols.items():
        x_positions[key] = cx
        cx += col["w"]

    tab_w = cx - x_start

    # En-tête tableau — fond gris
    rect_fill(x_start, y - head_h, tab_w, head_h, GRIS_THEAD, NOIR)
    c.setStrokeColor(NOIR)
    c.setLineWidth(0.5)
    c.rect(x_start, y - head_h, tab_w, head_h, fill=0, stroke=1)

    for key, col in cols.items():
        xh = x_positions[key] + (col["w"] / 2 if col["align"] == "center" else 1.5 * mm)
        texte(xh, y - head_h + 2.5 * mm, col["label"], taille=7, gras=True, align=col["align"])
        c.setStrokeColor(NOIR)
        c.setLineWidth(0.3)
        c.line(x_positions[key], y, x_positions[key], y - head_h)

    y -= head_h

    # Lignes matières
    for i, mat in enumerate(data["matieres"]):
        bg = colors.HexColor("#f5f5f5") if i % 2 == 0 else BLANC
        rect_fill(x_start, y - row_h, tab_w, row_h, bg, NOIR)

        c.setStrokeColor(colors.HexColor("#cccccc"))
        c.setLineWidth(0.3)
        c.line(x_start, y - row_h, x_start + tab_w, y - row_h)

        for key in cols:
            c.setStrokeColor(colors.HexColor("#cccccc"))
            c.line(x_positions[key], y, x_positions[key], y - row_h)

        y_txt = y - row_h + 2 * mm

        def val_mat(key, valeur):
            col = cols[key]
            if col["align"] == "center":
                xv = x_positions[key] + col["w"] / 2
            else:
                xv = x_positions[key] + 1.5 * mm
            if valeur is None or valeur == "":
                txt = ""
            elif isinstance(valeur, float):
                txt = f"{valeur:.2f}"
            else:
                txt = str(valeur)

            couleur_val = NOIR
            if key == "moy_mat" and isinstance(valeur, float) and valeur < 10:
                couleur_val = ROUGE_MOY

            texte(xv, y_txt, txt, taille=7.5, couleur=couleur_val, align=col["align"])

        val_mat("discipline",   mat["discipline"])
        val_mat("coeff",        mat.get("coeff"))
        val_mat("devoir",       mat.get("devoir"))
        val_mat("compose",      mat.get("compose"))
        val_mat("moy_mat",      mat.get("moy_mat"))
        val_mat("moy_coeff",    mat.get("moy_coeff"))
        val_mat("rang",         mat.get("rang", ""))
        val_mat("appreciation", mat.get("appreciation", ""))

        y -= row_h

    # Bordure extérieure tableau
    c.setStrokeColor(NOIR)
    c.setLineWidth(1)
    c.rect(x_start, y, tab_w, len(data["matieres"]) * row_h + head_h, fill=0, stroke=1)

    y -= 1 * mm

    # ═══════════════════════════════════════════════════════════════════════
    # BLOC 5 — LIGNE TOTAUX
    # ═══════════════════════════════════════════════════════════════════════
    tot_h = 7 * mm
    rect_fill(x_start, y - tot_h, tab_w, tot_h, GRIS_THEAD, NOIR)

    y_tot = y - tot_h + 2 * mm
    texte(x_start + 2 * mm, y_tot, "TOTAUX", taille=8, gras=True)

    texte(x_start + 45 * mm, y_tot,
          f"MOY. GÉNÉRALE : {totaux['moy_generale']:.2f}/20", taille=9, gras=True, couleur=BLEU_TITRE)

    texte(x_start + 100 * mm, y_tot,
          f"RANG : {totaux['rang']}/{totaux.get('effectif', '?')}", taille=8, gras=True)

    texte(x_start + 140 * mm, y_tot,
          f"Retard : {totaux.get('retard', 0)}   Abs : {totaux.get('absence', 0)}", taille=7)

    c.setStrokeColor(NOIR)
    c.setLineWidth(1)
    c.rect(x_start, y - tot_h, tab_w, tot_h, fill=0, stroke=1)

    y -= tot_h + 6 * mm

    # ═══════════════════════════════════════════════════════════════════════
    # BLOC 6 — RÉSULTAT FINAL & DÉCISION
    # ═══════════════════════════════════════════════════════════════════════
    moy = totaux['moy_generale']
    if moy >= 16:
        mention_txt, mention_couleur = "EXCELLENT", VERT_ETAT
    elif moy >= 14:
        mention_txt, mention_couleur = "TRÈS BIEN", BLEU_TITRE
    elif moy >= 12:
        mention_txt, mention_couleur = "BIEN", colors.HexColor("#009900")
    elif moy >= 10:
        mention_txt, mention_couleur = "ASSEZ BIEN", colors.HexColor("#cc6600")
    else:
        mention_txt, mention_couleur = "INSUFFISANT", ROUGE_MOY

    decision = data.get("decision", "")

    res_h = 14 * mm
    rect_fill(x_start, y - res_h, tab_w, res_h, colors.HexColor("#f0f8f0"), VERT_ETAT)
    texte(page_width / 2, y - 4 * mm,
          f"MOYENNE GÉNÉRALE : {moy:.2f}/20  —  MENTION : {mention_txt}",
          taille=10, gras=True, couleur=mention_couleur, align="center")
    if decision:
        texte(page_width / 2, y - 9 * mm,
              f"DÉCISION : {decision}",
              taille=9, gras=True, couleur=BLEU_TITRE, align="center")

    c.setStrokeColor(VERT_ETAT)
    c.setLineWidth(1)
    c.rect(x_start, y - res_h, tab_w, res_h, fill=0, stroke=1)

    y -= res_h + 4 * mm

    # ═══════════════════════════════════════════════════════════════════════
    # BLOC 7 — OBSERVATIONS (2 colonnes)
    # ═══════════════════════════════════════════════════════════════════════
    col_obs_g_w = 80 * mm
    col_obs_d_w = tab_w - col_obs_g_w

    obs_jury = data.get("observations_jury", [])
    obs_prof = data.get("observations_profs", "")

    obs_h = max(len(obs_jury) * 5.5 * mm + 12 * mm, 40 * mm)

    # Colonne gauche : Observations
    rect_fill(x_start, y - obs_h, col_obs_g_w, obs_h, colors.HexColor("#f9f9f9"), NOIR)
    texte(x_start + col_obs_g_w / 2, y - 5 * mm,
          "OBSERVATIONS DU CONSEIL / JURY", taille=7, gras=True, align="center")

    y_obs = y - 10 * mm
    for obs in obs_jury:
        texte(x_start + 2 * mm, y_obs, obs["label"], taille=7)
        c.setStrokeColor(NOIR)
        c.setLineWidth(0.5)
        c.rect(x_start + col_obs_g_w - 6 * mm, y_obs - 1 * mm, 4 * mm, 3.5 * mm, fill=0, stroke=1)
        if obs.get("valeur"):
            texte(x_start + col_obs_g_w - 5 * mm, y_obs, "X", taille=7)
        y_obs -= 5.5 * mm

    if obs_prof:
        texte(x_start + 2 * mm, y_obs, f"Observation : {obs_prof}", taille=7, couleur=ROUGE_MOY)

    # Colonne droite : Chef d'établissement + signature
    x_d = x_start + col_obs_g_w
    rect_fill(x_d, y - obs_h, col_obs_d_w, obs_h, BLANC, NOIR)
    texte(x_d + col_obs_d_w / 2, y - 8 * mm, "Le Chef d'Établissement", taille=8, gras=True, align="center")
    texte(x_d + col_obs_d_w / 2, y - obs_h + 10 * mm,
          "_______________________", taille=8, align="center")
    texte(x_d + col_obs_d_w / 2, y - obs_h + 6 * mm,
          "Signature et cachet", taille=6.5, couleur=colors.grey, align="center")

    c.setStrokeColor(NOIR)
    c.setLineWidth(1)
    c.rect(x_start, y - obs_h, tab_w, obs_h, fill=0, stroke=1)

    # ═══════════════════════════════════════════════════════════════════════
    # BLOC 8 — VÉRIFICATION & QR (espace réservé)
    # ═══════════════════════════════════════════════════════════════════════
    y -= obs_h + 3 * mm
    ligne_h(y, epaisseur=0.5, couleur=colors.grey)
    y -= 4 * mm

    token = data.get("verification_token", "")
    texte(marge_g, y, f"AUTH-ID: {token}", taille=7, couleur=colors.grey)
    texte(marge_g, y - 4 * mm,
          "Document certifié conforme — Plateforme Académie Numérique IA",
          taille=6.5, couleur=colors.grey)

    # Espace QR à droite
    qr_x = marge_d - 20 * mm
    qr_y = y - 2 * mm
    c.setStrokeColor(NOIR)
    c.setLineWidth(0.5)
    c.rect(qr_x, qr_y - 15 * mm, 15 * mm, 15 * mm, fill=0, stroke=1)
    texte(qr_x + 7.5 * mm, qr_y - 20 * mm, "QR CODE", taille=6, align="center", couleur=colors.grey)

    # ═══════════════════════════════════════════════════════════════════════
    # NOTE DE BAS DE PAGE
    # ═══════════════════════════════════════════════════════════════════════
    y -= obs_h * 0.15 + 2 * mm
    texte(marge_g, y,
          "N.B. : Ce bulletin n'est délivré qu'une seule fois. Toute demande de duplicata pourrait faire l'objet d'un contrôle rigoureux.",
          taille=6, couleur=colors.grey)

    # Barre drapeau footer
    y -= 6 * mm
    rect_fill(marge_g, y, largeur / 3, 4 * mm, VERT_ETAT)
    rect_fill(marge_g + largeur / 3, y, largeur / 3, 4 * mm, JAUNE_ETAT)
    rect_fill(marge_g + 2 * largeur / 3, y, largeur / 3, 4 * mm, ROUGE_ETAT)

    # ─── FINALISATION ────────────────────────────────────────────────────
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def add_qr_to_pdf(pdf_bytes: bytes, download_url: str) -> bytes:
    """
    Ajoute un QR code réel sur un PDF reportlab existant.
    Utilise pypdf pour merger un QR PNG sur la dernière page.
    """
    import tempfile

    # 1. Générer le QR code PNG
    qr = segno.make(download_url, error='h')
    qr_buffer = io.BytesIO()
    qr.save(qr_buffer, kind='png', scale=8, dark='#000000', light='#ffffff')
    qr_buffer.seek(0)

    # 2. Créer un PDF temporaire avec le QR image
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.units import mm as rl_mm

    qr_pdf_buffer = io.BytesIO()
    c = rl_canvas.Canvas(qr_pdf_buffer, pagesize=A4)

    # Position du QR (bas à droite, correspond à l'espace réservé)
    page_w, page_h = A4
    qr_size = 15 * rl_mm
    x = page_w - 15 * rl_mm - 15 * rl_mm  # marge_d - QR size
    y = page_h - 10 * rl_mm - 6 * rl_mm - 4 * rl_mm - 5 * rl_mm - 7.5 * rl_mm - 5 * rl_mm - 3 * rl_mm - 4 * rl_mm - 15 * rl_mm - 4 * rl_mm - 40 * rl_mm

    c.drawImage(qr_buffer, x, y, width=qr_size, height=qr_size)
    c.showPage()
    c.save()
    qr_pdf_buffer.seek(0)

    # 3. Merger les deux PDFs
    reader = PdfReader(io.BytesIO(pdf_bytes))
    qr_reader = PdfReader(qr_pdf_buffer)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        if i == len(reader.pages) - 1:  # dernière page
            qr_page = qr_reader.pages[0]
            page.merge_page(qr_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.getvalue()
