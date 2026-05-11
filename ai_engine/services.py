import os
import logging
import json
import requests
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Tentative d'import de Groq
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# Nouvelle bibliothèque Gemini (google-genai) supportée
try:
    from google import genai
    from google.genai import types
    HAS_NEW_GENAI = True
except ImportError:
    try:
        import google.generativeai as old_genai
        HAS_NEW_GENAI = False
    except ImportError:
        HAS_NEW_GENAI = None


def _preprocess_image_for_ocr(image):
    """Prétraitement d'image pour améliorer la qualité OCR."""
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        # Convertir en niveaux de gris
        if image.mode != 'L':
            image = image.convert('L')
        # Augmenter la netteté
        image = image.filter(ImageFilter.SHARPEN)
        # Améliorer le contraste
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        # Améliorer la luminosité si nécessaire
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)
        # Redimensionner si trop petite (minimum 300 DPI équivalent)
        w, h = image.size
        if w < 1500 or h < 2000:
            scale = max(1500 / w, 2000 / h)
            image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    except Exception as e:
        logger.debug(f"Prétraitement image partiel: {e}")
    return image


def extract_text_from_file(file_path: str) -> str:
    """
    Extrait le texte complet d'un fichier (texte brut, PDF, ou image via OCR).
    Aucune limite de caractères — tout le contenu est extrait pour une correction IA précise.
    Pour les images : prétraitement automatique (contraste, netteté, redimensionnement)
    pour minimiser les erreurs d'extraction OCR.
    """
    if not os.path.exists(file_path):
        logger.warning(f"Fichier introuvable: {file_path}")
        return ""

    ext = os.path.splitext(file_path)[1].lower()

    # Fichiers texte brut
    if ext in ['.txt', '.md', '.csv']:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erreur lecture fichier texte {file_path}: {e}")
            return ""

    # Fichiers PDF — extraction texte + OCR des pages scannées
    if ext == '.pdf':
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text_parts = []
            for page_num, page in enumerate(doc):
                # Essai extraction texte natif d'abord
                page_text = page.get_text().strip()
                if len(page_text) > 50:
                    text_parts.append(page_text)
                else:
                    # Page scannée : rendre en image haute résolution et OCR
                    try:
                        from PIL import Image
                        import pytesseract, io
                        # 300 DPI pour qualité maximale
                        mat = fitz.Matrix(300 / 72, 300 / 72)
                        pix = page.get_pixmap(matrix=mat, alpha=False)
                        img_bytes = pix.tobytes("png")
                        image = Image.open(io.BytesIO(img_bytes))
                        image = _preprocess_image_for_ocr(image)
                        ocr_text = pytesseract.image_to_string(
                            image, lang='fra+eng',
                            config='--psm 1 --oem 3'
                        )
                        if ocr_text.strip():
                            text_parts.append(f"[Page {page_num + 1}]\n{ocr_text}")
                    except Exception as ocr_err:
                        logger.warning(f"OCR page {page_num + 1} impossible: {ocr_err}")
                        if page_text:
                            text_parts.append(page_text)
            doc.close()
            return "\n\n".join(text_parts)
        except ImportError:
            logger.warning("PyMuPDF non installé, tentative lecture brute")
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception:
                return ""
        except Exception as e:
            logger.error(f"Erreur lecture PDF {file_path}: {e}")
            return ""

    # Fichiers image — OCR avec prétraitement haute qualité
    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']:
        try:
            from PIL import Image
            import pytesseract
            image = Image.open(file_path)
            image = _preprocess_image_for_ocr(image)
            # PSM 1 = orientation auto + OSD ; OEM 3 = LSTM neural net (plus précis)
            text = pytesseract.image_to_string(
                image, lang='fra+eng',
                config='--psm 1 --oem 3'
            )
            logger.info(f"OCR réussi sur {file_path}: {len(text)} caractères extraits")
            return text
        except ImportError:
            logger.warning("Pillow ou pytesseract non installé pour OCR")
            return "[Image reçue — OCR non disponible sur ce serveur. Installez Pillow et pytesseract.]"
        except Exception as e:
            logger.error(f"Erreur OCR {file_path}: {e}")
            return ""

    # Autre format : lecture brute
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ""


def build_correction_prompt(corrige_type_text: str, copie_text: str, exam_info: dict) -> str:
    note_max = exam_info.get('note_maximale', 20)
    return f"""
Tu es un correcteur d'examens professionnel et strict.

INFORMATIONS DE L'EXAMEN :
- Titre : {exam_info.get('titre', '')}
- Matière : {exam_info.get('matiere', 'Non spécifiée')}
- Note maximale : {note_max}

CORRIGE TYPE (référence absolue) :
---
{corrige_type_text}
---

COPIE DE L'ELEVE :
---
{copie_text}
---

INSTRUCTIONS CRITIQUES :
1. Corrige EXACTEMENT selon le corrigé type fourni.
2. Sois strict et exigeant dans l'évaluation.
3. Analyse : connaissances, méthodologie, clarté, complétude.
4. Attribue une note précise et justifiée sur {note_max}.
5. Retourne UNIQUEMENT un objet JSON valide avec cette structure :
{{
  "note": <nombre>,
  "appreciation": "<appréciation globale professionnelle>",
  "details": [
    {{"question": "<partie>", "points": <nombre>, "max_points": <nombre>, "commentaire": "<explication>"}}
  ],
  "points_forts_global": "<points forts>",
  "axes_amelioration": "<axes d'amélioration>",
  "niveau_maitrise": "<niveau>",
  "recommandations": "<conseils>"
}}
"""

class AIService:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or getattr(settings, 'AI_PROVIDER', 'gemini')
        self.gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.deepseek_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        self.groq_key = getattr(settings, 'GROQ_API_KEY', '')

        # Initialisation Gemini si nécessaire
        if self.provider == 'gemini' and self.gemini_key:
            if HAS_NEW_GENAI:
                self.client = genai.Client(api_key=self.gemini_key)
            elif HAS_NEW_GENAI is False:
                old_genai.configure(api_key=self.gemini_key)
        
        # Initialisation Groq si nécessaire
        if self.provider == 'groq' and self.groq_key and HAS_GROQ:
            self.groq_client = Groq(api_key=self.groq_key)

    def correct_copy(self, corrige_type_text: str, copie_text: str, exam_info: dict) -> dict:
        prompt = build_correction_prompt(corrige_type_text, copie_text, exam_info)

        if self.provider == 'gemini' and self.gemini_key:
            return self._call_gemini(prompt)
        elif self.provider == 'deepseek' and self.deepseek_key:
            return self._call_deepseek(prompt)
        elif self.provider == 'groq' and self.groq_key and HAS_GROQ:
            return self._call_groq(prompt)
        else:
            logger.warning(f"Fournisseur IA '{self.provider}' non configuré ou clé manquante.")
            return self._fallback_correction(exam_info)

    def _call_gemini(self, prompt: str) -> dict:
        try:
            if HAS_NEW_GENAI:
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                return json.loads(response.text)
            else:
                model = old_genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                text = response.text
                if '```json' in text:
                    text = text.split('```json')[1].split('```')[0]
                elif '```' in text:
                    text = text.split('```')[1].split('```')[0]
                return json.loads(text.strip())
        except Exception as e:
            logger.error(f"Erreur Gemini: {e}")
            return self._fallback_correction({})

    def _call_deepseek(self, prompt: str) -> dict:
        try:
            headers = {
                'Authorization': f'Bearer {self.deepseek_key}',
                'Content-Type': 'application/json',
            }
            data = {
                'model': 'deepseek-chat',
                'messages': [
                    {"role": "system", "content": "You are a professional exam grader. You must output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                'response_format': {'type': 'json_object'},
            }
            resp = requests.post('https://api.deepseek.com/chat/completions', headers=headers, json=data, timeout=120)
            resp.raise_for_status()
            content = resp.json()['choices'][0]['message']['content']
            return json.loads(content)
        except Exception as e:
            logger.error(f"Erreur DeepSeek: {e}")
            return self._fallback_correction({})

    def _call_groq(self, prompt: str) -> dict:
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a professional exam grader. You must output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
            )
            content = chat_completion.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"Erreur Groq: {e}")
            return self._fallback_correction({})

    def _fallback_correction(self, exam_info: dict) -> dict:
        note_max = exam_info.get('note_maximale', 20)
        return {
            "note": 0,
            "appreciation": "Erreur technique lors de la correction. Veuillez réessayer ou contacter un administrateur.",
            "details": [],
            "points_forts_global": "",
            "axes_amelioration": "",
        }

# Instance globale
ai_service = AIService()
