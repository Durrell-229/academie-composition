#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def test_nvidia_api_catalog():
    """Test du catalogue NVIDIA et modèles disponibles"""
    print("🧪 TEST CATALOGUE NVIDIA ET MODÈLES DISPONIBLES")
    print("=" * 60)
    
    try:
        import requests
        import json
        
        api_key = "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"
        
        print(f"\n🔑 Clé API: {api_key[:20]}...")
        
        # Test 1: Catalogue des modèles
        print("\n1. Test catalogue des modèles...")
        catalog_url = "https://integrate.api.nvidia.com/v1/models"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(catalog_url, headers=headers, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                models = response.json()
                print(f"   ✅ Catalogue accessible")
                print(f"   Modèles disponibles: {len(models.get('data', []))}")
                
                for model in models.get('data', [])[:10]:
                    print(f"      - {model.get('id', 'N/A')}")
            else:
                print(f"   ❌ Erreur: {response.status_code}")
                print(f"   Message: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)}")
        
        # Test 2: Endpoint de base
        print("\n2. Test endpoint de base...")
        base_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        
        # Essayer avec des modèles courants
        common_models = [
            "meta/llama-3.1-8b-instruct",
            "meta/llama-3.1-70b-instruct",
            "google/gemma-2-27b-it",
            "mistralai/mistral-large",
            "nvidia/llama-3.1-nemotron-70b-instruct"
        ]
        
        for model in common_models:
            print(f"   🤖 Test modèle: {model}")
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "OK"
                    }
                ],
                "max_tokens": 5
            }
            
            try:
                response = requests.post(base_url, headers=headers, json=payload, timeout=30)
                print(f"      Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"      ✅ SUCCÈS! Modèle fonctionnel")
                    result = response.json()
                    print(f"      Tokens: {result.get('usage', {}).get('total_tokens', 'N/A')}")
                    
                    # Test complet
                    print(f"\n   🎯 Test complet avec {model}...")
                    full_payload = {
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Tu es un assistant pour l'éducation."
                            },
                            {
                                "role": "user",
                                "content": "Génère une question de mathématiques pour Terminale S."
                            }
                        ],
                        "max_tokens": 50,
                        "temperature": 0.7
                    }
                    
                    full_response = requests.post(base_url, headers=headers, json=full_payload, timeout=60)
                    
                    if full_response.status_code == 200:
                        full_result = full_response.json()
                        ai_response = full_result.get('choices', [{}])[0].get('message', {}).get('content', '')
                        print(f"      ✅ Test complet réussi")
                        print(f"      Réponse: {ai_response[:100]}...")
                        
                        # Mettre à jour la configuration
                        update_nvidia_config(base_url, model)
                        
                        return True
                    else:
                        print(f"      ⚠️ Test complet échoué: {full_response.status_code}")
                    
                    return True
                    
                elif response.status_code == 404:
                    print(f"      ❌ Not Found")
                elif response.status_code == 401:
                    print(f"      ❌ Unauthorized")
                else:
                    print(f"      ❌ Erreur: {response.status_code}")
                    
            except Exception as e:
                print(f"      ❌ Erreur: {str(e)}")
        
        # Test 3: Endpoint alternatif NVIDIA
        print("\n3. Test endpoint NVIDIA NIM...")
        nim_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        
        # Modèles NIM
        nim_models = [
            "meta/llama-3.1-405b-instruct",
            "meta/llama-3.1-8b-instruct",
            "nvidia/llama-3.1-nemotron-70b-instruct"
        ]
        
        for model in nim_models:
            print(f"   🤖 Test NIM modèle: {model}")
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Test"
                    }
                ],
                "max_tokens": 5
            }
            
            try:
                response = requests.post(nim_url, headers=headers, json=payload, timeout=30)
                print(f"      Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"      ✅ SUCCÈS!")
                    update_nvidia_config(nim_url, model)
                    return True
                    
            except Exception as e:
                print(f"      ❌ Erreur: {str(e)}")
        
        print("\n❌ Aucun modèle fonctionnel trouvé")
        print("\n💡 La clé API semble valide mais aucun modèle accessible")
        print("   Vérifiez votre compte NVIDIA pour les abonnements actifs")
        
        return False
        
    except Exception as e:
        print(f"\n❌ Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def update_nvidia_config(endpoint, model):
    """Mettre à jour la configuration NVIDIA"""
    try:
        with open('ai_engine/nvidia_ocr.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer l'URL de base
        content = content.replace(
            'self.base_url = "https://integrate.api.nvidia.com/v1/chat/completions"',
            f'self.base_url = "{endpoint}"'
        )
        
        # Remplacer le nom du modèle
        content = content.replace(
            'self.model_name = "nvidia/nemotron-4-340b-instruct"',
            f'self.model_name = "{model}"'
        )
        
        with open('ai_engine/nvidia_ocr.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ Configuration NVIDIA mise à jour:")
        print(f"   Endpoint: {endpoint}")
        print(f"   Modèle: {model}")
        
    except Exception as e:
        print(f"⚠️ Erreur mise à jour configuration: {e}")

if __name__ == "__main__":
    success = test_nvidia_api_catalog()
    if success:
        print("\n🎉 CONFIGURATION NVIDIA TROUVÉE!")
    else:
        print("\n❌ AUCUN MODÈLE DISPONIBLE TROUVÉ")
