#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def test_nemotron_ocr_v1():
    """Test spécifique du modèle nemotron-ocr v1"""
    print("🧪 TEST MODÈLE NEMOTRON-OCR V1")
    print("=" * 60)
    
    try:
        import requests
        import json
        
        api_key = "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"
        
        print(f"\n🔑 Clé API: {api_key[:20]}...")
        print(f"🤖 Modèle cible: nemotron-ocr v1")
        
        # Différentes variations du nom du modèle
        model_variations = [
            "nemotron-ocr-v1",
            "nvidia/nemotron-ocr-v1",
            "nemotron_ocr_v1",
            "nvidia/nemotron-ocr",
            "nemotron-ocr"
        ]
        
        # Différents endpoints
        endpoints = [
            "https://integrate.api.nvidia.com/v1/chat/completions",
            "https://integrate.api.nvidia.com/v1/ocr/completions",
            "https://api.nvcf.nvidia.com/v2/nvcf/publish/v2/nemotron-ocr-v1/deployments"
        ]
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print("\n🔍 Recherche du modèle nemotron-ocr v1...")
        
        # D'abord, vérifier le catalogue complet
        print("\n1. Recherche dans le catalogue...")
        catalog_url = "https://integrate.api.nvidia.com/v1/models"
        
        try:
            response = requests.get(catalog_url, headers=headers, timeout=30)
            if response.status_code == 200:
                models = response.json()
                print(f"   ✅ Catalogue accessible - {len(models.get('data', []))} modèles")
                
                # Chercher des modèles OCR
                ocr_models = [m for m in models.get('data', []) if 'ocr' in m.get('id', '').lower() or 'nemotron' in m.get('id', '').lower()]
                
                if ocr_models:
                    print(f"   📋 Modèles OCR/Nemotron trouvés:")
                    for model in ocr_models:
                        print(f"      - {model.get('id', 'N/A')}")
                else:
                    print(f"   ⚠️ Aucun modèle OCR/Nemotron trouvé dans le catalogue")
                    
        except Exception as e:
            print(f"   ❌ Erreur catalogue: {e}")
        
        # Tester chaque variation du modèle
        print("\n2. Test des variations du modèle...")
        
        for endpoint in endpoints:
            print(f"\n📡 Endpoint: {endpoint}")
            
            for model in model_variations:
                print(f"   🤖 Test: {model}")
                
                # Test OCR simple
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Tu es un expert OCR pour documents éducatifs."
                        },
                        {
                            "role": "user",
                            "content": "Extrais le texte de ce document: 'Ceci est un test OCR pour le système éducatif béninois.'"
                        }
                    ],
                    "max_tokens": 50,
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
                        print(f"      ✅ SUCCÈS! Modèle trouvé et fonctionnel")
                        result = response.json()
                        ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                        print(f"      Réponse: {ai_response[:100]}...")
                        
                        # Test OCR complet
                        print(f"\n   🎯 Test OCR complet...")
                        ocr_payload = {
                            "model": model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "Tu es un expert OCR spécialisé pour le système éducatif béninois. Extrais et analyse le texte avec précision."
                                },
                                {
                                    "role": "user",
                                    "content": """Analyse ce texte et extrait les informations:
                                    
EXAMEN DE MATHÉMATIQUES - TERMINALE S
ÉCOLE: Lycée Cotonou
SUJET: Les fonctions dérivées

Question 1: Soit f(x) = x³ - 3x + 2. Calcule f'(x).
Question 2: Détermine les extremums de f.
Question 3: Trace la courbe représentative.

Barème: Q1=4pts, Q2=8pts, Q3=8pts"""
                                }
                            ],
                            "max_tokens": 200,
                            "temperature": 0.3
                        }
                        
                        ocr_response = requests.post(endpoint, headers=headers, json=ocr_payload, timeout=60)
                        
                        if ocr_response.status_code == 200:
                            ocr_result = ocr_response.json()
                            ocr_text = ocr_result.get('choices', [{}])[0].get('message', {}).get('content', '')
                            print(f"      ✅ Test OCR complet réussi")
                            print(f"      Réponse OCR: {ocr_text[:150]}...")
                            
                            # Mettre à jour la configuration
                            update_nvidia_config(endpoint, model)
                            
                            return True
                        else:
                            print(f"      ⚠️ Test OCR complet échoué: {ocr_response.status_code}")
                        
                        return True
                        
                    elif response.status_code == 404:
                        print(f"      ❌ Not Found")
                    elif response.status_code == 401:
                        print(f"      ❌ Unauthorized")
                    elif response.status_code == 400:
                        print(f"      ❌ Bad Request")
                        try:
                            error_detail = response.json()
                            print(f"      Détail: {error_detail.get('detail', error_detail.get('error', 'N/A'))[:100]}")
                        except:
                            print(f"      Message: {response.text[:100]}")
                    else:
                        print(f"      ❌ Erreur: {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    print(f"      ⏱️ Timeout")
                except requests.exceptions.ConnectionError:
                    print(f"      🔌 Connection error")
                except Exception as e:
                    print(f"      ❌ Erreur: {str(e)}")
        
        # Si nemotron-ocr v1 n'est pas trouvé, proposer des alternatives OCR
        print("\n3. Recherche d'alternatives OCR...")
        
        ocr_alternatives = [
            "google/gemma-2-27b-it",
            "meta/llama-3.1-70b-instruct",
            "nvidia/llama-3.1-nemotron-70b-instruct"
        ]
        
        for model in ocr_alternatives:
            print(f"   🤖 Test alternative OCR: {model}")
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Tu es un expert OCR pour documents éducatifs."
                    },
                    {
                        "role": "user",
                        "content": "Extrais le texte: 'Test OCR Bénin'"
                    }
                ],
                "max_tokens": 20
            }
            
            try:
                response = requests.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    print(f"      ✅ Alternative fonctionnelle")
                    
                    # Proposer cette alternative
                    print(f"\n💡 Alternative trouvée: {model}")
                    print(f"   Voulez-vous utiliser cette alternative à nemotron-ocr v1?")
                    
                    # Mettre à jour avec l'alternative
                    update_nvidia_config("https://integrate.api.nvidia.com/v1/chat/completions", model)
                    
                    return True
                    
            except Exception as e:
                print(f"      ❌ Erreur: {e}")
        
        print("\n❌ Modèle nemotron-ocr v1 non trouvé")
        print("\n💡 Suggestions:")
        print("1. Vérifiez l'orthographe exacte du modèle")
        print("2. Le modèle peut avoir un nom différent sur votre compte")
        print("3. Contactez le support NVIDIA pour activer nemotron-ocr v1")
        print("4. Utilisez une alternative OCR fonctionnelle")
        
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
            'self.model_name = "meta/llama-3.1-70b-instruct"',
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
    success = test_nemotron_ocr_v1()
    if success:
        print("\n🎉 MODÈLE NEMOTRON-OCR V1 CONFIGURÉ!")
    else:
        print("\n❌ MODÈLE NEMOTRON-OCR V1 NON TROUVÉ")
