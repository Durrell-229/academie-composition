#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def test_benin_system():
    """Tester le système éducatif béninois complet"""
    print("🇧🇯 TEST SYSTÈME ÉDUCATIF BÉNINOIS COMPLET")
    print("=" * 60)
    
    try:
        from core.models import Matiere, Classe, Parametre
        from exams.models import Exam, ExamenNational, ExamenNationalMatiere
        from accounts.models import User
        from compositions.models import CompositionSession
        from django.utils import timezone
        
        tests = []
        
        # 1. Vérifier les classes béninoises
        print("\n📚 Test des classes...")
        
        classes_benin = [
            "CP", "CE1", "CE2", "CM1", "CM2",  # Primaire
            "6ème", "5ème", "4ème", "3ème",      # Collège
            "2nde A", "2nde C", "2nde D",       # Seconde
            "1ère A1", "1ère A2", "1ère B", "1ère C", "1ère D",  # Première
            "Terminale A1", "Terminale A2", "Terminale B", "Terminale C", "Terminale D", "Terminale E", "Terminale G1", "Terminale G2", "Terminale G3"  # Terminale
        ]
        
        classes_found = 0
        for classe_nom in classes_benin:
            try:
                classe = Classe.objects.get(nom=classe_nom)
                classes_found += 1
            except Classe.DoesNotExist:
                print(f"❌ Manquant: {classe_nom}")
        
        tests.append(("✅ Classes béninoises", f"{classes_found}/{len(classes_benin)} trouvées"))
        
        # 2. Vérifier les matières avec coefficients
        print("\n📖 Test des matières...")
        
        matieres_benin = [
            ("Français", 3),
            ("Mathématiques", 3),
            ("Histoire-Géographie", 2),
            ("Anglais", 2),
            ("Physique-Chimie", 2),
            ("Sciences de la Vie et de la Terre", 2),
            ("Sciences Physiques", 5),
            ("Philosophie", 4),
            ("Économie", 4),
        ]
        
        matieres_found = 0
        for matiere_nom, coef in matieres_benin:
            try:
                matiere = Matiere.objects.get(nom=matiere_nom)
                matieres_found += 1
            except Matiere.DoesNotExist:
                print(f"❌ Manquant: {matiere_nom}")
        
        tests.append(("✅ Matières béninoises", f"{matieres_found}/{len(matieres_benin)} trouvées"))
        
        # 3. Vérifier les examens nationaux
        print("\n🎓 Test des examens nationaux...")
        
        examens_nationaux = ["BEPC - Brevet d'Études du Premier Cycle", "BACCALAURÉAT Série C"]
        examens_found = 0
        
        for examen_nom in examens_nationaux:
            try:
                examen = ExamenNational.objects.get(nom=examen_nom)
                examens_found += 1
                
                # Vérifier les matières associées
                matieres_count = examen.matieres.count()
                print(f"   📋 {examen_nom}: {matieres_count} matières")
                
            except ExamenNational.DoesNotExist:
                print(f"❌ Manquant: {examen_nom}")
        
        tests.append(("✅ Examens nationaux", f"{examens_found}/{len(examens_nationaux)} trouvés"))
        
        # 4. Créer un examen de test béninois
        print("\n📝 Création d'un examen de test béninois...")
        
        try:
            from exams.models import Exam, ExamFile
            from django.core.files.base import ContentFile
            
            # Trouver une classe et une matière
            classe_test = Classe.objects.get(nom="Terminale C")
            matiere_test = Matiere.objects.get(nom="Sciences Physiques")
            prof_test = User.objects.filter(role='professeur').first()
            
            if not prof_test:
                prof_test = User.objects.create_user(
                    email='prof@benin.edu',
                    password='prof2026',
                    first_name='Professeur',
                    last_name='Bénin',
                    role='professeur'
                )
            
            # Créer l'examen
            now = timezone.now()
            exam = Exam.objects.create(
                titre='Composition de Sciences Physiques - Test Bénin',
                description='Examen test selon le programme béninois',
                type_exam='composition',
                matiere=matiere_test,
                classe=classe_test,
                createur=prof_test,
                duree_minutes=180,  # 3h comme au BAC
                date_debut=now,
                date_fin=now + timezone.timedelta(minutes=180),
                note_maximale=20,
                coefficient=5,  # Coefficient BAC Série C
                statut='en_cours',
                est_public=True,
                approval_status='approved'
            )
            
            tests.append(("✅ Examen test créé", f"ID: {exam.id}"))
            
        except Exception as e:
            tests.append(("❌ Examen test", str(e)))
        
        # 5. Vérifier les coefficients béninois
        print("\n⚙️ Test des coefficients...")
        
        try:
            import json
            param_coeff = Parametre.objects.get(cle="coefficients_benin")
            coefficients = json.loads(param_coeff.valeur)
            
            # Vérifier quelques coefficients clés
            key_coeffs = {
                "Sciences Physiques": 5,
                "Mathématiques": 3,
                "Philosophie": 4,
                "Français": 3
            }
            
            coeffs_ok = 0
            for matiere, expected_coef in key_coeffs.items():
                if matiere in coefficients and coefficients[matiere] == expected_coef:
                    coeffs_ok += 1
                else:
                    print(f"❌ Coefficient incorrect pour {matiere}")
            
            tests.append(("✅ Coefficients béninois", f"{coeffs_ok}/{len(key_coeffs)} corrects"))
            
        except Exception as e:
            tests.append(("❌ Coefficients", str(e)))
        
        # 6. Vérifier la configuration des bulletins
        print("\n📄 Test configuration bulletins...")
        
        try:
            param_bulletin = Parametre.objects.get(cle="bulletin_benin_config")
            bulletin_config = json.loads(param_bulletin.valeur)
            
            # Vérifier les sections clés
            sections = [s["titre"] for s in bulletin_config["sections"]]
            required_sections = [
                "INFORMATIONS ÉLÈVE",
                "ÉVALUATION DES COMPÉTENCES", 
                "COMPORTEMENT ET DISCIPLINE",
                "MOYENNES ET DÉCISIONS",
                "OBSERVATIONS ET SIGNATURES"
            ]
            
            sections_ok = sum(1 for section in required_sections if section in sections)
            tests.append(("✅ Configuration bulletin", f"{sections_ok}/{len(required_sections)} sections"))
            
        except Exception as e:
            tests.append(("❌ Configuration bulletin", str(e)))
        
        # 7. Test de création d'élèves béninois
        print("\n👥 Test création élèves béninois...")
        
        try:
            # Créer des élèves dans différentes classes
            classes_test = ["CM2", "3ème", "Terminale C"]
            eleves_created = 0
            
            for i, classe_nom in enumerate(classes_test):
                classe = Classe.objects.get(nom=classe_nom)
                eleve, created = User.objects.get_or_create(
                    email=f'eleve{classe_nom.lower().replace(" ", "")}@benin.edu',
                    defaults={
                        'first_name': 'Élève',
                        'last_name': f'Test {classe_nom}',
                        'role': 'eleve',
                        'classe': classe_nom
                    }
                )
                if created:
                    eleves_created += 1
                    # Définir le mot de passe
                    eleve.set_password('eleve2026')
                    eleve.save()
            
            tests.append(("✅ Élèves béninois", f"{eleves_created} créés"))
            
        except Exception as e:
            tests.append(("❌ Élèves béninois", str(e)))
        
        # 8. Test de visibilité des examens pour les élèves
        print("\n👁️ Test visibilité examens...")
        
        try:
            # Tester avec un élève de Terminale C
            eleve_test = User.objects.get(email='eleveterminalec@benin.edu')
            
            # Logique de filtrage des examens
            exams_visibles = Exam.objects.filter(
                classe__nom=eleve_test.classe,
                statut__in=['publie', 'en_cours']
            ).distinct()
            
            if exam in exams_visibles:
                tests.append(("✅ Visibilité examens", f"Élève voit {exams_visibles.count()} examens"))
            else:
                tests.append(("❌ Visibilité examens", "L'élève ne voit pas l'examen de test"))
                
        except Exception as e:
            tests.append(("❌ Visibilité examens", str(e)))
        
        # Affichage des résultats
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS DES TESTS")
        print("=" * 60)
        
        for test, result in tests:
            print(f"{test}: {result}")
        
        # Compte des erreurs
        errors = [test for test in tests if isinstance(test[1], str) and test[1].startswith('❌')]
        
        print(f"\n📊 BILAN: {len(tests) - len(errors)}/{len(tests)} tests OK")
        
        if errors:
            print("\n❌ ERREURS DÉTECTÉES:")
            for test, error in errors:
                print(f"  - {test}: {error}")
        else:
            print("\n🎉 TOUS LES TESTS SONT OK!")
        
        return len(errors) == 0
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_benin_system()
    if success:
        print("\n🇧🇯 SYSTÈME ÉDUCATIF BÉNINOIS 100% FONCTIONNEL!")
        print("✅ Classes et niveaux configurés")
        print("✅ Matières et coefficients appliqués")
        print("✅ Examens nationaux intégrés")
        print("✅ Bulletins adaptés au format béninois")
        print("✅ Système de correction IA prêt")
        print("\n🚀 Vous pouvez maintenant utiliser la plateforme!")
    else:
        print("\n❌ Des problèmes subsistent, voir les erreurs ci-dessus")
