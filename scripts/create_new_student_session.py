#!/usr/bin/env python
"""
Crée une nouvelle session de test pour un élève
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

from django.contrib.auth import get_user_model
from compositions.models import CompositionSession
from exams.models import Exam

User = get_user_model()

def create_fresh_session():
    """Crée une session fraîche pour les tests"""
    print("🆕 CRÉATION SESSION FRAÎCHE POUR ÉLÈVE")
    print("=" * 40)
    
    # Trouver un élève
    student = User.objects.filter(is_staff=False).first()
    if not student:
        print("❌ Aucun élève trouvé")
        return None
    
    print(f"✅ Élève: {student.email}")
    
    # Trouver un examen
    exam = Exam.objects.first()
    if not exam:
        print("❌ Aucun examen trouvé")
        return None
    
    print(f"✅ Examen: {exam.titre}")
    
    # Créer une nouvelle session
    session, created = CompositionSession.objects.get_or_create(
        exam=exam,
        eleve=student,
        defaults={
            'mode': 'en_ligne',
            'statut': 'en_attente',
            'ip_address': '127.0.0.1',
            'user_agent': 'Test Environment'
        }
    )
    
    if created:
        print(f"✅ Nouvelle session créée: {session.id}")
        print(f"   Statut: {session.statut}")
        
        # URL de la salle de composition
        room_url = f"http://127.0.0.1:8000/compositions/room/{session.id}/"
        print(f"   URL salle: {room_url}")
        
        return session
    else:
        print(f"⚠️ Session existante trouvée: {session.id}")
        print(f"   Statut: {session.statut}")
        
        # Si la session est déjà terminée, la réinitialiser
        if session.statut in ['soumis', 'corrige', 'exclu']:
            print("🔄 Réinitialisation de la session...")
            session.statut = 'en_attente'
            session.save()
            print(f"✅ Session réinitialisée: {session.statut}")
        
        return session

def main():
    """Fonction principale"""
    session = create_fresh_session()
    
    if session:
        print("\n🎯 INSTRUCTIONS POUR TESTER:")
        print("1. Démarrer le serveur: python manage.py runserver 8000")
        print("2. Se connecter avec l'élève")
        print("3. Accéder à la salle de composition")
        print("4. Écrire une réponse dans la zone de texte")
        print("5. Uploader une copie (optionnel)")
        print("6. Cliquer sur 'Soumettre l'examen'")
        print("7. Confirmer dans le modal")
        
        print(f"\n🔗 URL DIRECTE: http://127.0.0.1:8000/compositions/room/{session.id}/")
        
        print("\n📋 COMPTES ÉLÈVE DISPONIBLES:")
        students = User.objects.filter(is_staff=False)
        for student in students:
            print(f"   {student.email} | mot de passe: Test123456!")
        
        print("\n✅ La session est prête pour les tests !")
    else:
        print("❌ Impossible de créer une session")

if __name__ == "__main__":
    main()
