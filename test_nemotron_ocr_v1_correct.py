#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def test_nemotron_ocr_v1_correct():
    """Test du bon endpoint Nemotron OCR v1"""
    print("🧪 TEST NEMOTRON OCR V1 - BON ENDPOINT")
    print("=" * 60)
    
    try:
        import requests
        import base64
        
        api_key = "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"
        invoke_url = "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v1"
        
        print(f"\n🔑 Clé API: {api_key[:20]}...")
        print(f"🌐 Endpoint: {invoke_url}")
        print(f"🤖 Modèle: nvidia/nemotron-ocr-v1")
        
        # Créer une image de test
        print("\n📸 Création image de test...")
        from PIL import Image, ImageDraw, ImageFont
        
        # Créer une image avec du texte
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Ajouter du texte simulant un document éducatif
        text_lines = [
            "EXAMEN DE MATHEMATIQUES - TERMINALE S",
            "Lycée Cotonou - Année 2025-2026",
            "",
            "Exercice 1: Etude de fonction (4 points)",
            "Soit f(x) = x³ - 3x + 2",
            "a) Calcule f'(x)",
            "b) Determine le tableau de variation",
            "c) Deduis les extremums",
            "",
            "Exercice 2: Integration (6 points)",
            "Calcule l'integrale de 0 à pi de sin(x) dx",
            "",
            "Barème: Ex1=4pts, Ex2=6pts, Ex3=10pts"
        ]
        
        y_position = 50
        for line in text_lines:
            draw.text((50, y_position), line, fill='black')
            y_position += 40
        
        # Sauvegarder l'image
        test_image_path = "test_ocr_image.png"
        img.save(test_image_path)
        print(f"✅ Image de test créée: {test_image_path}")
        
        # Encoder l'image en base64
        print("\n🔐 Encodage image en base64...")
        with open(test_image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()
        
        assert len(image_b64) < 180_000, "Image trop grande"
        print(f"✅ Image encodée: {len(image_b64)} caractères")
        
        # Préparer les headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        
        # Préparer le payload
        payload = {
            "input": [
                {
                    "type": "image_url",
                    "url": f"data:image/png;base64,{image_b64}"
                }
            ]
        }
        
        print("\n📤 Envoi de la requête OCR...")
        response = requests.post(invoke_url, headers=headers, json=payload)
        
        print(f"📥 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCÈS! NEMOTRON OCR V1 OPÉRATIONNEL")
            print("\n📊 RÉSULTAT OCR:")
            print(f"   {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Si le résultat contient du texte extrait
            if 'data' in result and len(result['data']) > 0:
                ocr_text = result['data'][0].get('text', '')
                if ocr_text:
                    print(f"\n📝 Texte extrait:")
                    print(f"   {ocr_text}")
            
            # Nettoyer l'image de test
            os.remove(test_image_path)
            
            # Mettre à jour la configuration
            update_nvidia_ocr_config()
            
            return True
        else:
            print(f"\n❌ Erreur: {response.status_code}")
            print(f"Message: {response.text}")
            
            # Nettoyer l'image de test
            if os.path.exists(test_image_path):
                os.remove(test_image_path)
            
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Nettoyer l'image de test
        if os.path.exists("test_ocr_image.png"):
            os.remove("test_ocr_image.png")
        
        return False

def update_nvidia_ocr_config():
    """Mettre à jour la configuration NVIDIA OCR avec le bon endpoint"""
    try:
        with open('ai_engine/nvidia_ocr.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer l'endpoint par le bon endpoint OCR
        content = content.replace(
            'self.base_url = "https://integrate.api.nvidia.com/v1/chat/completions"',
            'self.base_url = "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v1"'
        )
        
        # Remplacer le nom du modèle
        content = content.replace(
            'self.model_name = "meta/llama-3.1-70b-instruct"',
            'self.model_name = "nvidia/nemotron-ocr-v1"'
        )
        
        # Mettre à jour la méthode d'extraction pour utiliser le bon format
        old_extract = '''def extract_text_from_bytes(self, image_data: bytes, language: str = 'fr') -> Dict:
        """Extraire le texte de bytes d'image avec Nemotron"""
        try:
            if not self.is_configured():
                return self._demo_ocr(image_data, language)
            
            processed_image = self.preprocess_image(image_data)
            image_base64 = base64.b64encode(processed_image).decode('utf-8')
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Prompt optimisé pour Nemotron avec contexte béninois
            prompt_text = f"""You are an expert OCR system specialized in educational documents from Benin. Extract text from this image in {language}.

Instructions:
- Extract ALL text accurately
- Maintain structure (paragraphs, lists, headings)
- Preserve formatting where possible
- Handle mathematical formulas carefully
- Include any diagrams descriptions
- Format output as clean, structured text
- Context: Educational document from Benin school system

Extract the text now:"""
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert OCR system for educational documents with high accuracy in text extraction."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt_text
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 4000,
                "temperature": 0.1,
                "top_p": 0.9,
                "stream": False
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )'''
        
        new_extract = '''def extract_text_from_bytes(self, image_data: bytes, language: str = 'fr') -> Dict:
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
            )'''
        
        content = content.replace(old_extract, new_extract)
        
        # Mettre à jour le traitement de la réponse
        old_response = '''if response.status_code == 200:
                result = response.json()
                extracted_text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                confidence_score = self._calculate_confidence(extracted_text)
                
                return {
                    'text': extracted_text.strip(),
                    'confidence': confidence_score,
                    'success': True,
                    'language_detected': language,
                    'model_used': self.model_name,
                    'processing_time': response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
                    'tokens_used': result.get('usage', {}).get('total_tokens', 0)
                }
            else:
                logger.error(f"Erreur API Nemotron: {response.status_code} - {response.text}")
                return {
                    'text': '',
                    'confidence': 0,
                    'success': False,
                    'error': f"API Error: {response.status_code}",
                    'language_detected': language
                }'''
        
        new_response = '''if response.status_code == 200:
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
                }'''
        
        content = content.replace(old_response, new_response)
        
        with open('ai_engine/nvidia_ocr.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ Configuration NVIDIA OCR mise à jour avec le bon endpoint")
        print(f"   Endpoint: https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v1")
        print(f"   Modèle: nvidia/nemotron-ocr-v1")
        
    except Exception as e:
        print(f"⚠️ Erreur mise à jour configuration: {e}")

if __name__ == "__main__":
    import json
    success = test_nemotron_ocr_v1_correct()
    if success:
        print("\n🎉 NEMOTRON OCR V1 CORRECTEMENT CONFIGURÉ!")
    else:
        print("\n❌ ERREUR LORS DU TEST NEMOTRON OCR V1")
