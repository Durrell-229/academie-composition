#!/usr/bin/env python
"""
Test complet du flux: inscription → composition → correction → bulletin
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

from django.contrib.auth import get_user_model
from compositions.models import CompositionSession, Resultat, StudentAnswer
from django.test import Client
from django.urls import reverse
import json
import time

User = get_user_model()

class TestFlowRunner:
    """Exécuteur de test du flux complet"""
    
    def __init__(self):
        self.client = Client()
        self.test_user = None
        self.test_session = None
        self.results = {}
    
    def setup_user(self):
        """Configure l'utilisateur de test"""
        print("👤 CONFIGURATION UTILISATEUR")
        
        try:
            # Trouver ou créer l'utilisateur de test
            self.test_user, created = User.objects.get_or_create(
                email='flow.test@ecole.com',
                defaults={
                    'first_name': 'Flow',
                    'last_name': 'Test',
                    'classe': '3ème A'
                }
            )
            
            if created:
                self.test_user.set_password('Test123456!')
                self.test_user.save()
                print("✅ Utilisateur de test créé")
            else:
                print("✅ Utilisateur de test existant")
            
            # Connexion
            login_success = self.client.login(
                email='flow.test@ecole.com',
                password='Test123456!'
            )
            
            if login_success:
                print("✅ Connexion réussie")
                return True
            else:
                print("❌ Échec connexion")
                return False
                
        except Exception as e:
            print(f"❌ Erreur configuration utilisateur: {e}")
            return False
    
    def test_dashboard_access(self):
        """Test l'accès au dashboard"""
        print("\n📊 TEST ACCÈS DASHBOARD")
        
        try:
            response = self.client.get('/dashboard/')
            
            if response.status_code == 200:
                print("✅ Dashboard accessible")
                self.results['dashboard'] = 'PASS'
                return True
            else:
                print(f"❌ Dashboard inaccessible: {response.status_code}")
                self.results['dashboard'] = f'FAIL ({response.status_code})'
                return False
                
        except Exception as e:
            print(f"❌ Erreur dashboard: {e}")
            self.results['dashboard'] = f'ERROR ({e})'
            return False
    
    def test_composition_list(self):
        """Test l'accès à la liste des compositions"""
        print("\n📝 TEST LISTE COMPOSITIONS")
        
        try:
            response = self.client.get('/compositions/')
            
            if response.status_code == 200:
                print("✅ Liste compositions accessible")
                self.results['compositions_list'] = 'PASS'
                return True
            else:
                print(f"❌ Liste compositions inaccessible: {response.status_code}")
                self.results['compositions_list'] = f'FAIL ({response.status_code})'
                return False
                
        except Exception as e:
            print(f"❌ Erreur liste compositions: {e}")
            self.results['compositions_list'] = f'ERROR ({e})'
            return False
    
    def test_session_creation(self):
        """Test la création d'une session"""
        print("\n🎯 TEST CRÉATION SESSION")
        
        try:
            # Trouver un examen disponible
            from exams.models import Exam
            exam = Exam.objects.filter(is_active=True).first()
            
            if not exam:
                print("❌ Aucun examen actif trouvé")
                self.results['session_creation'] = 'FAIL (no exam)'
                return False
            
            # Créer ou trouver une session
            self.test_session, created = CompositionSession.objects.get_or_create(
                exam=exam,
                eleve=self.test_user,
                defaults={
                    'mode': 'en_ligne',
                    'statut': 'en_attente',
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Test Flow Runner'
                }
            )
            
            if created:
                print(f"✅ Session créée: {exam.titre}")
            else:
                print(f"✅ Session existante: {exam.titre}")
            
            self.results['session_creation'] = 'PASS'
            return True
            
        except Exception as e:
            print(f"❌ Erreur création session: {e}")
            self.results['session_creation'] = f'ERROR ({e})'
            return False
    
    def test_composition_room(self):
        """Test l'accès à la salle de composition"""
        print("\n🏠 TEST ACCÈS SALLE DE COMPOSITION")
        
        if not self.test_session:
            print("❌ Pas de session disponible")
            return False
        
        try:
            response = self.client.get(f'/compositions/room/{self.test_session.id}/')
            
            if response.status_code == 200:
                print("✅ Salle de composition accessible")
                
                # Vérifier les éléments essentiels
                content = response.content.decode()
                essentials = [
                    'webcam',  # Caméra
                    'exam-timer',  # Timer
                    'composition-textarea',  # Zone de réponse
                    'submit-modal'  # Modal de soumission
                ]
                
                missing_essentials = []
                for essential in essentials:
                    if essential not in content:
                        missing_essentials.append(essential)
                
                if missing_essentials:
                    print(f"⚠️ Éléments manquants: {missing_essentials}")
                    self.results['composition_room'] = f'PARTIAL (missing: {missing_essentials})'
                else:
                    print("✅ Tous les éléments essentiels présents")
                    self.results['composition_room'] = 'PASS'
                
                return True
            else:
                print(f"❌ Salle de composition inaccessible: {response.status_code}")
                self.results['composition_room'] = f'FAIL ({response.status_code})'
                return False
                
        except Exception as e:
            print(f"❌ Erreur salle de composition: {e}")
            self.results['composition_room'] = f'ERROR ({e})'
            return False
    
    def test_submission(self):
        """Test la soumission d'une composition"""
        print("\n📤 TEST SOUMISSION COMPOSITION")
        
        if not self.test_session:
            print("❌ Pas de session disponible")
            return False
        
        try:
            # Démarrer la session
            self.test_session.start()
            print("✅ Session démarrée")
            
            # Créer une réponse de test
            test_answer = """
            Test de composition pour validation du flux:
            
            La technologie a transformé notre société de manière profonde.
            D'un côté, elle nous a rapprochés grâce aux communications instantanées
            et à l'accès à l'information. De l'autre, elle peut créer une forme
            d'isolement si elle n'est pas utilisée de manière équilibrée.
            
            En conclusion, la technologie est un outil puissant qui nécessite
            une utilisation réfléchie et modérée.
            """.strip()
            
            # Soumettre la réponse
            response = self.client.post(
                f'/compositions/api/submit-from-room/',
                {
                    'session_id': str(self.test_session.id),
                    'reponse_texte': test_answer,
                    'csrfmiddlewaretoken': self.client.cookies['csrftoken'].value
                }
            )
            
            if response.status_code == 200:
                result = json.loads(response.content)
                if result.get('success'):
                    print("✅ Soumission réussie")
                    self.results['submission'] = 'PASS'
                    return True
                else:
                    print(f"❌ Soumission échouée: {result.get('error')}")
                    self.results['submission'] = f'FAIL ({result.get("error")})'
                    return False
            else:
                print(f"❌ Erreur soumission: {response.status_code}")
                self.results['submission'] = f'FAIL ({response.status_code})'
                return False
                
        except Exception as e:
            print(f"❌ Erreur soumission: {e}")
            self.results['submission'] = f'ERROR ({e})'
            return False
    
    def test_correction_process(self):
        """Test le processus de correction"""
        print("\n🤖 TEST PROCESSUS CORRECTION")
        
        if not self.test_session:
            print("❌ Pas de session disponible")
            return False
        
        try:
            # Vérifier que la session est soumise
            if self.test_session.statut != 'soumis':
                print("❌ Session non soumise")
                self.results['correction'] = 'FAIL (not submitted)'
                return False
            
            # Lancer la correction manuellement
            from compositions.tasks import process_ia_correction
            
            print("🚀 Lancement correction IA...")
            result = process_ia_correction(str(self.test_session.id))
            
            print(f"✅ Correction terminée: {result}")
            
            # Vérifier le résultat
            try:
                resultat = Resultat.objects.get(session=self.test_session)
                print(f"✅ Résultat créé: {resultat.note}/{resultat.note_sur}")
                
                if resultat.bulletin_pdf:
                    print("✅ Bulletin PDF généré")
                    self.results['correction'] = 'PASS'
                    return True
                else:
                    print("❌ Bulletin PDF non généré")
                    self.results['correction'] = 'PARTIAL (no bulletin)'
                    return False
                    
            except Resultat.DoesNotExist:
                print("❌ Pas de résultat créé")
                self.results['correction'] = 'FAIL (no result)'
                return False
                
        except Exception as e:
            print(f"❌ Erreur correction: {e}")
            self.results['correction'] = f'ERROR ({e})'
            return False
    
    def test_result_access(self):
        """Test l'accès aux résultats"""
        print("\n📊 TEST ACCÈS RÉSULTATS")
        
        if not self.test_session:
            print("❌ Pas de session disponible")
            return False
        
        try:
            response = self.client.get(f'/compositions/result/{self.test_session.id}/')
            
            if response.status_code == 200:
                print("✅ Page résultats accessible")
                
                # Vérifier les éléments de résultat
                content = response.content.decode()
                result_elements = [
                    'note',
                    'mention',
                    'appreciation'
                ]
                
                missing_elements = []
                for element in result_elements:
                    if element not in content:
                        missing_elements.append(element)
                
                if missing_elements:
                    print(f"⚠️ Éléments manquants: {missing_elements}")
                    self.results['result_access'] = f'PARTIAL (missing: {missing_elements})'
                else:
                    print("✅ Tous les éléments de résultat présents")
                    self.results['result_access'] = 'PASS'
                
                return True
            else:
                print(f"❌ Page résultats inaccessible: {response.status_code}")
                self.results['result_access'] = f'FAIL ({response.status_code})'
                return False
                
        except Exception as e:
            print(f"❌ Erreur accès résultats: {e}")
            self.results['result_access'] = f'ERROR ({e})'
            return False
    
    def test_bulletin_download(self):
        """Test le téléchargement du bulletin"""
        print("\n📄 TEST TÉLÉCHARGEMENT BULLETIN")
        
        if not self.test_session:
            print("❌ Pas de session disponible")
            return False
        
        try:
            # Trouver le résultat
            try:
                resultat = Resultat.objects.get(session=self.test_session)
                
                if not resultat.bulletin_pdf:
                    print("❌ Pas de bulletin PDF")
                    self.results['bulletin_download'] = 'FAIL (no bulletin)'
                    return False
                
                response = self.client.get(f'/compositions/bulletin/{resultat.id}/')
                
                if response.status_code == 200:
                    print("✅ Bulletin téléchargeable")
                    self.results['bulletin_download'] = 'PASS'
                    return True
                else:
                    print(f"❌ Bulletin non téléchargeable: {response.status_code}")
                    self.results['bulletin_download'] = f'FAIL ({response.status_code})'
                    return False
                    
            except Resultat.DoesNotExist:
                print("❌ Pas de résultat trouvé")
                self.results['bulletin_download'] = 'FAIL (no result)'
                return False
                
        except Exception as e:
            print(f"❌ Erreur bulletin: {e}")
            self.results['bulletin_download'] = f'ERROR ({e})'
            return False
    
    def run_full_test(self):
        """Exécute le test complet"""
        print("🚀 DÉMARRAGE DU TEST COMPLET DU FLUX")
        print("=" * 50)
        
        tests = [
            ('Configuration utilisateur', self.setup_user),
            ('Accès dashboard', self.test_dashboard_access),
            ('Liste compositions', self.test_composition_list),
            ('Création session', self.test_session_creation),
            ('Salle composition', self.test_composition_room),
            ('Soumission', self.test_submission),
            ('Correction IA', self.test_correction_process),
            ('Accès résultats', self.test_result_access),
            ('Bulletin PDF', self.test_bulletin_download)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Erreur inattendue: {e}")
                failed += 1
                self.results[test_name] = f'CRASH ({e})'
        
        self.print_summary(passed, failed)
        return failed == 0
    
    def print_summary(self, passed, failed):
        """Affiche le résumé des tests"""
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DES TESTS")
        print("="*60)
        
        print(f"✅ Tests réussis: {passed}")
        print(f"❌ Tests échoués: {failed}")
        print(f"📈 Taux de réussite: {(passed/(passed+failed)*100):.1f}%")
        
        print("\n📋 DÉTAILS:")
        for test_name, result in self.results.items():
            status = "✅" if result == 'PASS' else "❌" if result.startswith('FAIL') else "⚠️"
            print(f"   {status} {test_name}: {result}")
        
        if failed == 0:
            print("\n🎉 TOUS LES TESTS RÉUSSIS!")
            print("✅ Le système est prêt pour la production")
        else:
            print(f"\n⚠️ {failed} test(s) échoué(s)")
            print("🔧 Veuillez corriger les problèmes avant la production")

def main():
    """Fonction principale"""
    print("🧪 TEST COMPLET DU FLUX ACADÉMIE NUMÉRIQUE")
    print("=" * 60)
    
    runner = TestFlowRunner()
    success = runner.run_full_test()
    
    if success:
        print("\n🚀 SYSTÈME 100% FONCTIONNEL!")
        print("\n📋 PROCHAINES ÉTAPES:")
        print("1. ✅ Tests locaux validés")
        print("2. 🔄 Tests multi-utilisateurs")
        print("3. 🌐 Tests de charge")
        print("4. 🚀 Déploiement production")
    else:
        print("\n🔧 ACTION REQUISE:")
        print("1. Corriger les tests échoués")
        print("2. Relancer les tests")
        print("3. Valider avant déploiement")

if __name__ == "__main__":
    main()
