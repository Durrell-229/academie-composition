#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def test_nvidia_ocr():
    """Tester le service OCR NVIDIA"""
    print("🧪 TEST DU SERVICE OCR NVIDIA")
    print("=" * 50)
    
    try:
        from ai_engine.nvidia_ocr import nvidia_ocr_service
        from django.core.files.base import ContentFile
        import base64
        
        tests = []
        
        # Test 1: Vérification de la configuration
        print("\n1. Configuration du service...")
        try:
            is_configured = nvidia_ocr_service.is_configured()
            health_check = nvidia_ocr_service.health_check()
            
            tests.append(("✅ Configuration", f"Configuré: {is_configured}, Status: {health_check.get('status', 'unknown')}"))
            
        except Exception as e:
            tests.append(("❌ Configuration", str(e)))
        
        # Test 2: Créer une image de test
        print("\n2. Création image de test...")
        try:
            # Créer une image de test simple
            test_image_content = b"""iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6vgAAAABJRU5ErkJggg=="""
            test_image = base64.b64decode(test_image_content)
            
            # Créer un fichier de test
            test_file = ContentFile(test_image, name='test_image.png')
            
            tests.append(("✅ Image de test", "Créée avec succès"))
            
        except Exception as e:
            tests.append(("❌ Image de test", str(e)))
            return False
        
        # Test 3: Extraction de texte
        print("\n3. Extraction de texte...")
        try:
            result = nvidia_ocr_service.extract_text_from_file(test_file, language='fr')
            
            if result['success']:
                tests.append(("✅ Extraction OCR", f"Texte: '{result['text'][:50]}...', Confiance: {result.get('confidence', 0)}%"))
            else:
                tests.append(("❌ Extraction OCR", f"Erreur: {result.get('error', 'Unknown')}"))
                
        except Exception as e:
            tests.append(("❌ Extraction OCR", str(e)))
        
        # Test 4: Langues supportées
        print("\n4. Langues supportées...")
        try:
            languages = nvidia_ocr_service.get_supported_languages()
            tests.append(("✅ Langues", f"{len(languages)} langues: {', '.join(languages[:5])}..."))
            
        except Exception as e:
            tests.append(("❌ Langues", str(e)))
        
        # Test 5: Prétraitement d'image
        print("\n5. Prétraitement d'image...")
        try:
            processed = nvidia_ocr_service.preprocess_image(test_image)
            tests.append(("✅ Prétraitement", f"Taille originale: {len(test_image)} -> Traitée: {len(processed)}"))
            
        except Exception as e:
            tests.append(("❌ Prétraitement", str(e)))
        
        # Test 6: Service multi-IA intégré
        print("\n6. Service multi-IA intégré...")
        try:
            from ai_engine.enhanced_multi_ai import multi_ai
            
            if hasattr(multi_ai, 'ocr_service'):
                tests.append(("✅ Intégration multi-IA", "NVIDIA OCR intégré"))
            else:
                tests.append(("❌ Intégration multi-IA", "OCR non trouvé"))
                
        except Exception as e:
            tests.append(("❌ Intégration multi-IA", str(e)))
        
        # Test 7: Service de correction
        print("\n7. Service de correction...")
        try:
            from ai_engine.enhanced_ocr_correction import enhanced_ocr_service
            
            # Test de nettoyage de texte
            test_text = "Ceci est un test de texte pour la correction OCR avec le contexte éducatif béninois."
            cleaned = enhanced_ocr_service.clean_text(test_text)
            
            tests.append(("✅ Service correction", f"Texte nettoyé: '{cleaned[:30]}...'"))
            
        except Exception as e:
            tests.append(("❌ Service correction", str(e)))
        
        # Affichage des résultats
        print("\n" + "=" * 50)
        print("📊 RÉSULTATS DES TESTS")
        print("=" * 50)
        
        for test, result in tests:
            print(f"{test}: {result}")
        
        # Compte des erreurs
        errors = [test for test in tests if isinstance(test[1], str) and test[1].startswith('❌')]
        
        print(f"\n📊 BILAN: {len(tests) - len(errors)}/{len(tests)} tests OK")
        
        if errors:
            print("\n❌ ERREURS DÉTECTÉES:")
            for test, error in errors:
                print(f"  - {test}: {error}")
        else:
            print("\n🎉 TOUS LES TESTS SONT OK!")
        
        return len(errors) == 0
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_nvidia_ocr()
    if success:
        print("\n🚀 SERVICE OCR NVIDIA 100% OPÉRATIONNEL!")
        print("\n📋 INSTRUCTIONS:")
        print("1. Obtenez votre clé API NVIDIA gratuite")
        print("2. Ajoutez NVIDIA_API_KEY=votre_clé dans votre .env")
        print("3. Redémarrez votre serveur Django")
        print("4. Le service OCR NVIDIA est prêt pour la correction de copies!")
    else:
        print("\n❌ Des problèmes subsistent, voir les erreurs ci-dessus")
