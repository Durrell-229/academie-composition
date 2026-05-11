"""
Service de surveillance d'examen par IA Nemotron - VERSION PRODUCTION
Surveillance réelle avec banissement intelligent (ni trop strict, ni trop laxiste)
"""
import os
import json
import base64
import logging
import requests
from typing import Dict, List, Optional
from PIL import Image
import io
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class NemotronProctorService:
    """
    Surveillance d'examen par IA Nemotron - Version PRODUCTION
    - Surveillance active et réelle
    - Banissement intelligent (5 violations graves ou 10 légères)
    - Rapports détaillés pour les professeurs
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'NVIDIA_API_KEY', os.getenv('NVIDIA_API_KEY', ''))
        self.base_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.model_name = "nvidia/nemotron-4-340b-instruct"
        self.max_file_size = 5 * 1024 * 1024
        
        # Seuils de banissement (configurables)
        self.BAN_THRESHOLD_HIGH = 3   # 3 violations HIGH = ban
        self.BAN_THRESHOLD_LOW = 8   # 8 violations LOW = ban
        self.WARNING_THRESHOLD = 2   # 2 violations = avertissement
        
        if not self.api_key:
            logger.warning("⚠️ NVIDIA_API_KEY non configurée. Surveillance IA désactivée.")
        else:
            logger.info(f"✅ Nemotron Proctor configuré (clé: {self.api_key[:20]}...)")
    
    def is_configured(self) -> bool:
        """Vérifier si le service est configuré"""
        return bool(self.api_key)
    
    def analyze_screenshot(self, image_data: bytes, session_id: str = '', 
                          current_violations: int = 0) -> Dict:
        """
        Analyser une capture d'écran et décider si banissement nécessaire
        """
        if not self.is_configured():
            logger.warning("Nemotron non configuré - mode démo")
            return self._demo_analysis(current_violations)
        
        try:
            # Compresser l'image
            compressed_image = self._compress_image(image_data)
            image_base64 = base64.b64encode(compressed_image).decode('utf-8')
            
            # Prompt optimisé pour Nemotron
            prompt = """Analyse cette capture d'écran d'un examen en ligne. Sois strict mais juste.

RÈGLES DE DÉTECTION:
1. Visages: Compte les personnes (1=normal, 2+=suspect, 0=absent)
2. Téléphone: Détecte tout téléphone, tablette, appareil électronique
3. Documents: Notes papier, livres ouverts = NON AUTORISÉ
4. Comportement: Regard ailleurs, gestes suspects

CLASSIFICATION RISQUE:
- LOW: Rien d'anormal, élève concentré
- MEDIUM: Anomalie mineure (regard ailleurs, mouvement)
- HIGH: Triche probable (téléphone, documents, 2+ personnes)
- CRITICAL: Triche évidente (téléphone en main, copie ouverte)

FORMAT JSON OBLIGATOIRE:
{
    "persons_detected": 1,
    "phone_detected": false,
    "documents_detected": false,
    "looking_at_screen": true,
    "suspicious_behavior": false,
    "risk_level": "low/medium/high/critical",
    "confidence": 85,
    "details": "Description précise de ce que tu vois",
    "should_warn": false,
    "should_ban": false
}"""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "Tu es un surveillant d'examen IA strict mais juste. Réponds UNIQUEMENT en JSON valide."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 400
            }
            
            logger.info(f"📤 Envoi analyse Nemotron pour session {session_id[:8]}...")
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result['choices'][0]['message']['content']
                
                # Parser le JSON
                analysis = self._parse_json_response(analysis_text)
                
                # Déterminer l'action
                action = self._determine_action(analysis, current_violations)
                
                logger.info(f"✅ Analyse Nemotron: {analysis.get('risk_level')} - {action}")
                
                return {
                    'success': True,
                    'analysis': analysis,
                    'action': action,
                    'timestamp': timezone.now().isoformat(),
                    'session_id': session_id,
                    'model_used': self.model_name,
                    'violations_count': current_violations + (1 if analysis.get('risk_level') in ['high', 'critical'] else 
                                                           0.5 if analysis.get('risk_level') == 'medium' else 0)
                }
            else:
                logger.error(f"❌ Erreur API Nemotron: {response.status_code}")
                return self._demo_analysis(current_violations)
                
        except Exception as e:
            logger.error(f"❌ Erreur analyse Nemotron: {e}")
            return self._demo_analysis(current_violations)
    
    def _parse_json_response(self, text: str) -> Dict:
        """Parser la réponse JSON de Nemotron"""
        try:
            # Chercher le JSON dans la réponse
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = text[json_start:json_end]
                return json.loads(json_str)
            
            # Fallback: parser le texte
            return self._parse_text_response(text)
            
        except json.JSONDecodeError:
            return self._parse_text_response(text)
    
    def _parse_text_response(self, text: str) -> Dict:
        """Parser une réponse textuelle"""
        text_lower = text.lower()
        
        # Détection des mots-clés
        risk_level = 'low'
        if 'critical' in text_lower or 'crítico' in text_lower:
            risk_level = 'critical'
        elif 'high' in text_lower or 'élevé' in text_lower or 'alto' in text_lower:
            risk_level = 'high'
        elif 'medium' in text_lower or 'moyen' in text_lower:
            risk_level = 'medium'
        
        return {
            'persons_detected': 2 if '2 personnes' in text_lower or 'deux personnes' in text_lower else 
                               0 if 'aucune personne' in text_lower or '0 personne' in text_lower else 1,
            'phone_detected': 'téléphone' in text_lower or 'phone' in text_lower or 'portable' in text_lower,
            'documents_detected': 'document' in text_lower and ('non autorisé' in text_lower or 'interdit' in text_lower),
            'looking_at_screen': 'regarde l\'écran' in text_lower or 'écran' in text_lower,
            'suspicious_behavior': 'suspect' in text_lower or 'comportement' in text_lower,
            'risk_level': risk_level,
            'confidence': 70,
            'details': text[:300],
            'should_warn': risk_level in ['medium', 'high'],
            'should_ban': risk_level == 'critical'
        }
    
    def _determine_action(self, analysis: Dict, current_violations: int) -> str:
        """Déterminer l'action à prendre basée sur l'analyse"""
        risk = analysis.get('risk_level', 'low')
        
        # Calculer le nouveau score de violation
        violation_score = current_violations
        if risk == 'critical':
            violation_score += 2
        elif risk == 'high':
            violation_score += 1
        elif risk == 'medium':
            violation_score += 0.5
        
        # Décision intelligente
        if violation_score >= self.BAN_THRESHOLD_HIGH and risk in ['high', 'critical']:
            return 'BAN'
        elif violation_score >= self.BAN_THRESHOLD_LOW:
            return 'BAN'
        elif violation_score >= self.WARNING_THRESHOLD:
            return 'WARN'
        else:
            return 'MONITOR'
    
    def _compress_image(self, image_data: bytes, max_size: int = 800) -> bytes:
        """Compresser l'image pour l'API"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Redimensionner
            width, height = image.size
            if width > max_size or height > max_size:
                ratio = min(max_size / width, max_size / height)
                new_size = (int(width * ratio), int(height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convertir en JPEG
            buffer = io.BytesIO()
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            image.save(buffer, format='JPEG', quality=75, optimize=True)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erreur compression: {e}")
            return image_data
    
    def _demo_analysis(self, current_violations: int) -> Dict:
        """Mode démo"""
        return {
            'success': False,
            'demo_mode': True,
            'analysis': {
                'persons_detected': 1,
                'phone_detected': False,
                'documents_detected': False,
                'looking_at_screen': True,
                'suspicious_behavior': False,
                'risk_level': 'low',
                'confidence': 0,
                'details': 'Mode démo - Nemotron non configuré',
                'should_warn': False,
                'should_ban': False
            },
            'action': 'MONITOR',
            'violations_count': current_violations,
            'timestamp': timezone.now().isoformat()
        }
    
    def health_check(self) -> Dict:
        """Vérifier l'état du service"""
        if not self.is_configured():
            return {
                'status': 'not_configured',
                'message': 'NVIDIA_API_KEY non configurée'
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5
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
                    'message': '✅ Nemotron opérationnel'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Erreur API: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erreur: {str(e)}'
            }


# Instance globale
nemotron_proctor = NemotronProctorService()
