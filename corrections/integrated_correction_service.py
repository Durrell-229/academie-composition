# Service de correction intégré avec barèmes IA et bulletins automatiques
from ai_engine.enhanced_multi_ai import multi_ai
from ai_engine.nvidia_ocr import nvidia_ocr_service
from corrections.baremes_service import baremes_service

import logging

logger = logging.getLogger(__name__)

class IntegratedCorrectionService:
    """Service de correction intégré: OCR + Barèmes IA + Bulletins automatiques"""
    
    def __init__(self):
        self.ocr_service = nvidia_ocr_service
        self.baremes_service = baremes_service
        self.bulletin_generator = None  # bulletins supprimé
        self.min_confidence = 70
    
    def correct_student_copy(self, session, files, text_response="") -> dict:
        """Correction complète avec OCR, barèmes IA et génération bulletin"""
        try:
            # 1. Extraire le texte avec NVIDIA Nemotron OCR
            logger.info(f"Étape 1: OCR avec Nemotron pour session {session.id}")
            ocr_result = self._extract_text(session, files, text_response)
            
            if not ocr_result['success']:
                return {
                    'note': 0,
                    'success': False,
                    'error': 'Erreur extraction texte',
                    'details': ocr_result
                }
            
            # 2. Récupérer ou générer le barème IA
            logger.info(f"Étape 2: Génération barème IA")
            bareme = self.baremes_service.get_bareme_for_exam(session.exam)
            
            # 3. Corriger selon le barème IA
            logger.info(f"Étape 3: Correction selon barème IA")
            correction_result = self.baremes_service.evaluate_with_bareme(
                ocr_result['student_text'],
                ocr_result['correction_text'],
                bareme
            )
            
            # 4. Enrichir avec détails OCR
            correction_result.update({
                'ocr_confidence': ocr_result.get('avg_ocr_confidence', 0),
                'files_processed': ocr_result.get('files_processed', 0),
                'ocr_service_used': 'NVIDIA Nemotron',
                'bareme_utilise': bareme.get('titre', 'Barème par défaut'),
                'student_text_length': len(ocr_result['student_text'])
            })
            
            # 5. Sauvegarder le résultat
            self._save_correction_result(session, correction_result, bareme)
            
            return {
                'note': correction_result.get('note_totale', 0),
                'success': True,
                'correction': correction_result,
                'message': 'Correction effectuée avec succès'
            }
            
        except Exception as e:
            logger.error(f"Erreur correction intégrée: {e}")
            return {
                'note': 0,
                'success': False,
                'error': str(e)
            }
    
    def _extract_text(self, session, files, text_response="") -> dict:
        """Extraire le texte avec OCR Nemotron"""
        try:
            # Récupérer le corrigé type
            from exams.models import ExamFile
            correction_file = ExamFile.objects.filter(
                exam=session.exam, 
                type_fichier='corrige_type'
            ).first()
            
            if not correction_file:
                return {
                    'success': False,
                    'error': 'Aucun corrigé type trouvé'
                }
            
            # Extraire le texte du corrigé
            correction_result = self.ocr_service.extract_text_from_file(
                correction_file.fichier, 
                language='fr'
            )
            
            if not correction_result['success']:
                return {
                    'success': False,
                    'error': 'Impossible de lire le corrigé type'
                }
            
            # Extraire le texte de la copie élève
            student_text = text_response
            ocr_results = []
            
            for file_obj in files:
                try:
                    file_result = self.ocr_service.extract_text_from_file(
                        file_obj, 
                        language='fr'
                    )
                    
                    if file_result['success'] and file_result['confidence'] >= self.min_confidence:
                        student_text += '\n\n' + file_result['text']
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
                    'error': 'Aucun texte trouvé dans la copie'
                }
            
            return {
                'success': True,
                'student_text': student_text,
                'correction_text': correction_result['text'],
                'ocr_results': ocr_results,
                'avg_ocr_confidence': sum(r['confidence'] for r in ocr_results) / len(ocr_results) if ocr_results else 0,
                'files_processed': len(files)
            }
            
        except Exception as e:
            logger.error(f"Erreur extraction texte: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_correction_result(self, session, correction_result, bareme):
        """Sauvegarder le résultat de correction"""
        try:
            from corrections.models import CorrectionResult
            
            # Créer ou mettre à jour le résultat
            correction, created = CorrectionResult.objects.update_or_create(
                session=session,
                defaults={
                    'note': correction_result.get('note_totale', 0),
                    'details_correction': correction_result,
                    'bareme_utilise': bareme,
                    'date_correction': timezone.now()
                }
            )
            
            logger.info(f"Résultat correction sauvegardé: {correction.id}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde correction: {e}")

# Instance globale
integrated_correction_service = IntegratedCorrectionService()
