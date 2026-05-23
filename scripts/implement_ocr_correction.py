#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def implement_ocr_correction_system():
    """Implémenter le système de correction IA avec OCR et corrigés types"""
    print("🔧 IMPLÉMENTATION SYSTÈME DE CORRECTION IA AVEC OCR")
    print("=" * 60)
    
    try:
        # 1. Créer le service de correction OCR
        print("📝 Création du service de correction OCR...")
        
        ocr_service_code = '''import os
import base64
import json
import logging
from typing import List, Dict, Optional, Tuple
from PIL import Image
import pytesseract
import pdf2image
import io
from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

class OCRCorrectionService:
    """Service de correction IA avec OCR et comparaison aux corrigés types"""
    
    def __init__(self):
        self.tesseract_config = r'--oem 3 --psm 6 -l fra'
        self.min_confidence = 60
        
    def extract_text_from_image(self, image_path: str) -> Dict:
        """Extraire le texte d'une image avec OCR"""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            confidence = pytesseract.image_to_string(image, output_type=pytesseract.Output.DICT)
            
            return {
                'text': text.strip(),
                'confidence': confidence.get('conf', 0),
                'success': True
            }
        except Exception as e:
            logger.error(f"Erreur OCR image {image_path}: {e}")
            return {'text': '', 'confidence': 0, 'success': False, 'error': str(e)}
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict:
        """Extraire le texte d'un PDF avec OCR"""
        try:
            images = pdf2image.convert_from_path(pdf_path)
            all_text = []
            total_confidence = 0
            
            for image in images:
                text = pytesseract.image_to_string(image, config=self.tesseract_config)
                confidence = pytesseract.image_to_string(image, output_type=pytesseract.Output.DICT)
                
                all_text.append(text.strip())
                total_confidence += confidence.get('conf', 0)
            
            full_text = '\\n'.join(all_text)
            avg_confidence = total_confidence / len(images) if images else 0
            
            return {
                'text': full_text,
                'confidence': avg_confidence,
                'pages': len(images),
                'success': True
            }
        except Exception as e:
            logger.error(f"Erreur OCR PDF {pdf_path}: {e}")
            return {'text': '', 'confidence': 0, 'success': False, 'error': str(e)}
    
    def extract_text_from_file(self, file_obj) -> Dict:
        """Extraire le texte d'un fichier uploadé"""
        try:
            # Sauvegarder temporairement le fichier
            temp_path = f"/tmp/exam_copy_{file_obj.name}"
            
            with open(temp_path, 'wb') as f:
                for chunk in file_obj.chunks():
                    f.write(chunk)
            
            # Déterminer le type de fichier
            if file_obj.content_type == 'application/pdf':
                result = self.extract_text_from_pdf(temp_path)
            elif file_obj.content_type.startswith('image/'):
                result = self.extract_text_from_image(temp_path)
            else:
                result = {'text': '', 'confidence': 0, 'success': False, 'error': 'Type de fichier non supporté'}
            
            # Nettoyer le fichier temporaire
            os.remove(temp_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur extraction fichier: {e}")
            return {'text': '', 'confidence': 0, 'success': False, 'error': str(e)}
    
    def compare_with_correction_type(self, student_text: str, correction_text: str) -> Dict:
        """Comparer la copie élève avec le corrigé type"""
        try:
            # Nettoyer les textes
            student_clean = self.clean_text(student_text)
            correction_clean = self.clean_text(correction_text)
            
            # Extraire les mots-clés du corrigé
            correction_keywords = self.extract_keywords(correction_clean)
            student_keywords = self.extract_keywords(student_clean)
            
            # Calculer les scores
            keyword_score = self.calculate_keyword_score(student_keywords, correction_keywords)
            structure_score = self.calculate_structure_score(student_clean, correction_clean)
            completeness_score = self.calculate_completeness_score(student_clean, correction_clean)
            
            # Score global
            total_score = (keyword_score * 0.4 + structure_score * 0.3 + completeness_score * 0.3)
            note = min(20, max(0, total_score * 20))  # Convertir en note sur 20
            
            return {
                'note': round(note, 2),
                'keyword_score': keyword_score,
                'structure_score': structure_score,
                'completeness_score': completeness_score,
                'missing_keywords': [kw for kw in correction_keywords if kw not in student_keywords],
                'extra_keywords': [kw for kw in student_keywords if kw not in correction_keywords],
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Erreur comparaison: {e}")
            return {'note': 0, 'success': False, 'error': str(e)}
    
    def clean_text(self, text: str) -> str:
        """Nettoyer le texte pour l'analyse"""
        import re
        # Supprimer la ponctuation excessive
        text = re.sub(r'[^\w\sàáâãäåçèéêëìíîïñòóôõöùúûüýÿ]', ' ', text.lower())
        # Supprimer les espaces multiples
        text = re.sub(r'\\s+', ' ', text)
        return text.strip()
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extraire les mots-clés importants"""
        # Mots à ignorer
        stop_words = {'le', 'la', 'les', 'de', 'du', 'des', 'et', 'est', 'sont', 'dans', 'pour', 'avec', 
                     'par', 'sur', 'une', 'un', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'ce', 'se',
                     'ne', 'ni', 'ou', 'où', 'que', 'qui', 'quoi', 'dont', 'mais', 'ou', 'donc', 'car'}
        
        words = [w for w in text.split() if len(w) > 3 and w not in stop_words]
        # Garder les mots uniques
        return list(set(words))
    
    def calculate_keyword_score(self, student_keywords: List[str], correction_keywords: List[str]) -> float:
        """Calculer le score basé sur les mots-clés"""
        if not correction_keywords:
            return 0.0
        
        matching_keywords = set(student_keywords) & set(correction_keywords)
        return len(matching_keywords) / len(correction_keywords)
    
    def calculate_structure_score(self, student_text: str, correction_text: str) -> float:
        """Calculer le score basé sur la structure"""
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
    
    def calculate_completeness_score(self, student_text: str, correction_text: str) -> float:
        """Calculer le score de complétude"""
        student_words = len(student_text.split())
        correction_words = len(correction_text.split())
        
        if correction_words == 0:
            return 0.0
        
        return min(1.0, student_words / correction_words)
    
    def correct_student_copy(self, session, files, text_response="") -> Dict:
        """Corriger la copie d'un élève"""
        try:
            # Récupérer le corrigé type
            from exams.models import ExamFile
            correction_file = ExamFile.objects.filter(
                exam=session.exam, 
                type_fichier='corrige_type'
            ).first()
            
            if not correction_file:
                return {'note': 0, 'success': False, 'error': 'Aucun corrigé type trouvé'}
            
            # Extraire le texte du corrigé type
            correction_text = self.extract_text_from_file(correction_file.fichier)
            if not correction_text['success']:
                return {'note': 0, 'success': False, 'error': 'Impossible de lire le corrigé type'}
            
            # Extraire le texte de la copie élève
            student_text = text_response
            
            # Traiter les fichiers uploadés
            for file_obj in files:
                file_result = self.extract_text_from_file(file_obj)
                if file_result['success']:
                    student_text += '\\n' + file_result['text']
            
            if not student_text.strip():
                return {'note': 0, 'success': False, 'error': 'Aucun texte trouvé dans la copie'}
            
            # Comparer avec le corrigé
            result = self.compare_with_correction_type(student_text, correction_text['text'])
            
            # Ajouter les détails de la correction
            result.update({
                'student_text_length': len(student_text),
                'correction_text_length': len(correction_text['text']),
                'files_processed': len(files),
                'ocr_confidence': correction_text.get('confidence', 0)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur correction copie: {e}")
            return {'note': 0, 'success': False, 'error': str(e)}
'''
        
        # Écrire le service OCR
        with open('ai_engine/ocr_correction.py', 'w', encoding='utf-8') as f:
            f.write(ocr_service_code)
        
        print("✅ Service OCR créé: ai_engine/ocr_correction.py")
        
        # 2. Mettre à jour la vue de soumission pour utiliser l'OCR
        print("\\n📝 Mise à jour de la vue de soumission...")
        
        # Lire la vue existante
        with open('compositions/views.py', 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        # Ajouter l'import et la logique OCR
        if 'from ai_engine.ocr_correction import OCRCorrectionService' not in current_content:
            new_import = '''from ai_engine.ocr_correction import OCRCorrectionService'''
            updated_content = current_content.replace(
                'from ai_engine.multi_ai import multi_ai',
                'from ai_engine.multi_ai import multi_ai\\nfrom ai_engine.ocr_correction import OCRCorrectionService'
            )
            
            # Mettre à jour la fonction submit_paper_view
            updated_content = updated_content.replace(
                '''# Correction IA asynchrone via Redis
        from .tasks import process_ia_correction
        process_ia_correction.delay(str(session.id))''',
                '''# Correction IA avec OCR immédiate
        ocr_service = OCRCorrectionService()
        correction_result = ocr_service.correct_student_copy(session, uploaded_files, reponse_texte)
        
        if correction_result['success']:
            # Créer le résultat
            from compositions.models import Resultat
            resultat = Resultat.objects.create(
                session=session,
                note=correction_result['note'],
                corrige_par_ia=True,
                feedback_ia=correction_result,
                created_at=timezone.now()
            )
            
            # Générer le bulletin automatiquement
            try:
                from bulletins.services import BulletinService
                bulletin_service = BulletinService()
                bulletin_service.generate_bulletin_for_student(session.eleve, session.exam.matiere)
                messages.success(request, "Votre copie a été corrigée par IA et votre bulletin généré.")
            except Exception as e:
                logger.warning(f"Erreur génération bulletin: {e}")
                messages.success(request, f"Votre copie a été corrigée par IA. Note: {correction_result['note']}/20")
        else:
            messages.error(request, f"Erreur lors de la correction: {correction_result.get('error', 'Erreur inconnue')}")'''
            )
            
            # Écrire le fichier mis à jour
            with open('compositions/views.py', 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("✅ Vue submit_paper_view mise à jour avec OCR")
        
        # 3. Ajouter les dépendances OCR
        print("\\n📦 Ajout des dépendances OCR...")
        
        dependencies = '''
# OCR et traitement d'images
pytesseract==0.3.10
pdf2image==1.16.3
Pillow==10.0.0
# Pour l'installation de Tesseract sur le système:
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-fra
# macOS: brew install tesseract tesseract-lang
'''
        
        with open('requirements.txt', 'a', encoding='utf-8') as f:
            f.write(dependencies)
        
        print("✅ Dépendances OCR ajoutées à requirements.txt")
        
        # 4. Créer une tâche de correction asynchrone
        print("\\n⚙️ Création de la tâche de correction asynchrone...")
        
        tasks_code = '''import logging
from celery import shared_task
from django.utils import timezone
from .ocr_correction import OCRCorrectionService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_ia_correction_with_ocr(self, session_id):
    """Tâche asynchrone de correction IA avec OCR"""
    try:
        from compositions.models import CompositionSession, StudentSubmissionFile, Resultat
        
        session = CompositionSession.objects.get(id=session_id)
        
        # Récupérer les fichiers soumis
        files = StudentSubmissionFile.objects.filter(session=session)
        uploaded_files = [file.fichier for file in files]
        
        # Récupérer la réponse texte
        text_response = ""
        try:
            from compositions.models import StudentAnswer
            answer = StudentAnswer.objects.filter(session=session).first()
            if answer:
                text_response = answer.content
        except:
            pass
        
        # Correction OCR
        ocr_service = OCRCorrectionService()
        correction_result = ocr_service.correct_student_copy(session, uploaded_files, text_response)
        
        if correction_result['success']:
            # Créer ou mettre à jour le résultat
            resultat, created = Resultat.objects.get_or_create(
                session=session,
                defaults={
                    'note': correction_result['note'],
                    'corrige_par_ia': True,
                    'feedback_ia': correction_result,
                    'created_at': timezone.now()
                }
            )
            
            if not created:
                resultat.note = correction_result['note']
                resultat.feedback_ia = correction_result
                resultat.corrige_par_ia = True
                resultat.save()
            
            # Générer le bulletin
            try:
                from bulletins.services import BulletinService
                bulletin_service = BulletinService()
                bulletin_service.generate_bulletin_for_student(session.eleve, session.exam.matiere)
                logger.info(f"Bulletin généré pour {session.eleve.email}")
            except Exception as e:
                logger.warning(f"Erreur génération bulletin: {e}")
            
            logger.info(f"Correction OCR réussie pour session {session_id}: {correction_result['note']}/20")
            return {'success': True, 'note': correction_result['note']}
        else:
            logger.error(f"Erreur correction OCR session {session_id}: {correction_result.get('error')}")
            return {'success': False, 'error': correction_result.get('error')}
            
    except Exception as e:
        logger.error(f"Erreur tâche correction OCR {session_id}: {e}")
        if self.request.retries < self.max_retries:
            return self.retry(countdown=60 * (self.request.retries + 1))
        return {'success': False, 'error': str(e)}
'''
        
        with open('compositions/tasks.py', 'w', encoding='utf-8') as f:
            f.write(tasks_code)
        
        print("✅ Tâche asynchrone créée: compositions/tasks.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur implémentation OCR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = implement_ocr_correction_system()
    if success:
        print("\\n🎉 SYSTÈME DE CORRECTION IA AVEC OCR IMPLEMENTÉ!")
        print("\\n📋 ÉTAPES SUIVANTES:")
        print("1. Installer Tesseract OCR sur votre système")
        print("2. Installer les dépendances: pip install -r requirements.txt")
        print("3. Redémarrer le serveur Django")
        print("4. Tester avec une copie scannée")
    else:
        print("\\n❌ ÉCHEC DE L'IMPLÉMENTATION")
