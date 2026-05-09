# Ajout de NVIDIA OCR au service multi-IA existant
from .nvidia_ocr import nvidia_ocr_service
from .multi_ai import MultiAIService

class EnhancedMultiAIService(MultiAIService):
    """Service multi-IA avec NVIDIA OCR intégré"""
    
    def __init__(self):
        super().__init__()
        self.ocr_service = nvidia_ocr_service
    
    def ocr_extract_text(self, file_obj, language: str = 'fr') -> dict:
        """Extraire le texte avec NVIDIA OCR"""
        return self.ocr_service.extract_text_from_file(file_obj, language)
    
    def ocr_extract_text_from_image(self, image_path: str, language: str = 'fr') -> dict:
        """Extraire le texte d'une image avec NVIDIA OCR"""
        return self.ocr_service.extract_text_from_image(image_path, language)
    
    def ocr_extract_text_from_pdf(self, pdf_path: str, language: str = 'fr') -> dict:
        """Extraire le texte d'un PDF avec NVIDIA OCR"""
        return self.ocr_service.extract_text_from_pdf(pdf_path, language)
    
    def ocr_batch_process(self, files, language: str = 'fr') -> list:
        """Traiter plusieurs fichiers avec OCR"""
        return self.ocr_service.batch_process_files(files, language)
    
    def ocr_health_check(self) -> dict:
        """Vérifier l'état du service OCR"""
        return self.ocr_service.health_check()

# Mettre à jour l'instance globale
multi_ai = EnhancedMultiAIService()
