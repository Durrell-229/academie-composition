#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def test_all_integrations():
    """Tester toutes les intégrations"""
    print("🧪 TEST DES INTÉGRATIONS")
    print("=" * 70)
    
    tests = []
    
    # Test 1: URLs QCM béninois
    print("\n1. Test URLs QCM béninois...")
    try:
        from django.urls import reverse
        url = reverse('qcm_benin:start_benin')
        print(f"   ✅ URL QCM béninois: {url}")
        tests.append(('QCM béninois', True))
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        tests.append(('QCM béninois', False))
    
    # Test 2: URLs corrections
    print("\n2. Test URLs corrections...")
    try:
        from django.urls import reverse
        url = reverse('corrections:dashboard')
        print(f"   ✅ URL corrections: {url}")
        tests.append(('Corrections', True))
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        tests.append(('Corrections', False))
    
    # Test 3: URLs realtime
    print("\n3. Test URLs realtime...")
    try:
        from django.urls import reverse
        url = reverse('realtime:dashboard')
        print(f"   ✅ URL realtime: {url}")
        tests.append(('Realtime', True))
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        tests.append(('Realtime', False))
    
    # Test 4: Services IA
    print("\n4. Test services IA...")
    try:
        from ai_engine.nvidia_ocr import nvidia_ocr_service
        health = nvidia_ocr_service.health_check()
        print(f"   ✅ Service NVIDIA OCR: {health.get('status', 'unknown')}")
        tests.append(('NVIDIA OCR', True))
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        tests.append(('NVIDIA OCR', False))
    
    # Test 5: Services corrections
    print("\n5. Test services corrections...")
    try:
        from corrections.corrige_type_service import corrige_type_service
        print(f"   ✅ Service corrigés types chargé")
        tests.append(('Corrigés types', True))
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        tests.append(('Corrigés types', False))
    
    # Bilan
    print("\n" + "=" * 70)
    print("📊 BILAN DES INTÉGRATIONS")
    print("=" * 70)
    
    for name, success in tests:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    total = len(tests)
    passed = sum(1 for _, success in tests if success)
    
    print(f"\n📈 Résultat: {passed}/{total} intégrations réussies")
    
    return passed == total

if __name__ == "__main__":
    success = test_all_integrations()
    if success:
        print("\n🎉 TOUTES LES INTÉGRATIONS SONT OPÉRATIONNELLES!")
    else:
        print("\n⚠️ CERTAINES INTÉGRATIONS NÉCESSITENT DES CORRECTIONS")
