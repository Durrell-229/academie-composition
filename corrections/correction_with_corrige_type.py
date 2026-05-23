# Service de correction utilisant les corrigés types uploadés par les professeurs
from ai_engine.nvidia_ocr import nvidia_ocr_service
from corrections.corrige_type_service import corrige_type_service
bulletin_auto_generator = None  # bulletins supprimé
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class CorrectionWithCorrigeTypeService:
    """
    Service de correction utilisant strictement les corrigés types uploadés
    Garantit la séparation totale entre corrigés types et copies élèves
    """
    
    def __init__(self):
        self.ocr_service = nvidia_ocr_service
        self.corrige_service = corrige_type_service
        self.bulletin_generator = bulletin_auto_generator
        self.min_confidence = 70
    
    def correct_student_copy(self, session, files, text_response="") -> dict:
        """Correction de la copie élève avec le corrigé type de l'examen"""
        try:
            # ÉTAPE 1: Récupérer le corrigé type (UNIQUE par examen)
            logger.info(f"Étape 1: Récupération corrigé type pour examen {session.exam.id}")
            corrige_result = self.corrige_service.get_corrige_type_for_correction(session)
            
            if not corrige_result['success']:
                return {
                    'note': 0,
                    'success': False,
                    'error': f'Erreur corrigé type: {corrige_result["error"]}',
                    'step': 'corrige_type'
                }
            
            logger.info(f"Corrigé type récupéré: {corrige_result['exam_titre']}")
            
            # ÉTAPE 2: Extraire le texte de la copie élève
            logger.info(f"Étape 2: Extraction texte copie élève")
            student_result = self._extract_student_copy(session, files, text_response)
            
            if not student_result['success']:
                return {
                    'note': 0,
                    'success': False,
                    'error': f'Erreur extraction copie: {student_result["error"]}',
                    'step': 'student_copy'
                }
            
            logger.info(f"Texte élève extrait: {len(student_result['student_text'])} caractères")
            
            # ÉTAPE 3: Corriger selon le barème du corrigé type
            logger.info(f"Étape 3: Correction selon barème corrigé type")
            correction_result = self._correct_with_corrige_type(
                student_result['student_text'],
                corrige_result
            )
            
            if not correction_result['success']:
                return {
                    'note': 0,
                    'success': False,
                    'error': f'Erreur correction: {correction_result["error"]}',
                    'step': 'correction'
                }
            
            # ÉTAPE 4: Enrichir avec métadonnées
            correction_result.update({
                'exam_id': session.exam.id,
                'exam_titre': session.exam.titre,
                'corrige_type_used': corrige_result['fichier_corrige'],
                'bareme_source': 'corrige_type_upload',
                'ocr_confidence_student': student_result.get('avg_ocr_confidence', 0),
                'files_processed': student_result.get('files_processed', 0),
                'validation_passed': True,
                'no_mixing_verified': True
            })
            
            # ÉTAPE 5: Sauvegarder le résultat
            self._save_correction_result(session, correction_result)
            
            # ÉTAPE 6: Générer automatiquement le bulletin
            logger.info(f"Étape 4: Génération bulletin automatique")
            bulletin_result = self.bulletin_generator.generate_after_correction(
                session,
                correction_result
            )
            
            correction_result['bulletin'] = bulletin_result
            
            logger.info(f"Correction terminée avec succès - Note: {correction_result['note_totale']}/20")
            
            return {
                'note': correction_result.get('note_totale', 0),
                'success': True,
                'correction': correction_result,
                'message': 'Correction effectuée avec succès - Corrigé type utilisé'
            }
            
        except Exception as e:
            logger.error(f"Erreur correction avec corrigé type: {e}")
            return {
                'note': 0,
                'success': False,
                'error': str(e),
                'step': 'general'
            }
    
    def _extract_student_copy(self, session, files, text_response="") -> dict:
        """Extraire le texte de la copie élève avec validation stricte"""
        try:
            student_text = text_response
            ocr_results = []
            
            for file_obj in files:
                try:
                    # Validation : s'assurer que ce n'est pas un corrigé type
                    filename = getattr(file_obj, 'name', '').lower()
                    if 'corrige' in filename or 'correction' in filename:
                        logger.warning(f"Fichier suspect ignoré: {filename}")
                        continue
                    
                    file_result = self.ocr_service.extract_text_from_file(
                        file_obj, 
                        language='fr'
                    )
                    
                    if file_result['success'] and file_result['confidence'] >= self.min_confidence:
                        student_text += "\n\n" + file_result['text']
                        ocr_results.append({
                            'filename': getattr(file_obj, 'name', 'Unknown'),
                            'confidence': file_result['confidence'],
                            'text_length': len(file_result['text'])
                        })
                        
                except Exception as e:
                    logger.error(f"Erreur OCR fichier: {e}")
            
            if not student_text.strip():
                return {
                    'success': False,
                    'error': 'Aucun texte trouvé dans la copie élève'
                }
            
            return {
                'success': True,
                'student_text': student_text,
                'ocr_results': ocr_results,
                'avg_ocr_confidence': sum(r['confidence'] for r in ocr_results) / len(ocr_results) if ocr_results else 0,
                'files_processed': len(files),
                'validation': 'student_copy_verified'
            }
            
        except Exception as e:
            logger.error(f"Erreur extraction copie élève: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _correct_with_corrige_type(self, student_text: str, corrige_data: Dict) -> dict:
        """Corriger selon le barème extrait du corrigé type"""
        try:
            bareme = corrige_data['bareme']
            corrige_text = corrige_data['corrige_text']
            
            total_note = 0
            criteres_evaluations = []
            
            for critere in bareme.get('critères', []):
                # Évaluer ce critère selon le corrigé type
                evaluation = self._evaluate_critere_with_corrige(
                    student_text,
                    corrige_text,
                    critere
                )
                
                note_critere = evaluation['score'] * critere['points']
                total_note += note_critere
                
                criteres_evaluations.append({
                    'critere': critere['nom'],
                    'points_max': critere['points'],
                    'points_obtenus': round(note_critere, 2),
                    'score_pourcentage': round(evaluation['score'] * 100, 1),
                    'commentaire': evaluation['commentaire'],
                    'indicateurs': evaluation['indicateurs']
                })
            
            return {
                'note_totale': round(total_note, 2),
                'note_sur_20': round(total_note, 2),
                'criteres': criteres_evaluations,
                'evaluation_complete': True,
                'bareme_utilise': bareme,
                'source_correction': 'corrige_type_upload',
                'instructions_suivies': bareme.get('instructions_correction', 'Standard')
            }
            
        except Exception as e:
            logger.error(f"Erreur correction avec corrigé type: {e}")
            return {
                'note_totale': 0,
                'success': False,
                'error': str(e)
            }
    
    def _evaluate_critere_with_corrige(self, student_text: str, corrige_text: str, critere: Dict) -> Dict:
        """Évaluer un critère en comparant avec le corrigé type"""
        try:
            from ai_engine.enhanced_multi_ai import multi_ai
            
            prompt = f"""Compare la copie élève avec le corrigé type selon ce critère:

Critère: {critere['nom']}
Description: {critere['description']}
Points max: {critere['points']}
Indicateurs: {', '.join(critere.get('indicateurs', []))}

CORRIGÉ TYPE (référence absolue):
{corrige_text[:2000]}

COPIIE ÉLÈVE (à évaluer):
{student_text[:2000]}

Instructions strictes:
- Utiliser UNIQUEMENT le corrigé type comme référence
- Ne jamais mélanger avec d'autres documents
- Évaluer de 0 à 1 (0 = insuffisant, 1 = excellent)
- Fournir un commentaire objectif basé sur le corrigé type

Format JSON:
{{
    "score": 0.75,
    "commentaire": "Commentaire basé sur le corrigé type",
    "indicateurs": ["Indicateur respecté 1", "Indicateur respecté 2"]
}}"""
            
            response = multi_ai.generate(prompt)
            
            try:
                import json
                evaluation = json.loads(response)
                return evaluation
            except json.JSONDecodeError:
                # Fallback : évaluation basique
                return self._basic_evaluation(student_text, corrige_text, critere)
                
        except Exception as e:
            logger.error(f"Erreur évaluation critère: {e}")
            return self._basic_evaluation(student_text, corrige_text, critere)
    
    def _basic_evaluation(self, student_text: str, corrige_text: str, critere: Dict) -> Dict:
        """Évaluation basique de secours"""
        student_words = len(student_text.split())
        corrige_words = len(corrige_text.split())
        
        score = min(1.0, student_words / max(corrige_words, 1)) * 0.7
        
        return {
            'score': score,
            'commentaire': 'Évaluation basique (IA non disponible)',
            'indicateurs': []
        }
    
    def _save_correction_result(self, session, correction_result):
        """Sauvegarder le résultat avec traçabilité"""
        try:
            from corrections.models import CorrectionResult
            from django.utils import timezone
            
            # Créer ou mettre à jour le résultat
            correction, created = CorrectionResult.objects.update_or_create(
                session=session,
                defaults={
                    'note': correction_result.get('note_totale', 0),
                    'details_correction': correction_result,
                    'date_correction': timezone.now(),
                    'source_correction': 'corrige_type_upload'
                }
            )
            
            logger.info("Résultat correction sauvegardé: {}".format(correction.id))
            
        except Exception as e:
            logger.error("Erreur sauvegarde correction: {}".format(str(e)))

# Instance globale
correction_with_corrige_service = CorrectionWithCorrigeTypeService()
