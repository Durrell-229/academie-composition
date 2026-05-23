#!/usr/bin/env python
"""
Débogage complet du processus de soumission des élèves
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

from django.contrib.auth import get_user_model
from compositions.models import CompositionSession, StudentSubmissionFile, StudentAnswer, Resultat
from django.test import Client
from django.test import TestCase
import json

User = get_user_model()

def debug_student_submission_flow():
    """Débogue le flux complet de soumission étudiant"""
    print("🔍 DÉBOGAGE SOUMISSION ÉLÈVE")
    print("=" * 40)
    
    # 1. Trouver un élève test
    student = User.objects.filter(is_staff=False).first()
    if not student:
        print("❌ Aucun élève trouvé")
        return False
    
    print(f"✅ Élève trouvé: {student.email}")
    
    # 2. Trouver une session en cours
    session = CompositionSession.objects.filter(
        eleve=student,
        statut='en_cours'
    ).first()
    
    if not session:
        print("❌ Aucune session en cours trouvée")
        # Créer une session de test
        from exams.models import Exam
        exam = Exam.objects.first()
        if exam:
            session, created = CompositionSession.objects.get_or_create(
                exam=exam,
                eleve=student,
                defaults={
                    'mode': 'en_ligne',
                    'statut': 'en_cours',
                    'ip_address': '127.0.0.1'
                }
            )
            if created:
                print(f"✅ Session de test créée: {exam.titre}")
            else:
                print(f"✅ Session existante: {exam.titre}")
        else:
            print("❌ Aucun examen trouvé")
            return False
    
    print(f"📝 Session: {session.exam.titre}")
    print(f"   Statut: {session.statut}")
    print(f"   ID: {session.id}")
    
    # 3. Vérifier les fichiers et réponses existants
    files = session.submission_files.all()
    answers = session.answers.all()
    
    print(f"📁 Fichiers existants: {files.count()}")
    for f in files:
        print(f"   - {f.fichier.name} (Page {f.page_number})")
    
    print(f"✍️ Réponses existantes: {answers.count()}")
    for a in answers:
        print(f"   - Question {a.question_number}: {len(a.content)} caractères")
    
    # 4. Tester la soumission via API
    print("\n🧪 TEST SOUMISSION API")
    
    client = Client()
    
    # Connexion élève
    login_success = client.login(email=student.email, password='Test123456!')
    print(f"Connexion élève: {'✅ Succès' if login_success else '❌ Échec'}")
    
    if login_success:
        # Test soumission avec texte
        test_text = """
        Test de composition pour validation du système:
        
        La technologie moderne a transformé notre façon de vivre et de travailler. 
        Les ordinateurs et internet ont rendu l'information accessible à tous,
        mais cette facilité comporte aussi des risques pour la vie privée et 
        la concentration. Il faut trouver un équilibre entre les avantages 
        technologiques et les besoins humains fondamentaux.
        """.strip()
        
        # Créer un fichier test
        from django.core.files.uploadedfile import SimpleUploadedFile
        test_file = SimpleUploadedFile(
            "test_copy.jpg", 
            b"fake image content for testing", 
            content_type="image/jpeg"
        )
        
        # Soumettre via API
        response = client.post(
            '/compositions/api/submit-from-room/',
            {
                'session_id': str(session.id),
                'reponse_texte': test_text,
                'copies': [test_file]
            }
        )
        
        print(f"Réponse API: {response.status_code}")
        
        if response.status_code == 200:
            result = json.loads(response.content)
            print(f"✅ Soumission réussie: {result.get('message')}")
            
            # Vérifier que les données ont été sauvegardées
            session = CompositionSession.objects.get(id=session.id)
            print(f"   Statut session: {session.statut}")
            
            new_files = session.submission_files.all()
            new_answers = session.answers.all()
            
            print(f"   Fichiers après soumission: {new_files.count()}")
            print(f"   Réponses après soumission: {new_answers.count()}")
            
            return True
        else:
            print(f"❌ Erreur soumission: {response.status_code}")
            try:
                error_data = json.loads(response.content)
                print(f"   Message: {error_data.get('error')}")
            except:
                print(f"   Content: {response.content[:200]}")
            return False
    
    return False

def check_submit_view():
    """Vérifie la vue de soumission classique"""
    print("\n🔍 VÉRIFICATION VUE SOUMISSION CLASSIQUE")
    print("=" * 40)
    
    # Vérifier la vue submit_paper_view
    try:
        from compositions.views import submit_paper_view
        print("✅ Vue submit_paper_view importée")
        
        # Vérifier les URLs
        from django.urls import reverse
        try:
            url = reverse('submit_paper', kwargs={'session_id': 'test-id'})
            print(f"✅ URL submit_paper: {url}")
        except Exception as e:
            print(f"❌ Erreur URL: {e}")
        
    except Exception as e:
        print(f"❌ Erreur vue: {e}")

def check_api_endpoint():
    """Vérifie l'endpoint API de soumission"""
    print("\n🔍 VÉRIFICATION ENDPOINT API")
    print("=" * 30)
    
    try:
        from compositions.views import submit_from_room
        print("✅ Vue submit_from_room importée")
        
        # Vérifier les URLs
        from django.urls import reverse
        try:
            url = reverse('submit_from_room')
            print(f"✅ URL API: {url}")
        except Exception as e:
            print(f"❌ Erreur URL API: {e}")
        
    except Exception as e:
        print(f"❌ Erreur API: {e}")

def check_form_structure():
    """Vérifie la structure du formulaire dans room.html"""
    print("\n🔍 VÉRIFICATION FORMULAIRE ROOM.HTML")
    print("=" * 35)
    
    try:
        # Lire le template
        template_path = 'templates/compositions/room.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier les éléments essentiels
        checks = [
            ('form', 'Formulaire'),
            ('name="copies"', 'Input fichiers'),
            ('name="reponse_texte"', 'Textarea réponse'),
            ('onclick="confirmSubmit()"', 'Bouton soumission'),
            ('submitForm()', 'Fonction soumission'),
            ('csrfmiddlewaretoken', 'Token CSRF')
        ]
        
        for check, description in checks:
            if check in content:
                print(f"✅ {description}: Présent")
            else:
                print(f"❌ {description}: Manquant")
        
        # Vérifier la fonction submitForm
        if 'function submitForm()' in content:
            print("✅ Fonction submitForm: Présente")
            
            # Vérifier si elle utilise form.submit() ou fetch
            if 'form.submit()' in content:
                print("⚠️ submitForm utilise form.submit() (classique)")
            elif 'fetch(' in content:
                print("✅ submitForm utilise fetch (API)")
            else:
                print("❌ submitForm: Méthode non reconnue")
        else:
            print("❌ Fonction submitForm: Absente")
        
    except Exception as e:
        print(f"❌ Erreur lecture template: {e}")

def debug_csrf_token():
    """Débogue les problèmes de token CSRF"""
    print("\n🔍 DÉBOGAGE TOKEN CSRF")
    print("=" * 25)
    
    from django.middleware.csrf import get_token
    from django.http import HttpRequest
    
    request = HttpRequest()
    token = get_token(request)
    print(f"✅ Token CSRF généré: {token[:20]}...")
    
    # Vérifier si le template inclut le token
    try:
        template_path = 'templates/compositions/room.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '{% csrf_token %}' in content:
            print("✅ Token CSRF dans template: Présent")
        else:
            print("❌ Token CSRF dans template: Manquant")
        
        if 'csrfmiddlewaretoken' in content:
            print("✅ Champ csrfmiddlewaretoken: Présent")
        else:
            print("❌ Champ csrfmiddlewaretoken: Manquant")
            
    except Exception as e:
        print(f"❌ Erreur vérification template: {e}")

def main():
    """Fonction principale"""
    print("🚀 DÉBOGAGE COMPLET SOUMISSION ÉLÈVE")
    print("=" * 50)
    
    # Tests principaux
    submission_ok = debug_student_submission_flow()
    check_submit_view()
    check_api_endpoint()
    check_form_structure()
    debug_csrf_token()
    
    print("\n🎯 RÉSULTATS:")
    print(f"Test soumission: {'✅ OK' if submission_ok else '❌ Échec'}")
    
    if not submission_ok:
        print("\n🔧 ACTIONS CORRECTIVES:")
        print("1. Vérifier que l'élève est bien connecté")
        print("2. Vérifier que la session est en cours")
        print("3. Vérifier le token CSRF")
        print("4. Vérifier la fonction submitForm()")
        print("5. Tester avec différents navigateurs")
        
        print("\n📋 POINTS À VÉRIFIER MANUELLEMENT:")
        print("- Ouvrir la console F12 dans la salle de composition")
        print("- Cliquer sur 'Soumettre l'examen'")
        print("- Vérifier les erreurs JavaScript")
        print("- Vérifier les erreurs réseau dans l'onglet Network")
    else:
        print("\n🎉 LA SOUMISSION FONCTIONNE!")
        print("✅ Les élèves peuvent soumettre leurs copies")

if __name__ == "__main__":
    main()
