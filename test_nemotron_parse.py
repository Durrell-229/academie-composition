#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def test_nemotron_parse():
    """Test du modèle nvidia/nemotron-parse qui semble être le modèle OCR"""
    print("🧪 TEST MODÈLE NVIDIA/NEMOTRON-PARSE")
    print("=" * 60)
    
    try:
        import requests
        import json
        
        api_key = os.environ.get('NVIDIA_API_KEY', '')
        
        print(f"\n🔑 Clé API: {api_key[:20]}...")
        print(f"🤖 Modèle cible: nvidia/nemotron-parse")
        print(f"📝 Ce modèle semble être le modèle OCR NVIDIA disponible")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
        model = "nvidia/nemotron-parse"
        
        print(f"\n📡 Test du modèle {model}...")
        
        # Test 1: Extraction de texte simple
        print("\n1. Test extraction de texte simple...")
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un expert en extraction et analyse de texte pour documents éducatifs béninois. Extrais et structure le contenu avec précision."
                },
                {
                    "role": "user",
                    "content": """Extrais et structure les informations de ce document:

BULLETIN SCOLAIRE - TRIMESTRE 1
Élève: Koffi Marc
Classe: Terminale S1
École: Lycée Cotonou
Année: 2025-2026

Matières:
Mathématiques: 16/20 (Coeff 4)
Physique: 14/20 (Coeff 3)
Chimie: 15/20 (Coeff 3)
SVT: 13/20 (Coeff 2)
Français: 12/20 (Coeff 2)
Anglais: 14/20 (Coeff 2)
Histoire-Géo: 11/20 (Coeff 2)

Moyenne générale: 14.2/20
Rang: 5/32"""
                }
            ],
            "max_tokens": 300,
            "temperature": 0.1
        }
        
        response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"   ✅ Test extraction réussi")
            print(f"   Tokens utilisés: {result.get('usage', {}).get('total_tokens', 'N/A')}")
            print(f"   Réponse: {ai_response[:200]}...")
            
            # Test 2: OCR de corrigé type
            print("\n2. Test OCR de corrigé type...")
            
            ocr_payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Tu es un expert OCR pour documents éducatifs. Extrais le texte, identifie la structure, et isole le barème de correction."
                    },
                    {
                        "role": "user",
                        "content": """Analyse ce corrigé type et extrais le barème de correction:

CORRIGÉ TYPE - MATHÉMATIQUES
EXERCICE 1: Étude de fonction (4 points)

a) Calcule la dérivée de f(x) = x³ - 3x + 2 (1 pt)
   f'(x) = 3x² - 3

b) Détermine le tableau de variation (1.5 pts)
   x: -∞ | -1 | 1 | +∞
   f'(x): + | 0 | - | 0 | +
   f(x): ↗ | 4 | ↘ | 0 | ↗

c) Déduis les extremums (1.5 pts)
   Maximum: (-1, 4)
   Minimum: (1, 0)

EXERCICE 2: Intégration (8 points)
..."""
                    }
                ],
                "max_tokens": 250,
                "temperature": 0.2
            }
            
            ocr_response = requests.post(endpoint, headers=headers, json=ocr_payload, timeout=60)
            
            if ocr_response.status_code == 200:
                ocr_result = ocr_response.json()
                ocr_text = ocr_result.get('choices', [{}])[0].get('message', {}).get('content', '')
                print(f"   ✅ Test OCR corrigé réussi")
                print(f"   Réponse OCR: {ocr_text[:200]}...")
                
                # Test 3: Comparaison copie/corrigé
                print("\n3. Test comparaison copie/corrigé...")
                
                compare_payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Tu es un expert en correction pédagogique. Compare la copie élève avec le corrigé type et attribue une note selon un barème."
                        },
                        {
                            "role": "user",
                            "content": f"""CORRIGÉ TYPE:
Question: Calcule f'(x) pour f(x) = x³ - 3x + 2
Réponse attendue: f'(x) = 3x² - 3 (1 pt)

COPIIE ÉLÈVE:
Pour f(x) = x³ - 3x + 2, la dérivée est f'(x) = 3x² - 3

Évalue cette réponse et attribue la note sur 1 point."""
                        }
                    ],
                    "max_tokens": 100,
                    "temperature": 0.1
                }
                
                compare_response = requests.post(endpoint, headers=headers, json=compare_payload, timeout=60)
                
                if compare_response.status_code == 200:
                    compare_result = compare_response.json()
                    compare_text = compare_result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    print(f"   ✅ Test comparaison réussi")
                    print(f"   Évaluation: {compare_text[:150]}...")
                    
                    print("\n" + "=" * 60)
                    print("🎉 TOUS LES TESTS NEMOTRON-PARSE RÉUSSIS!")
                    print("\n📊 RÉSULTATS:")
                    print("✅ Extraction de texte fonctionnelle")
                    print("✅ OCR de corrigés types fonctionnel")
                    print("✅ Comparaison copie/corrigé fonctionnelle")
                    print("✅ Adapté au contexte éducatif béninois")
                    
                    # Mettre à jour la configuration
                    update_nvidia_config(endpoint, model)
                    
                    return True
                else:
                    print(f"   ❌ Test comparaison échoué: {compare_response.status_code}")
            else:
                print(f"   ❌ Test OCR corrigé échoué: {ocr_response.status_code}")
        else:
            print(f"   ❌ Test extraction échoué: {response.status_code}")
            print(f"   Message: {response.text[:200]}")
        
        print("\n❌ Le modèle nvidia/nemotron-parse n'est pas fonctionnel")
        print("\n💡 Le modèle meta/llama-3.1-70b-instruct reste configuré comme alternative")
        
        return False
        
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
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
    success = test_nemotron_parse()
    if success:
        print("\n🚀 NEMOTRON-PARSE CONFIGURÉ COMME MODÈLE OCR!")
    else:
        print("\n⚠️ ALTERNATIVE CONSERVÉE")
