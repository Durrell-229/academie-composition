"""
Service OCR pour la correction automatique des copies physiques d'examens
Extrait le texte des images et utilise l'IA pour corriger
"""

import os
import base64
from io import BytesIO
from typing import Dict, Any, Optional
from PIL import Image
import requests

from django.conf import settings
from django.core.files.storage import default_storage
from core.models import Matiere
from .models import AIProvider


class OCRCorrectionService:
    """Service de correction OCR pour copies physiques"""
    
    def __init__(self):
        self.provider = self._get_active_provider()
        
    def _get_active_provider(self):
        """Récupérer le provider IA actif"""
        try:
            return AIProvider.objects.filter(is_active=True, use_for_corrections=True).first()
        except:
            return None
    
    def _encode_image(self, image_path: str) -> str:
        """Encoder une image en base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _compress_image(self, image_path: str, max_size=(1024, 1024)) -> str:
        """Compresser une image pour l'API"""
        img = Image.open(image_path)
        
        # Convertir en RGB si nécessaire
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Redimensionner si trop grande
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Sauvegarder dans un buffer
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        
        # Encoder en base64
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def extraire_texte_ocr(self, image_path: str) -> Dict[str, Any]:
        """Extraire le texte d'une image avec OCR"""
        try:
            if not self.provider:
                return {
                    'success': False,
                    'error': 'Aucun provider IA configuré'
                }
            
            # Encoder l'image
            image_base64 = self._compress_image(image_path)
            
            # Prompt pour l'OCR
            prompt = """Tu es un système OCR spécialisé pour les copies d'examens scolaires.

Analyse cette image de copie d'examen et extraits :
1. TOUT le texte écrit par l'élève (questions et réponses)
2. La structure de la copie (numéros de questions, sections)
3. Les annotations ou corrections déjà présentes

Format de sortie attendu :
```
COPIE ANALYSEE :
================

[Texte extrait complet et fidèle]

STRUCTURE IDENTIFIÉE :
- Question X : [contenu]
- Réponse X : [contenu]

NOTES IMPORTANTES :
[Remarques sur la lisibilité, passages illisibles, etc.]
```

Sois précis et exhaustif. Si un passage est illisible, indique-le clairement avec [ILLISIBLE]."""
            
            # Appel à l'API selon le provider
            resultat = self._call_vision_api(image_base64, prompt)
            
            return {
                'success': True,
                'texte_extrait': resultat.get('text', ''),
                'raw_response': resultat
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur OCR: {str(e)}'
            }
    
    def corriger_copie(self, copie) -> Dict[str, Any]:
        """Corriger une copie avec l'IA"""
        try:
            # Extraire le texte avec OCR
            ocr_result = self.extraire_texte_ocr(copie.image_copie.path)
            
            if not ocr_result['success']:
                return ocr_result
            
            texte_extrait = ocr_result['texte_extrait']
            
            # Récupérer les informations de la matière et du barème
            matiere = copie.matiere
            note_maximale = 20.0  # Par défaut
            
            # Prompt pour la correction
            prompt_correction = f"""Tu es un correcteur d'examens expérimenté pour le système scolaire du Bénin.

MATIÈRE : {matiere.nom}
NOTE MAXIMALE : {note_maximale}/20

COPIE DE L'ÉLÈVE :
==================
{texte_extrait}

INSTRUCTIONS DE CORRECTION :
1. Analyse chaque question et sa réponse
2. Attribue des points partiels selon la qualité
3. Identifie les erreurs et donne des explications constructives
4. Calcule la note finale sur 20

Format de sortie JSON obligatoire :
```json
{{
    "note_suggeree": 15.5,
    "note_maximale": 20.0,
    "appreciation": "Bonne copie avec quelques erreurs de calcul...",
    "details_par_question": [
        {{
            "numero": 1,
            "points_attribues": 4.5,
            "points_max": 5.0,
            "commentaire": "Bonne méthode mais erreur de calcul à la fin"
        }}
    ],
    "points_positifs": ["Maîtrise du cours", "Présentation soignée"],
    "points_a_travailler": ["Attention aux calculs", "Justification des réponses"],
    "verdict": "Réussi - Bonne maîtrise de la matière"
}}
```

Sois juste, rigoureux et constructif."""
            
            # Appel à l'API pour la correction
            correction_result = self._call_text_api(prompt_correction)
            
            # Parser le JSON de la réponse
            import json
            import re
            
            # Extraire le JSON de la réponse
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', correction_result.get('text', ''), re.DOTALL)
            if json_match:
                correction_json = json.loads(json_match.group(1))
            else:
                # Essayer de parser directement
                try:
                    correction_json = json.loads(correction_result.get('text', '{}'))
                except:
                    correction_json = self._parse_correction_fallback(correction_result.get('text', ''))
            
            return {
                'success': True,
                'texte_extrait': texte_extrait,
                'correction': correction_json,
                'note_suggeree': correction_json.get('note_suggeree', 0.0),
                'raw_response': correction_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur correction: {str(e)}'
            }
    
    def _parse_correction_fallback(self, text: str) -> Dict:
        """Parser la correction si le JSON est mal formaté"""
        import re
        
        result = {
            'note_suggeree': 0.0,
            'note_maximale': 20.0,
            'appreciation': '',
            'details_par_question': [],
            'points_positifs': [],
            'points_a_travailler': [],
            'verdict': ''
        }
        
        # Extraire la note
        note_match = re.search(r'(?:note|score).*?(\d+(?:[.,]\d+)?)', text, re.IGNORECASE)
        if note_match:
            result['note_suggeree'] = float(note_match.group(1).replace(',', '.'))
        
        # Extraire l'appréciation (première phrase complète)
        lines = text.split('\n')
        for line in lines:
            if len(line) > 20 and not line.startswith(('```', '{', '[')):
                result['appreciation'] = line.strip()
                break
        
        return result
    
    def _call_vision_api(self, image_base64: str, prompt: str) -> Dict:
        """Appeler l'API vision du provider"""
        
        if self.provider.provider_type == 'gemini':
            return self._call_gemini_vision(image_base64, prompt)
        elif self.provider.provider_type == 'openai':
            return self._call_openai_vision(image_base64, prompt)
        elif self.provider.provider_type == 'anthropic':
            return self._call_anthropic_vision(image_base64, prompt)
        else:
            raise ValueError(f"Provider non supporté: {self.provider.provider_type}")
    
    def _call_text_api(self, prompt: str) -> Dict:
        """Appeler l'API texte du provider"""
        
        if self.provider.provider_type == 'gemini':
            return self._call_gemini_text(prompt)
        elif self.provider.provider_type == 'openai':
            return self._call_openai_text(prompt)
        elif self.provider.provider_type == 'anthropic':
            return self._call_anthropic_text(prompt)
        else:
            raise ValueError(f"Provider non supporté: {self.provider.provider_type}")
    
    def _call_gemini_vision(self, image_base64: str, prompt: str) -> Dict:
        """Appeler l'API Gemini Vision"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.provider.api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Créer l'image
        image_data = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_data))
        
        response = model.generate_content([prompt, image])
        
        return {
            'text': response.text,
            'provider': 'gemini'
        }
    
    def _call_openai_vision(self, image_base64: str, prompt: str) -> Dict:
        """Appeler l'API OpenAI Vision"""
        
        headers = {
            'Authorization': f'Bearer {self.provider.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-4o-mini',
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/jpeg;base64,{image_base64}'
                            }
                        }
                    ]
                }
            ],
            'max_tokens': 4096
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload
        )
        
        data = response.json()
        
        return {
            'text': data['choices'][0]['message']['content'],
            'provider': 'openai',
            'raw': data
        }
    
    def _call_anthropic_vision(self, image_base64: str, prompt: str) -> Dict:
        """Appeler l'API Anthropic Vision"""
        
        headers = {
            'x-api-key': self.provider.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': 'claude-3-haiku-20240307',
            'max_tokens': 4096,
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'image',
                            'source': {
                                'type': 'base64',
                                'media_type': 'image/jpeg',
                                'data': image_base64
                            }
                        },
                        {
                            'type': 'text',
                            'text': prompt
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=payload
        )
        
        data = response.json()
        
        return {
            'text': data['content'][0]['text'],
            'provider': 'anthropic',
            'raw': data
        }
    
    def _call_gemini_text(self, prompt: str) -> Dict:
        """Appeler l'API Gemini pour texte"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.provider.api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content(prompt)
        
        return {
            'text': response.text,
            'provider': 'gemini'
        }
    
    def _call_openai_text(self, prompt: str) -> Dict:
        """Appeler l'API OpenAI pour texte"""
        
        headers = {
            'Authorization': f'Bearer {self.provider.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-4o-mini',
            'messages': [
                {'role': 'system', 'content': 'Tu es un correcteur d\'examens expérimenté.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 4096
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload
        )
        
        data = response.json()
        
        return {
            'text': data['choices'][0]['message']['content'],
            'provider': 'openai'
        }
    
    def _call_anthropic_text(self, prompt: str) -> Dict:
        """Appeler l'API Anthropic pour texte"""
        
        headers = {
            'x-api-key': self.provider.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': 'claude-3-haiku-20240307',
            'max_tokens': 4096,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=payload
        )
        
        data = response.json()
        
        return {
            'text': data['content'][0]['text'],
            'provider': 'anthropic'
        }
