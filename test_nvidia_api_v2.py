#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def test_nvidia_api_alternatives():
    """Test alternatifs pour la clé API NVIDIA"""
    print("🧪 TEST ALTERNATIFS CLÉ API NVIDIA")
    print("=" * 60)
    
    try:
        import requests
        import json
        
        # Configuration
        api_key = "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"
        
        # Différents endpoints à tester
        endpoints = [
            "https://integrate.api.nvidia.com/v1/chat/completions",
            "https://api.nvcf.nvidia.com/v2/nvcf/publish/v2/nemotron-4-340b-instruct/deployments/nemotron-4-340b-instruct",
            "https://api.nvcf.nvidia.com/v2/nvcf/publish/v2/meta/llama-3.1-405b-instruct/deployments/meta/llama-3.1-405b-instruct",
            "https://api.nvcf.nvidia.com/v2/nvcf/publish/v2/nemotron-4-340b-instruct/v1/chat/completions"
        ]
        
        # Différents modèles à tester
        models = [
            "nvidia/nemotron-4-340b-instruct",
            "meta/llama-3.1-405b-instruct",
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "nemotron-4-340b-instruct",
            "llama-3.1-405b-instruct"
        ]
        
        print(f"\n🔑 Clé API: {api_key[:20]}...")
        print(f"\n🔍 Test de différents endpoints et modèles...")
        
        success_found = False
        
        for endpoint in endpoints:
            print(f"\n📡 Test endpoint: {endpoint}")
            
            for model in models:
                print(f"   🤖 Test modèle: {model}")
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Bonjour, réponds simplement: OK"
                        }
                    ],
                    "max_tokens": 10,
                    "temperature": 0.1
                }
                
                try:
                    response = requests.post(
                        endpoint,
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    print(f"      Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"      ✅ SUCCÈS! Endpoint et modèle trouvés")
                        result = response.json()
                        ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                        print(f"      Réponse: {ai_response}")
                        success_found = True
                        
                        # Test complet avec ce endpoint
                        print(f"\n🎯 Test complet avec endpoint valide...")
                        full_payload = {
                            "model": model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "Tu es un assistant pour le système éducatif béninois."
                                },
                                {
                                    "role": "user",
                                    "content": "Génère une question de mathématiques pour Terminale S sur les dérivées."
                                }
                            ],
                            "max_tokens": 100,
                            "temperature": 0.7
                        }
                        
                        full_response = requests.post(endpoint, headers=headers, json=full_payload, timeout=60)
                        
                        if full_response.status_code == 200:
                            full_result = full_response.json()
                            full_ai_response = full_result.get('choices', [{}])[0].get('message', {}).get('content', '')
                            print(f"   ✅ Test complet réussi")
                            print(f"   Réponse complète: {full_ai_response}")
                            
                            # Mettre à jour la configuration
                            print(f"\n⚙️ Configuration trouvée:")
                            print(f"   Endpoint: {endpoint}")
                            print(f"   Modèle: {model}")
                            
                            # Mettre à jour le service OCR
                            update_nvidia_config(endpoint, model)
                            
                            return True
                        else:
                            print(f"   ⚠️ Test complet échoué: {full_response.status_code}")
                        
                        break  # Sortir de la boucle des modèles
                        
                    elif response.status_code == 404:
                        print(f"      ❌ Not Found")
                    elif response.status_code == 401:
                        print(f"      ❌ Unauthorized - Clé API invalide")
                    elif response.status_code == 403:
                        print(f"      ❌ Forbidden - Pas d'accès")
                    else:
                        print(f"      ❌ Erreur: {response.status_code}")
                        print(f"      Message: {response.text[:200]}")
                        
                except requests.exceptions.Timeout:
                    print(f"      ⏱️ Timeout")
                except requests.exceptions.ConnectionError:
                    print(f"      🔌 Connection error")
                except Exception as e:
                    print(f"      ❌ Erreur: {str(e)}")
            
            if success_found:
                break  # Sortir de la boucle des endpoints
        
        if not success_found:
            print("\n❌ Aucun endpoint/modele valide trouvé")
            print("\n💡 Suggestions:")
            print("1. Vérifiez que la clé API est correcte")
            print("2. Vérifiez que l'API NVIDIA est activée sur votre compte")
            print("3. Contactez le support NVIDIA pour activer l'accès")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def update_nvidia_config(endpoint, model):
    """Mettre à jour la configuration NVIDIA"""
    try:
        # Mettre à jour le service OCR
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
        
        print("✅ Configuration NVIDIA mise à jour")
        
    except Exception as e:
        print(f"⚠️ Erreur mise à jour configuration: {e}")

if __name__ == "__main__":
    success = test_nvidia_api_alternatives()
    if success:
        print("\n🎉 CONFIGURATION NVIDIA TROUVÉE ET VALIDÉE!")
    else:
        print("\n❌ IMPOSSIBLE DE TROUVER UNE CONFIGURATION VALIDE")
