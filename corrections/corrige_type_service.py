import logging
import json
from typing import Dict, List, Optional
from django.conf import settings
from django.core.cache import cache
from ai_engine.nvidia_ocr import nvidia_ocr_service

logger = logging.getLogger(__name__)

class CorrigeTypeService:
    """
    Service de gestion des corrigés types uploadés par les professeurs
    Garantit la séparation stricte entre corrigés types et copies élèves
    """
    
    def __init__(self):
        self.ocr_service = nvidia_ocr_service
        self.cache_timeout = 3600  # 1 heure
    
    def extract_corrige_type(self, exam) -> Dict:
        """Extraire et analyser le corrigé type uploadé pour un examen"""
        try:
            from exams.models import ExamFile
            
            # Récupérer le corrigé type de l'examen (UNIQUE par examen)
            corrige_file = ExamFile.objects.filter(
                exam=exam,
                type_fichier='corrige_type'
            ).first()
            
            if not corrige_file:
                return {
                    'success': False,
                    'error': 'Aucun corrigé type trouvé pour cet examen',
                    'exam_id': exam.id
                }
            
            logger.info(f"Extraction corrigé type pour examen {exam.id}")
            
            # Vérifier si déjà en cache
            cache_key = f'corrige_type_{exam.id}'
            cached_corrige = cache.get(cache_key)
            
            if cached_corrige:
                logger.info(f"Corrigé type trouvé en cache pour examen {exam.id}")
                return cached_corrige
            
            # Extraire le texte avec OCR Nemotron
            ocr_result = self.ocr_service.extract_text_from_file(
                corrige_file.fichier,
                language='fr'
            )
            
            if not ocr_result['success']:
                return {
                    'success': False,
                    'error': 'Erreur extraction OCR du corrigé type',
                    'exam_id': exam.id
                }
            
            # Analyser le corrigé type pour extraire le barème
            bareme = self._extract_bareme_from_corrige(ocr_result['text'])
            
            # Créer le corrigé type complet
            corrige_data = {
                'success': True,
                'exam_id': exam.id,
                'exam_titre': exam.titre,
                'corrige_text': ocr_result['text'],
                'bareme': bareme,
                'ocr_confidence': ocr_result.get('confidence', 0),
                'fichier_corrige': corrige_file.fichier.name,
                'date_extraction': timezone.now().isoformat(),
                'professeur': exam.createur.email if exam.createur else 'Unknown'
            }
            
            # Mettre en cache
            cache.set(cache_key, corrige_data, self.cache_timeout)
            
            logger.info(f"Corrigé type extrait et mis en cache pour examen {exam.id}")
            return corrige_data
            
        except Exception as e:
            logger.error(f"Erreur extraction corrigé type: {e}")
            return {
                'success': False,
                'error': str(e),
                'exam_id': exam.id
            }
    
    def _extract_bareme_from_corrige(self, corrige_text: str) -> Dict:
        """Extraire le barème depuis le texte du corrigé type"""
        try:
            # Utiliser l'IA pour analyser et extraire le barème
            from ai_engine.enhanced_multi_ai import multi_ai
            
            prompt = f"""Analyse ce corrigé type et extrait le barème de correction:

{corrige_text[:3000]}

Retourne UNIQUEMENT un JSON avec cette structure exacte:
{{
    "total_points": 20,
    "critères": [
        {{
            "nom": "Nom du critère",
            "points": 5,
            "description": "Description détaillée",
            "indicateurs": ["Indicateur 1", "Indicateur 2"],
            "ponderation": 0.25
        }}
    ],
    "instructions_correction": "Instructions spécifiques pour la correction"
}}

Si aucun barème n'est explicitement mentionné, retourne un barème par défaut équilibré."""
            
            response = multi_ai.generate(prompt)
            
            try:
                bareme = json.loads(response)
                return self._validate_bareme(bareme)
            except json.JSONDecodeError:
                # Barème par défaut si extraction échoue
                return self._get_default_bareme()
                
        except Exception as e:
            logger.error(f"Erreur extraction barème: {e}")
            return self._get_default_bareme()
    
    def _validate_bareme(self, bareme: Dict) -> Dict:
        """Valider et normaliser le barème extrait"""
        # S'assurer que le total est 20
        if 'total_points' not in bareme or bareme['total_points'] != 20:
            bareme['total_points'] = 20
        
        # Normaliser les pondérations
        if 'critères' in bareme:
            total_ponderation = sum(c.get('ponderation', 0) for c in bareme['critères'])
            if total_ponderation != 1.0 and total_ponderation > 0:
                for critere in bareme['critères']:
                    critere['ponderation'] = critere.get('ponderation', 0) / total_ponderation
        
        # Ajouter les champs manquants
        if 'instructions_correction' not in bareme:
            bareme['instructions_correction'] = "Corriger selon le barème standard"
        
        return bareme
    
    def _get_default_bareme(self) -> Dict:
        """Barème par défaut si extraction échoue"""
        return {
            'total_points': 20,
            'critères': [
                {
                    'nom': 'Compréhension du sujet',
                    'points': 4,
                    'description': 'Capacité à comprendre et restituer les concepts',
                    'indicateurs': ['Définitions', 'Mise en contexte', 'Explication'],
                    'ponderation': 0.20
                },
                {
                    'nom': 'Structure et organisation',
                    'points': 4,
                    'description': 'Organisation logique de la réponse',
                    'indicateurs': ['Introduction', 'Développement', 'Conclusion'],
                    'ponderation': 0.20
                },
                {
                    'nom': 'Précision et exactitude',
                    'points': 5,
                    'description': 'Exactitude des informations',
                    'indicateurs': ['Données correctes', 'Calculs justes', 'Références'],
                    'ponderation': 0.25
                },
                {
                    'nom': 'Méthodologie',
                    'points': 4,
                    'description': 'Qualité du raisonnement',
                    'indicateurs': ['Logique', 'Étapes', 'Justifications'],
                    'ponderation': 0.20
                },
                {
                    'nom': 'Présentation',
                    'points': 3,
                    'description': "Qualité de l'expression",
                    'indicateurs': ['Orthographe', 'Grammaire', 'Lisibilité'],
                    'ponderation': 0.15
                }
            ],
            'instructions_correction': 'Corriger selon le barème standard'
        }
    
    def get_corrige_type_for_correction(self, session) -> Dict:
        """Récupérer le corrigé type pour une session de composition"""
        try:
            # Validation stricte : s'assurer que le corrigé type correspond à l'examen
            if not session.exam:
                return {
                    'success': False,
                    'error': 'Aucun examen associé à cette session'
                }
            
            # Récupérer le corrigé type
            corrige = self.extract_corrige_type(session.exam)
            
            if not corrige['success']:
                return corrige
            
            # Validation supplémentaire : éviter les mélanges
            validation = self._validate_no_mixing(session, corrige)
            
            if not validation['valid']:
                return {
                    'success': False,
                    'error': f'Erreur de validation: {validation["error"]}',
                    'exam_id': session.exam.id
                }
            
            return corrige
            
        except Exception as e:
            logger.error(f"Erreur récupération corrigé type: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_no_mixing(self, session, corrige: Dict) -> Dict:
        """Valider qu'il n'y a pas de mélange entre corrigés types et copies"""
        try:
            # Vérifier que l'ID de l'examen correspond
            if corrige['exam_id'] != session.exam.id:
                return {
                    'valid': False,
                    'error': f'Mismatch exam ID: {corrige["exam_id"]} != {session.exam.id}'
                }
            
            # Vérifier que le corrigé n'est pas une copie élève
            if 'eleve' in corrige and corrige['eleve']:
                return {
                    'valid': False,
                    'error': 'Corrigé type contient des données élève'
                }
            
            # Vérifier la cohérence du texte
            if len(corrige['corrige_text']) < 50:
                return {
                    'valid': False,
                    'error': 'Corrigé type trop court'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Erreur validation no-mixing: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def invalidate_cache(self, exam_id):
        """Invalider le cache d'un corrigé type"""
        cache_key = f'corrige_type_{exam_id}'
        cache.delete(cache_key)
        logger.info(f"Cache invalidé pour examen {exam_id}")

# Instance globale
corrige_type_service = CorrigeTypeService()
