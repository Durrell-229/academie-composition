import os
import json
import base64
import logging
import requests
from typing import Dict, List, Optional, Union
from PIL import Image
import io
from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

class NVIDIAOCRService:
    """
    Service OCR haute performance utilisant NVIDIA Nemotron (modèle gratuit et performant)
    Spécialisé pour le contexte éducatif béninois
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'NVIDIA_API_KEY', os.getenv('NVIDIA_API_KEY', ''))
        self.base_url = "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v1"
        self.model_name = "nvidia/nemotron-ocr-v1"  # Modèle Nemotron performant
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.pdf']
        
        if not self.api_key:
            logger.warning("NVIDIA_API_KEY non configurée. Utilisation du mode démo.")
        else:
            logger.info(f"NVIDIA Nemotron configuré avec clé API: {self.api_key[:20]}...")
    
    def is_configured(self) -> bool:
        """Vérifier si le service est correctement configuré"""
        return bool(self.api_key)
    
    def preprocess_image(self, image_data: bytes) -> bytes:
        """Prétraiter l'image pour une meilleure reconnaissance OCR"""
        try:
            from PIL import Image, ImageEnhance, ImageFilter
            
            # Ouvrir l'image
            image = Image.open(io.BytesIO(image_data))
            
            # Convertir en RGB si nécessaire
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Amélioration de la qualité pour l'OCR
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            if self._is_text_document(image):
                image = image.convert('L')
                image = self._adaptive_threshold(image)
                image = image.convert('RGB')
            
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=95, optimize=True)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erreur prétraitement image: {e}")
            return image_data
    
    def _is_text_document(self, image: Image.Image) -> bool:
        """Détecter si l'image est un document texte"""
        width, height = image.size
        pixels = image.load()
        
        white_black_count = 0
        total_count = width * height
        
        for i in range(0, min(width, 1000), 10):
            for j in range(0, min(height, 1000), 10):
                if i < width and j < height:
                    r, g, b = pixels[i, j]
                    if (r > 200 and g > 200 and b > 200) or (r < 50 and g < 50 and b < 50):
                        white_black_count += 1
        
        return (white_black_count / total_count) > 0.6
    
    def _adaptive_threshold(self, image: Image.Image) -> Image.Image:
        """Seuillage adaptatif pour les documents texte"""
        from PIL import ImageOps
        
        if image.getpixel((0, 0)) > 128:
            image = ImageOps.invert(image)
        
        return image
    
    def extract_text_from_image(self, image_path: str, language: str = 'fr') -> Dict:
        """Extraire le texte d'une image avec Nemotron"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            return self.extract_text_from_bytes(image_data, language)
            
        except Exception as e:
            logger.error(f"Erreur extraction texte image {image_path}: {e}")
            return {
                'text': '',
                'confidence': 0,
                'success': False,
                'error': str(e),
                'language_detected': language
            }
    
    def extract_text_from_bytes(self, image_data: bytes, language: str = 'fr') -> Dict:
        """Extraire le texte de bytes d'image avec Nemotron OCR v1"""
        try:
            if not self.is_configured():
                return self._demo_ocr(image_data, language)
            
            processed_image = self.preprocess_image(image_data)
            image_base64 = base64.b64encode(processed_image).decode('utf-8')
            
            # Vérifier la taille de l'image
            assert len(image_base64) < 180_000, "Image trop grande pour l'API OCR"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json"
            }
            
            # Payload spécifique pour l'endpoint OCR NVIDIA
            payload = {
                "input": [
                    {
                        "type": "image_url",
                        "url": f"data:image/png;base64,{image_base64}"
                    }
                ]
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extraire le texte depuis la réponse OCR
                extracted_text = ""
                if 'data' in result and len(result['data']) > 0:
                    extracted_text = result['data'][0].get('text', '')
                
                confidence_score = self._calculate_confidence(extracted_text)
                
                return {
                    'text': extracted_text.strip(),
                    'confidence': confidence_score,
                    'success': True,
                    'language_detected': language,
                    'model_used': self.model_name,
                    'processing_time': response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
                    'raw_response': result
                }
            else:
                logger.error(f"Erreur API Nemotron OCR: {response.status_code} - {response.text}")
                return {
                    'text': '',
                    'confidence': 0,
                    'success': False,
                    'error': f"API Error: {response.status_code}",
                    'language_detected': language
                }
                
        except Exception as e:
            logger.error(f"Erreur OCR Nemotron: {e}")
            return {
                'text': '',
                'confidence': 0,
                'success': False,
                'error': str(e),
                'language_detected': language
            }
    
    def extract_text_from_file(self, file_obj, language: str = 'fr') -> Dict:
        """Extraire le texte d'un fichier uploadé"""
        try:
            if hasattr(file_obj, 'read'):
                file_data = file_obj.read()
            else:
                with open(file_obj, 'rb') as f:
                    file_data = f.read()
            
            file_extension = os.path.splitext(getattr(file_obj, 'name', ''))[1].lower()
            
            if file_extension == '.pdf':
                import pdf2image
                temp_path = f"/tmp/ocr_temp_{hash(file_data)}.pdf"
                with open(temp_path, 'wb') as f:
                    f.write(file_data)
                
                images = pdf2image.convert_from_path(temp_path, dpi=300)
                all_text = []
                total_confidence = 0
                processing_times = []
                
                for i, image in enumerate(images):
                    buffer = io.BytesIO()
                    image.save(buffer, format='JPEG', quality=95)
                    image_data = buffer.getvalue()
                    
                    page_result = self.extract_text_from_bytes(image_data, language)
                    
                    if page_result['success']:
                        all_text.append(page_result['text'])
                        total_confidence += page_result['confidence']
                        if 'processing_time' in page_result:
                            processing_times.append(page_result['processing_time'])
                
                os.remove(temp_path)
                
                return {
                    'text': '\n\n'.join(all_text),
                    'confidence': total_confidence / len(images) if images else 0,
                    'success': len(all_text) > 0,
                    'language_detected': language,
                    'pages_processed': len(images),
                    'model_used': self.model_name,
                    'processing_time': sum(processing_times) if processing_times else 0
                }
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                return self.extract_text_from_bytes(file_data, language)
            else:
                return {
                    'text': '',
                    'confidence': 0,
                    'success': False,
                    'error': f'Format non supporté: {file_extension}',
                    'language_detected': language
                }
                
        except Exception as e:
            logger.error(f"Erreur extraction fichier: {e}")
            return {
                'text': '',
                'confidence': 0,
                'success': False,
                'error': str(e),
                'language_detected': language
            }
    
    def _calculate_confidence(self, text: str) -> float:
        """Calculer un score de confiance basé sur la qualité du texte"""
        if not text:
            return 0.0
        
        score = 50.0
        
        if len(text) > 100:
            score += 10
        if len(text) > 500:
            score += 10
        
        french_words = ['le', 'la', 'les', 'de', 'du', 'des', 'et', 'est', 'sont', 'dans', 'pour', 'avec', 
                        'bénin', 'cotonou', 'porto-novo', 'abomey', 'parakou', 'école', 'élève', 'professeur']
        word_count = sum(1 for word in french_words if word.lower() in text.lower())
        score += min(word_count * 2, 20)
        
        sentences = text.count('.') + text.count('!') + text.count('?')
        if sentences > 5:
            score += 10
        
        strange_chars = len([c for c in text if ord(c) > 255])
        score -= min(strange_chars, 20)
        
        return min(100.0, max(0.0, score))
    
    def _demo_ocr(self, image_data: bytes, language: str = 'fr') -> Dict:
        """Mode démo quand l'API NVIDIA n'est pas configurée"""
        return {
            'text': '[Mode Démo] Configurez NVIDIA_API_KEY pour utiliser Nemotron OCR',
            'confidence': 0,
            'success': False,
            'error': 'Clé API non configurée',
            'language_detected': language,
            'note': 'Mode démo - Configurez NVIDIA_API_KEY pour des performances optimales'
        }
    
    def health_check(self) -> Dict:
        """Vérifier l'état du service OCR"""
        try:
            if not self.is_configured():
                return {
                    'status': 'not_configured',
                    'message': 'NVIDIA_API_KEY non configurée',
                    'model': None,
                    'supported_formats': self.supported_formats
                }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=test_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'message': 'NVIDIA Nemotron opérationnel',
                    'model': self.model_name,
                    'supported_formats': self.supported_formats,
                    'api_response_time': response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
                }
            else:
                return {
                    'status': 'error',
                    'message': f'API Error: {response.status_code}',
                    'error': response.text[:200]
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erreur de connexion: {str(e)}'
            }

# Instance globale
nvidia_ocr_service = NVIDIAOCRService()
