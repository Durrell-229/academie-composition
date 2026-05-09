#!/usr/bin/env python
"""
Script de validation simple pour le système temps réel
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def validate_realtime_system():
    """Valider le système temps réel"""
    print("🧪 VALIDATION DU SYSTÈME TEMPS RÉEL")
    print("=" * 50)
    
    # 1. Vérifier les imports
    try:
        from accounts.models import User
        from realtime.services import realtime_service
        from realtime.consumers import DashboardConsumer, GlobalStatsConsumer
        print("✅ Imports réussis")
    except Exception as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    
    # 2. Vérifier les utilisateurs
    try:
        eleve_count = User.objects.filter(role='eleve').count()
        prof_count = User.objects.filter(role='professeur').count()
        admin_count = User.objects.filter(role='admin').count()
        print(f"✅ Utilisateurs trouvés: {eleve_count} élèves, {prof_count} profs, {admin_count} admins")
    except Exception as e:
        print(f"❌ Erreur utilisateurs: {e}")
        return False
    
    # 3. Vérifier les templates
    try:
        from django.template.loader import get_template
        
        templates = [
            'accounts/dashboard_eleve.html',
            'accounts/dashboard_professeur.html', 
            'accounts/dashboard_admin.html',
            'accounts/dashboard_conseiller.html'
        ]
        
        for template in templates:
            get_template(template)
        print("✅ Templates validés")
    except Exception as e:
        print(f"❌ Erreur templates: {e}")
        return False
    
    # 4. Vérifier les fichiers statiques
    try:
        import os
        static_files = [
            'static/js/dashboard-realtime.js',
            'static/css/dashboard-realtime.css'
        ]
        
        for file_path in static_files:
            if os.path.exists(file_path):
                print(f"✅ Fichier trouvé: {file_path}")
            else:
                print(f"❌ Fichier manquant: {file_path}")
    except Exception as e:
        print(f"❌ Erreur fichiers statiques: {e}")
    
    # 5. Vérifier les URLs
    try:
        from django.urls import reverse
        dashboard_url = reverse('dashboard')
        print(f"✅ URL dashboard: {dashboard_url}")
    except Exception as e:
        print(f"❌ Erreur URLs: {e}")
        return False
    
    print("\n🎯 SYSTÈME TEMPS RÉEL PRÊT!")
    print("=" * 50)
    print("📋 Instructions:")
    print("1. Démarrez le serveur: python manage.py runserver")
    print("2. Ouvrez: http://127.0.0.1:8000/accounts/dashboard/")
    print("3. Vérifiez le point vert en haut à droite (connexion temps réel)")
    print("4. Les données se mettront à jour automatiquement")
    
    return True

if __name__ == "__main__":
    validate_realtime_system()
