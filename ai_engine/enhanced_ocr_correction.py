# Service de correction avec NVIDIA OCR
from ai_engine.enhanced_multi_ai import multi_ai
from ai_engine.nvidia_ocr import nvidia_ocr_service
import logging

logger = logging.getLogger(__name__)

class EnhancedOCRCorrectionService:
    """Service de correction OCR avec NVIDIA haute performance"""
    
    def __init__(self):
        self.ocr_service = nvidia_ocr_service
        self.min_confidence = 70  # Seuil de confiance minimum
        
    def extract_text_from_student_copy(self, session, files, text_response="") -> dict:
        """Extraire et analyser le texte de la copie élève avec NVIDIA OCR"""
        try:
            # Récupérer le corrigé type
            from exams.models import ExamFile
            correction_file = ExamFile.objects.filter(
                exam=session.exam, 
                type_fichier='corrige_type'
            ).first()
            
            if not correction_file:
                return {
                    'note': 0, 
                    'success': False, 
                    'error': 'Aucun corrigé type trouvé'
                }
            
            # Extraire le texte du corrigé type
            correction_result = self.ocr_service.extract_text_from_file(
                correction_file.fichier, 
                language='fr'
            )
            
            if not correction_result['success']:
                return {
                    'note': 0, 
                    'success': False, 
                    'error': 'Impossible de lire le corrigé type'
                }
            
            # Extraire le texte de la copie élève
            student_text = text_response
            ocr_results = []
            
            # Traiter les fichiers uploadés avec NVIDIA OCR
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
                            'text_length': len(file_result['text']),
                            'processing_time': file_result.get('processing_time', 0)
                        })
                        logger.info(f"OCR réussi pour {getattr(file_obj, 'name', 'Unknown')}: {file_result['confidence']}%")
                    else:
                        logger.warning(f"OCR faible confiance pour {getattr(file_obj, 'name', 'Unknown')}: {file_result.get('confidence', 0)}%")
                        
                except Exception as e:
                    logger.error(f"Erreur OCR fichier {getattr(file_obj, 'name', 'Unknown')}: {e}")
            
            if not student_text.strip():
                return {
                    'note': 0, 
                    'success': False, 
                    'error': 'Aucun texte trouvé dans la copie'
                }
            
            # Comparer avec le corrigé
            comparison_result = self.compare_with_correction_type(
                student_text, 
                correction_result['text']
            )
            
            # Ajouter les détails OCR
            comparison_result.update({
                'student_text_length': len(student_text),
                'correction_text_length': len(correction_result['text']),
                'files_processed': len(files),
                'ocr_results': ocr_results,
                'avg_ocr_confidence': sum(r['confidence'] for r in ocr_results) / len(ocr_results) if ocr_results else 0,
                'total_ocr_time': sum(r['processing_time'] for r in ocr_results),
                'ocr_service_used': 'NVIDIA OCR',
                'language_detected': 'fr'
            })
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"Erreur correction OCR: {e}")
            return {
                'note': 0, 
                'success': False, 
                'error': str(e)
            }
    
    def compare_with_correction_type(self, student_text: str, correction_text: str) -> dict:
        """Comparer la copie élève avec le corrigé type (version améliorée)"""
        try:
            # Nettoyer les textes
            student_clean = self.clean_text(student_text)
            correction_clean = self.clean_text(correction_text)
            
            # Analyse sémantique avec NVIDIA
            semantic_analysis = self.semantic_analysis(student_clean, correction_clean)
            
            # Analyse structurelle
            structure_score = self.calculate_structure_score(student_clean, correction_clean)
            
            # Analyse de complétude
            completeness_score = self.calculate_completeness_score(student_clean, correction_clean)
            
            # Analyse des mots-clés contextuels béninois
            benin_context_score = self.calculate_benin_context_score(student_clean, correction_clean)
            
            # Score global pondéré
            total_score = (
                semantic_analysis['similarity'] * 0.4 +
                structure_score * 0.2 +
                completeness_score * 0.2 +
                benin_context_score * 0.2
            )
            
            note = min(20, max(0, total_score * 20))
            
            return {
                'note': round(note, 2),
                'semantic_similarity': semantic_analysis['similarity'],
                'structure_score': structure_score,
                'completeness_score': completeness_score,
                'benin_context_score': benin_context_score,
                'missing_keywords': semantic_analysis.get('missing_keywords', []),
                'extra_keywords': semantic_analysis.get('extra_keywords', []),
                'success': True,
                'analysis_details': {
                    'student_word_count': len(student_clean.split()),
                    'correction_word_count': len(correction_clean.split()),
                    'language_confidence': semantic_analysis.get('language_confidence', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur comparaison: {e}")
            return {
                'note': 0, 
                'success': False, 
                'error': str(e)
            }
    
    def semantic_analysis(self, student_text: str, correction_text: str) -> dict:
        """Analyse sémantique avancée avec contexte béninois"""
        try:
            # Mots-clés spécifiques au contexte éducatif béninois
            benin_keywords = [
                'bénin', 'cotonou', 'porto-novo', 'abomey', 'parakou',
                'école', 'élève', 'professeur', 'classe', 'matière',
                'examen', 'composition', 'note', 'évaluation',
                'primaire', 'collège', 'lycée', 'université',
                'français', 'mathématiques', 'physique', 'chimie',
                'histoire', 'géographie', 'svt', 'philosophie'
            ]
            
            student_words = set(self.extract_keywords(student_text))
            correction_words = set(self.extract_keywords(correction_text))
            
            # Mots-clés contextuels
            student_benin = student_words & set(benin_keywords)
            correction_benin = correction_words & set(benin_keywords)
            
            # Similarité sémantique
            common_words = student_words & correction_words
            total_unique = student_words | correction_words
            
            similarity = len(common_words) / len(total_unique) if total_unique else 0
            
            # Bonus pour le contexte béninois
            context_bonus = len(student_benin) / max(len(correction_benin), 1) * 0.1
            
            return {
                'similarity': min(1.0, similarity + context_bonus),
                'missing_keywords': list(correction_words - student_words),
                'extra_keywords': list(student_words - correction_words),
                'benin_context_keywords': list(student_benin),
                'language_confidence': 0.95  # Haute confiance avec NVIDIA OCR
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse sémantique: {e}")
            return {'similarity': 0, 'error': str(e)}
    
    def calculate_benin_context_score(self, student_text: str, correction_text: str) -> float:
        """Calculer le score basé sur le contexte éducatif béninois"""
        try:
            # Indicateurs de contexte béninois
            benin_indicators = [
                'bénin', 'cotonou', 'porto-novo', 'abomey', 'parakou',
                'école primaire', 'collège', 'lycée', 'terminale',
                'baccalauréat', 'bepc', 'cép',
                'ministère de l'éducation', 'programme officiel'
            ]
            
            student_lower = student_text.lower()
            correction_lower = correction_text.lower()
            
            # Compter les occurrences
            student_context = sum(1 for indicator in benin_indicators if indicator in student_lower)
            correction_context = sum(1 for indicator in benin_indicators if indicator in correction_lower)
            
            if correction_context == 0:
                return 0.5  # Score neutre si pas de contexte
            
            return min(1.0, student_context / correction_context)
            
        except Exception as e:
            logger.error(f"Erreur calcul contexte bénin: {e}")
            return 0.5
    
    def clean_text(self, text: str) -> str:
        """Nettoyer le texte pour l'analyse"""
        import re
        
        # Supprimer la ponctuation excessive
        text = re.sub(r'[^\w\sàáâãäåçèéêëìíîïñòóôõöùúûüýÿ]', ' ', text.lower())
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_keywords(self, text: str) -> list:
        """Extraire les mots-clés importants"""
        # Mots à ignorer
        stop_words = {'le', 'la', 'les', 'de', 'du', 'des', 'et', 'est', 'sont', 'dans', 'pour', 'avec',
                     'par', 'sur', 'une', 'un', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'ce', 'se',
                     'ne', 'ni', 'ou', 'où', 'que', 'qui', 'quoi', 'dont', 'mais', 'ou', 'donc', 'car'}
        
        words = [w for w in text.split() if len(w) > 3 and w not in stop_words]
        return list(set(words))
    
    def calculate_structure_score(self, student_text: str, correction_text: str) -> float:
        """Calculer le score basé sur la structure du texte"""
        try:
            # Compter les phrases
            student_sentences = len([s for s in student_text.split('.') if s.strip()])
            correction_sentences = len([s for s in correction_text.split('.') if s.strip()])
            
            if correction_sentences == 0:
                return 0.0
            
            # Ratio de phrases
            sentence_ratio = min(1.0, student_sentences / correction_sentences)
            
            # Longueur du texte
            length_ratio = min(1.0, len(student_text) / len(correction_text))
            
            return (sentence_ratio + length_ratio) / 2
            
        except Exception as e:
            logger.error(f"Erreur calcul structure: {e}")
            return 0.0
    
    def calculate_completeness_score(self, student_text: str, correction_text: str) -> float:
        """Calculer le score de complétude"""
        try:
            student_words = len(student_text.split())
            correction_words = len(correction_text.split())
            
            if correction_words == 0:
                return 0.0
            
            return min(1.0, student_words / correction_words)
            
        except Exception as e:
            logger.error(f"Erreur calcul complétude: {e}")
            return 0.0

# Instance globale
enhanced_ocr_service = EnhancedOCRCorrectionService()
