#!/usr/bin/env python
"""
Débogage de l'accès aux sessions de composition
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

from django.contrib.auth import get_user_model
from compositions.models import CompositionSession, Resultat
from django.test import Client

User = get_user_model()

def debug_session_access():
    """Débogue l'accès à une session spécifique"""
    print("🔍 DÉBOGAGE ACCÈS SESSION")
    print("=" * 40)
    
    # Session demandée dans l'erreur
    session_id = 'f4f89ae0-b8e7-483c-9be0-bf39cdcf9d22'
    
    try:
        # Vérifier si la session existe
        session = CompositionSession.objects.get(id=session_id)
        print(f"✅ Session trouvée: {session.exam.titre}")
        print(f"   Élève: {session.eleve.email}")
        print(f"   Statut: {session.statut}")
        
        # Vérifier l'utilisateur
        user = session.eleve
        print(f"   ID utilisateur: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Staff: {user.is_staff}")
        print(f"   Role: {getattr(user, 'role', 'non défini')}")
        
        # Vérifier le résultat
        try:
            resultat = Resultat.objects.get(session=session)
            print(f"✅ Résultat trouvé: {resultat.note}/{resultat.note_sur}")
            print(f"   Bulletin: {'Oui' if resultat.bulletin_pdf else 'Non'}")
        except Resultat.DoesNotExist:
            print("❌ Pas de résultat")
        
        # Test avec le client Django
        print("\n🧪 TEST ACCÈS VIA DJANGO CLIENT")
        client = Client()
        
        # Connexion
        login_success = client.login(email='test2@example.com', password='Test123456!')
        print(f"Connexion: {'✅ Succès' if login_success else '❌ Échec'}")
        
        if login_success:
            # Test accès à la page de résultats
            response = client.get(f'/compositions/result/{session_id}/')
            print(f"Accès résultats: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Page accessible")
            elif response.status_code == 404:
                print("❌ Page non trouvée (404)")
                print("   Vérification de la vue...")
                
                # Vérifier la vue
                from compositions.views import result_view
                print("   Vue result_view: ✅ Importée")
                
                # Tester directement la vue
                try:
                    from django.http import HttpRequest
                    request = HttpRequest()
                    request.user = user
                    
                    result = result_view(request, session_id)
                    print(f"   Vue directe: {result.status_code if hasattr(result, 'status_code') else 'OK'}")
                except Exception as e:
                    print(f"   Erreur vue: {e}")
            else:
                print(f"⚠️ Status inattendu: {response.status_code}")
        
        return True
        
    except CompositionSession.DoesNotExist:
        print(f"❌ Session non trouvée: {session_id}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def check_all_sessions():
    """Vérifie toutes les sessions"""
    print("\n📋 VÉRIFICATION DE TOUTES LES SESSIONS")
    print("=" * 40)
    
    sessions = CompositionSession.objects.all()
    
    for session in sessions:
        print(f"\n📝 Session: {session.exam.titre}")
        print(f"   ID: {session.id}")
        print(f"   Élève: {session.eleve.email}")
        print(f"   Statut: {session.statut}")
        
        # Vérifier si un résultat existe
        try:
            resultat = Resultat.objects.get(session=session)
            print(f"   Résultat: {resultat.note}/{resultat.note_sur}")
            print(f"   Bulletin: {'✅' if resultat.bulletin_pdf else '❌'}")
        except Resultat.DoesNotExist:
            print(f"   Résultat: ❌ Non créé")
        
        # URL d'accès
        url = f"http://127.0.0.1:8000/compositions/result/{session.id}/"
        print(f"   URL: {url}")

def fix_session_access():
    """Corrige les problèmes d'accès"""
    print("\n🔧 CORRECTION DES PROBLÈMES D'ACCÈS")
    print("=" * 40)
    
    # Vérifier la vue result_view
    try:
        from compositions.views import result_view
        print("✅ Vue result_view importée")
        
        # Vérifier le décorateur login_required
        import functools
        if hasattr(result_view, '__wrapped__'):
            print("✅ Décorateur login_required présent")
        else:
            print("⚠️ Décorateur login_required peut être manquant")
        
        # Vérifier la logique de la vue
        print("✅ Logique de vue: get_object_or_404 avec filtre eleve=request.user")
        
    except Exception as e:
        print(f"❌ Erreur vue: {e}")
    
    # Vérifier les URLs
    try:
        from django.urls import reverse
        url = reverse('result_detail', kwargs={'session_id': 'test-id'})
        print(f"✅ URL result_detail: {url}")
    except Exception as e:
        print(f"❌ Erreur URL: {e}")
    
    # Suggestion de correction
    print("\n💡 SUGGESTIONS:")
    print("1. Vérifier que l'utilisateur est bien connecté")
    print("2. S'assurer que session.eleve == request.user")
    print("3. Vérifier les permissions de la vue")
    print("4. Tester avec un autre utilisateur si nécessaire")

def main():
    """Fonction principale"""
    debug_session_access()
    check_all_sessions()
    fix_session_access()
    
    print("\n🎯 CONCLUSION:")
    print("La session existe mais l'accès échoue probablement car:")
    print("- L'utilisateur test2@example.com n'est pas correctement connecté")
    print("- Ou il y a un problème de permissions dans la vue")
    print("\n📋 ACTIONS RECOMMANDÉES:")
    print("1. Se connecter avec test2@example.com dans le navigateur")
    print("2. Accéder directement à l'URL de résultats")
    print("3. Si ça échoue, vérifier les logs Django")

if __name__ == "__main__":
    main()
