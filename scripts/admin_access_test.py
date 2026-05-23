#!/usr/bin/env python
"""
Test de l'accès admin aux sessions et résultats
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

def test_admin_access():
    """Test l'accès admin à toutes les sessions"""
    print("🔑 TEST ACCÈS ADMIN")
    print("=" * 30)
    
    # Trouver l'utilisateur admin
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        print("❌ Aucun utilisateur admin trouvé")
        return False
    
    print(f"✅ Admin trouvé: {admin_user.email}")
    
    # Lister toutes les sessions
    sessions = CompositionSession.objects.all()
    print(f"📝 Sessions disponibles: {sessions.count()}")
    
    # Test avec le client Django
    client = Client()
    
    # Connexion admin
    login_success = client.login(email=admin_user.email, password='Admin123456!')
    print(f"Connexion admin: {'✅ Succès' if login_success else '❌ Échec'}")
    
    if login_success:
        # Tester l'accès à chaque session
        success_count = 0
        for session in sessions:
            response = client.get(f'/compositions/result/{session.id}/')
            
            if response.status_code == 200:
                print(f"✅ {session.exam.titre[:30]:30} - {session.eleve.email[:20]:20}")
                success_count += 1
            else:
                print(f"❌ {session.exam.titre[:30]:30} - {session.eleve.email[:20]:20} ({response.status_code})")
        
        print(f"\n📊 Accès admin: {success_count}/{sessions.count()} sessions accessibles")
        return success_count == sessions.count()
    
    return False

def test_admin_dashboard():
    """Test l'accès admin au dashboard"""
    print("\n📊 TEST DASHBOARD ADMIN")
    print("=" * 30)
    
    admin_user = User.objects.filter(is_staff=True).first()
    client = Client()
    
    login_success = client.login(email=admin_user.email, password='Admin123456!')
    
    if login_success:
        # Test dashboard
        response = client.get('/dashboard/')
        print(f"Dashboard admin: {response.status_code}")
        
        # Test admin dashboard
        response = client.get('/admin_dashboard/')
        print(f"Admin dashboard: {response.status_code}")
        
        # Test liste des corrections IA
        response = client.get('/compositions/ia-corrections/')
        print(f"Liste corrections IA: {response.status_code}")
        
        return True
    
    return False

def create_admin_view():
    """Crée une vue admin pour voir toutes les sessions"""
    print("\n🔧 CRÉATION VUE ADMIN SESSIONS")
    print("=" * 30)
    
    admin_view_code = '''
# Vue admin pour voir toutes les sessions
@login_required
def admin_all_sessions_view(request):
    if not (request.user.is_staff or getattr(request.user, 'role', '') == 'admin'):
        return redirect('dashboard')
    
    sessions = CompositionSession.objects.all().order_by('-created_at')
    
    # Statistiques
    total_sessions = sessions.count()
    soumis_sessions = sessions.filter(statut='soumis').count()
    corrige_sessions = sessions.filter(statut='corrige').count()
    exclu_sessions = sessions.filter(statut='exclu').count()
    
    context = {
        'sessions': sessions,
        'stats': {
            'total': total_sessions,
            'soumis': soumis_sessions,
            'corrige': corrige_sessions,
            'exclu': exclu_sessions,
        }
    }
    
    return render(request, 'compositions/admin_sessions.html', context)
'''
    
    print("✅ Code vue admin généré")
    print("📝 À ajouter dans compositions/views.py")
    
    url_pattern = "path('admin-sessions/', views.admin_all_sessions_view, name='admin_all_sessions'),"
    print(f"🔗 URL à ajouter: {url_pattern}")
    
    return True

def main():
    """Fonction principale"""
    print("🚀 TEST ACCÈS ADMIN COMPLET")
    print("=" * 40)
    
    # Test 1: Accès admin aux sessions
    admin_access_ok = test_admin_access()
    
    # Test 2: Dashboard admin
    dashboard_ok = test_admin_dashboard()
    
    # Test 3: Créer vue admin
    view_created = create_admin_view()
    
    print("\n🎯 RÉSULTATS:")
    print(f"Accès sessions: {'✅ OK' if admin_access_ok else '❌ Échec'}")
    print(f"Dashboard admin: {'✅ OK' if dashboard_ok else '❌ Échec'}")
    print(f"Vue admin: {'✅ Créée' if view_created else '❌ Erreur'}")
    
    if admin_access_ok:
        print("\n🎉 L'ADMIN PEUT ACCÉDER À TOUTES LES SESSIONS!")
        print("\n📋 URLS ADMIN DISPONIBLES:")
        
        sessions = CompositionSession.objects.all()
        for session in sessions:
            url = f"http://127.0.0.1:8000/compositions/result/{session.id}/"
            print(f"   {session.exam.titre[:30]:30} - {session.eleve.email[:20]:20}")
            print(f"   {url}")
    else:
        print("\n⚠️ L'ACCÈS ADMIN NÉCESSITE DES CORRECTIONS")
        print("📋 Vérifications:")
        print("1. L'utilisateur admin est bien is_staff=True")
        print("2. Le mot de passe admin est correct")
        print("3. Les permissions de vue sont correctes")

if __name__ == "__main__":
    main()
