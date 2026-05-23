#!/usr/bin/env python
"""
Création automatique des données de test pour l'Académie Numérique
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

from django.contrib.auth import get_user_model
from exams.models import Exam
from core.models import Matiere
from compositions.models import CompositionSession
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
import uuid

User = get_user_model()

def create_test_users():
    """Crée les utilisateurs de test"""
    print("👥 CRÉATION DES UTILISATEURS DE TEST")
    
    users_data = [
        {
            'email': 'eleve.test@ecole.com',
            'password': 'Test123456!',
            'first_name': 'Test',
            'last_name': 'Élève',
            'classe': '3ème A',
            'role': 'student'
        },
        {
            'email': 'eleve2.test@ecole.com',
            'password': 'Test123456!',
            'first_name': 'Marie',
            'last_name': 'Curie',
            'classe': '4ème B',
            'role': 'student'
        },
        {
            'email': 'admin.test@ecole.com',
            'password': 'Admin123456!',
            'first_name': 'Admin',
            'last_name': 'Test',
            'role': 'admin'
        }
    ]
    
    created_users = []
    
    for user_data in users_data:
        try:
            if User.objects.filter(email=user_data['email']).exists():
                user = User.objects.get(email=user_data['email'])
                print(f"✅ Utilisateur existant: {user.email}")
            else:
                user = User.objects.create_user(
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                if user_data['role'] == 'admin':
                    user.is_staff = True
                    user.is_superuser = True
                user.classe = user_data.get('classe', '')
                user.save()
                print(f"✅ Utilisateur créé: {user.email}")
            
            created_users.append(user)
            
        except Exception as e:
            print(f"❌ Erreur création utilisateur {user_data['email']}: {e}")
    
    return created_users

def create_test_subjects():
    """Crée les matières de test"""
    print("\n📚 CRÉATION DES MATIÈRES")
    
    subjects_data = [
        {
            'nom': 'Français',
            'description': 'Langue et littérature française',
            'niveau': 'Secondaire',
            'coefficient': 3
        },
        {
            'nom': 'Mathématiques',
            'description': 'Mathématiques et calcul',
            'niveau': 'Secondaire',
            'coefficient': 4
        },
        {
            'nom': 'Histoire-Géographie',
            'description': 'Histoire et géographie',
            'niveau': 'Secondaire',
            'coefficient': 2
        }
    ]
    
    created_subjects = []
    
    for subject_data in subjects_data:
        try:
            subject, created = Matiere.objects.get_or_create(
                nom=subject_data['nom'],
                defaults={
                    'description': subject_data['description'],
                    'niveau': subject_data['niveau'],
                    'coefficient': subject_data['coefficient']
                }
            )
            
            if created:
                print(f"✅ Matière créée: {subject.nom}")
            else:
                print(f"✅ Matière existante: {subject.nom}")
            
            created_subjects.append(subject)
            
        except Exception as e:
            print(f"❌ Erreur création matière {subject_data['nom']}: {e}")
    
    return created_subjects

def create_test_files():
    """Crée les fichiers de test (sujets et corrigés)"""
    print("\n📄 CRÉATION DES FICHIERS DE TEST")
    
    # Sujet Français
    sujet_francais_content = """
COMPOSITION DE FRANÇAIS - DURÉE: 2 HEURES

Sujet:
"La technologie améliore-t-elle vraiment nos vies ou nous éloigne-t-elle de l'essentiel ?"

Consignes:
1. Rédigez une composition argumentative (200-300 mots)
2. Présentez une thèse claire
3. Argumentez avec des exemples concrets
4. Concluez avec une nuance

Barème:
- Introduction: 3 points
- Développement: 10 points  
- Conclusion: 4 points
- Langue: 3 points
Total: 20 points
""".strip()
    
    # Corrigé Français
    corrige_francais_content = """
CORRIGÉ TYPE - COMPOSITION FRANÇAIS

Introduction attendue (3/3):
- Accroche sur la place de la technologie
- Problématique clairement posée
- Annonce du plan

Développement attendu (10/10):
Thèse: La technologie améliore nos vies si nous l'utilisons judicieusement.

Arguments attendus:
1. Technologies de communication: rapprochement des distances
2. Technologies médicales: amélioration de la santé
3. Technologies éducatives: accès au savoir
4. Risques: dépendance, isolement social

Nuance attendue: Équilibre entre bénéfices et risques.

Conclusion attendue (4/4):
- Synthèse des arguments
- Ouverture sur l'avenir technologique

Langue (3/3):
- Orthographe, grammaire, style
    """.strip()
    
    # Sujet Mathématiques
    sujet_maths_content = """
EXERCICES DE MATHÉMATIQUES - DURÉE: 1 HEURE

Exercice 1 (5 points):
Résoudre l'équation: 2x² - 8x + 6 = 0

Exercice 2 (7 points):
Un triangle ABC a pour côtés AB = 8 cm, AC = 6 cm, BC = 10 cm.
1. Démontrer que le triangle est rectangle.
2. Calculer l'aire du triangle.
3. Calculer la longueur de la hauteur issue de A.

Exercice 3 (8 points):
Une fonction f est définie par f(x) = 2x² - 4x + 1
1. Calculer f'(x)
2. Étudier les variations de f
3. Déterminer le minimum de f
4. Tracer la courbe représentative

Total: 20 points
""".strip()
    
    # Corrigé Mathématiques
    corrige_maths_content = """
CORRIGÉ TYPE - MATHÉMATIQUES

Exercice 1 (5/5):
2x² - 8x + 6 = 0
Δ = b² - 4ac = 64 - 48 = 16
x₁ = (8 + 4)/4 = 3
x₂ = (8 - 4)/4 = 1
Solutions: {1; 3}

Exercice 2 (7/7):
1. AB² + AC² = 64 + 36 = 100 = BC² → Triangle rectangle en A
2. Aire = (AB × AC)/2 = (8 × 6)/2 = 24 cm²
3. Hauteur = (2 × Aire)/BC = (2 × 24)/10 = 4,8 cm

Exercice 3 (8/8):
1. f'(x) = 4x - 4
2. f'(x) = 0 → x = 1
   Tableau de variations: décroissante sur ]-∞;1], croissante sur [1;+∞[
3. Minimum: f(1) = -1
4. Parabole avec sommet (1;-1)
    """.strip()
    
    files_data = [
        {
            'name': 'sujet_francais.pdf',
            'content': sujet_francais_content,
            'type': 'sujet'
        },
        {
            'name': 'corrige_francais.pdf',
            'content': corrige_francais_content,
            'type': 'corrige_type'
        },
        {
            'name': 'sujet_maths.pdf',
            'content': sujet_maths_content,
            'type': 'sujet'
        },
        {
            'name': 'corrige_maths.pdf',
            'content': corrige_maths_content,
            'type': 'corrige_type'
        }
    ]
    
    created_files = []
    
    for file_data in files_data:
        try:
            # Créer un fichier simple (en pratique, on utiliserait un vrai PDF)
            uploaded_file = SimpleUploadedFile(
                file_data['name'],
                file_data['content'].encode('utf-8'),
                content_type='text/plain'
            )
            created_files.append({
                'file': uploaded_file,
                'name': file_data['name'],
                'type': file_data['type']
            })
            print(f"✅ Fichier créé: {file_data['name']}")
            
        except Exception as e:
            print(f"❌ Erreur création fichier {file_data['name']}: {e}")
    
    return created_files

def create_test_exams(subjects, files):
    """Crée les examens de test"""
    print("\n📝 CRÉATION DES EXAMENS")
    
    # Trouver les fichiers par type
    sujet_francais = next((f for f in files if f['name'] == 'sujet_francais.pdf'), None)
    corrige_francais = next((f for f in files if f['name'] == 'corrige_francais.pdf'), None)
    sujet_maths = next((f for f in files if f['name'] == 'sujet_maths.pdf'), None)
    corrige_maths = next((f for f in files if f['name'] == 'corrige_maths.pdf'), None)
    
    # Trouver un admin pour le champ createur
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        print("❌ Aucun utilisateur admin trouvé pour créer les examens")
        return []
    
    exams_data = [
        {
            'titre': 'Composition Française - Test Local',
            'description': 'Composition argumentative sur la technologie',
            'matiere': subjects[0],  # Français
            'duree_minutes': 120,
            'note_maximale': 20,
            'sujet': sujet_francais,
            'corrige': corrige_francais
        },
        {
            'titre': 'Examen Mathématiques - Test Local',
            'description': 'Exercices de mathématiques variés',
            'matiere': subjects[1],  # Mathématiques
            'duree_minutes': 60,
            'note_maximale': 20,
            'sujet': sujet_maths,
            'corrige': corrige_maths
        }
    ]
    
    created_exams = []
    
    for exam_data in exams_data:
        try:
            now = timezone.now()
            exam, created = Exam.objects.get_or_create(
                titre=exam_data['titre'],
                defaults={
                    'description': exam_data['description'],
                    'matiere': exam_data['matiere'],
                    'duree_minutes': exam_data['duree_minutes'],
                    'note_maximale': exam_data['note_maximale'],
                    'date_debut': now,
                    'date_fin': now + timezone.timedelta(hours=2),
                    'createur': admin_user,
                    'statut': 'publie',
                    'approval_status': 'approved',
                    'est_public': True
                }
            )
            
            # Ajouter les fichiers
            if exam_data['sujet']:
                exam.files.create(
                    fichier=exam_data['sujet']['file'],
                    nom_original=exam_data['sujet']['name'],
                    type_fichier='sujet'
                )
            
            if exam_data['corrige']:
                exam.files.create(
                    fichier=exam_data['corrige']['file'],
                    nom_original=exam_data['corrige']['name'],
                    type_fichier='corrige_type'
                )
            
            if created:
                print(f"✅ Examen créé: {exam.titre}")
            else:
                print(f"✅ Examen existant: {exam.titre}")
            
            created_exams.append(exam)
            
        except Exception as e:
            print(f"❌ Erreur création examen {exam_data['titre']}: {e}")
    
    return created_exams

def create_test_sessions(users, exams):
    """Crée les sessions de test"""
    print("\n🎯 CRÉATION DES SESSIONS")
    
    # Trouver les élèves
    students = [u for u in users if not u.is_staff]
    
    sessions_data = []
    
    for student in students:
        for exam in exams:
            sessions_data.append({
                'student': student,
                'exam': exam
            })
    
    created_sessions = []
    
    for session_data in sessions_data:
        try:
            session, created = CompositionSession.objects.get_or_create(
                exam=session_data['exam'],
                eleve=session_data['student'],
                defaults={
                    'mode': 'en_ligne',
                    'statut': 'en_attente',
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Test Local Environment'
                }
            )
            
            if created:
                print(f"✅ Session créée: {session.eleve.email} - {session.exam.titre}")
            else:
                print(f"✅ Session existante: {session.eleve.email} - {session.exam.titre}")
            
            created_sessions.append(session)
            
        except Exception as e:
            print(f"❌ Erreur création session: {e}")
    
    return created_sessions

def main():
    """Fonction principale"""
    print("🚀 CRÉATION AUTOMATIQUE DES DONNÉES DE TEST")
    print("=" * 50)
    
    # 1. Créer les utilisateurs
    users = create_test_users()
    
    # 2. Créer les matières
    subjects = create_test_subjects()
    
    # 3. Créer les fichiers
    files = create_test_files()
    
    # 4. Créer les examens
    exams = create_test_exams(subjects, files)
    
    # 5. Créer les sessions
    sessions = create_test_sessions(users, exams)
    
    print("\n🎉 DONNÉES DE TEST CRÉÉES AVEC SUCCÈS!")
    print("\n📋 RÉCAPITULATIF:")
    print(f"   Utilisateurs: {len(users)}")
    print(f"   Matières: {len(subjects)}")
    print(f"   Examens: {len(exams)}")
    print(f"   Sessions: {len(sessions)}")
    
    print("\n🔑 COMPTES UTILISATEURS:")
    for user in users:
        if user.is_staff:
            print(f"   ADMIN: {user.email} | mot de passe: Admin123456!")
        else:
            print(f"   ÉLÈVE: {user.email} | mot de passe: Test123456! | classe: {user.classe}")
    
    print("\n📝 SESSIONS DISPONIBLES:")
    for session in sessions:
        print(f"   {session.exam.titre} - {session.eleve.email}")
        print(f"   URL: http://127.0.0.1:5600/compositions/room/{session.id}/")
    
    print("\n🚀 PROCHAINES ÉTAPES:")
    print("1. Démarrer le serveur: python manage.py runserver 5600")
    print("2. Se connecter avec un compte élève")
    print("3. Accéder à une session de composition")
    print("4. Tester le flux complet")
    
    print("\n✅ Le système est prêt pour les tests locaux!")

if __name__ == "__main__":
    main()
