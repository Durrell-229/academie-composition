"""
Test OCR complet : image legere (inline) ET image volumineuse (compression auto).
Lance depuis la racine du projet :
    python test_ocr_large.py
"""
import os, sys, io, base64, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from PIL import Image, ImageDraw, ImageFont


def make_test_image(width: int, height: int, label: str) -> bytes:
    """Generer une image de test avec du texte lisible."""
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/times.ttf",
    ]
    font_big = font_sm = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_big = ImageFont.truetype(fp, max(20, width // 40))
                font_sm  = ImageFont.truetype(fp, max(16, width // 55))
                break
            except Exception:
                pass

    lines = [
        "REPUBLIQUE DU BENIN",
        "MINISTERE DES ENSEIGNEMENTS SECONDAIRE",
        "",
        f"COPIE D'ELEVE -- {label}",
        "",
        "Nom : AGOSSOU Komlan Fidele",
        "Classe : Terminale D -- Lycee Mathieu Boueke",
        "Matiere : Sciences de la Vie et de la Terre (SVT)",
        "Date : 23 mai 2026",
        "",
        "Question 1 :",
        "Decrivez le mecanisme de la photosynthese",
        "en precisant le role de la chlorophylle.",
        "",
        "Reponse :",
        "La photosynthese est un processus biologique par lequel",
        "les plantes convertissent la lumiere solaire en energie",
        "chimique stockee sous forme de glucose.",
        "La chlorophylle absorbe principalement la lumiere rouge",
        "et bleue, reflechissant la verte.",
        "",
        "Note attendue : 14/20",
    ]

    line_h = max(30, width // 35)
    y = line_h
    for line in lines:
        font = font_big if any(k in line for k in ("REPUBLIQUE", "COPIE")) else font_sm
        draw.text((40, y), line, fill=(10, 10, 10), font=font)
        y += int(line_h * 1.4)

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=92)
    return buf.getvalue()


def run_test(label: str, width: int, height: int) -> bool:
    from ai_engine.nvidia_ocr import nvidia_ocr_service

    print(f"\n{'='*60}")
    print(f"TEST : {label}  ({width}x{height} px)")
    print('='*60)

    img_bytes = make_test_image(width, height, label)
    b64_len = len(base64.b64encode(img_bytes))
    print(f"  Taille brute  : {len(img_bytes)//1024} KB")
    print(f"  Base64 length : {b64_len} chars")
    print(f"  Limite API    : {nvidia_ocr_service._BASE64_MAX_CHARS} chars")
    route = "INLINE" if b64_len <= nvidia_ocr_service._BASE64_MAX_CHARS else "COMPRESSION -> INLINE"
    print(f"  Route prevue  : {route}")

    t0 = time.time()
    result = nvidia_ocr_service.extract_text_from_bytes(img_bytes, language='fr')
    elapsed = time.time() - t0

    print(f"\n  Succes   : {result['success']}")
    print(f"  Duree    : {elapsed:.1f}s")
    print(f"  Confiance: {result.get('confidence', 0):.1f}%")
    if result.get('error'):
        print(f"  ERREUR   : {result['error']}")
    txt = result.get('text', '')
    print(f"  Texte ({len(txt)} chars) :")
    for line in txt.splitlines()[:8]:
        print(f"    {line}")
    if len(txt.splitlines()) > 8:
        print(f"    ... (+{len(txt.splitlines())-8} lignes)")
    return result['success']


if __name__ == '__main__':
    print("\n=== TEST OCR NVIDIA NEMOTRON ===\n")

    # Image moderee : doit passer inline (< 175K chars b64)
    ok1 = run_test("IMAGE MODEREE (inline)", width=900, height=700)
    # Image A4 haute resolution : doit etre compressee automatiquement
    ok2 = run_test("IMAGE A4 HD (compression auto)", width=2480, height=3508)

    print(f"\n{'='*60}")
    print(f"RESUME")
    print(f"  Image moderee (inline)          : {'OK' if ok1 else 'ECHEC'}")
    print(f"  Image A4 HD  (compression auto) : {'OK' if ok2 else 'ECHEC'}")
    print('='*60)
