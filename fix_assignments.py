#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def fix_student_assignments():
    """Corriger l'assignation des élèves à la classe et créer les assignments"""
    print("🔧 CORRECTION DES ASSIGNATIONS ÉLÈVES")
    print("=" * 50)
    
    try:
        from accounts.models import User
        from exams.models import Exam, ExamAssignment
        from django.utils import timezone
        
        # 1. Assigner les élèves à la classe Terminale S1
        print("📚 Assignation des élèves à la classe...")
        
        eleves = User.objects.filter(role='eleve')
        classe_nom = 'Terminale S1'
        
        for eleve in eleves:
            if not eleve.classe:
                eleve.classe = classe_nom
                eleve.save()
                print(f"✅ {eleve.email} assigné à {classe_nom}")
        
        # 2. Créer les assignments pour l'examen existant
        print("\n📝 Création des assignments d'examen...")
        
        exam = Exam.objects.filter(titre__contains='Mathématiques').first()
        if not exam:
            print("❌ Aucun examen trouvé")
            return False
        
        print(f"📋 Examen trouvé: {exam.titre} (ID: {exam.id})")
        
        eleves_classe = User.objects.filter(role='eleve', classe=classe_nom)
        assignments_created = 0
        
        for eleve in eleves_classe:
            assignment, created = ExamAssignment.objects.get_or_create(
                exam=exam,
                eleve=eleve
            )
            if created:
                assignments_created += 1
                print(f"✅ Assignment créé pour: {eleve.email}")
        
        print(f"📊 Total assignments créés: {assignments_created}")
        
        # 3. Vérifier que les élèves peuvent voir l'examen
        print("\n🔍 Vérification de la visibilité...")
        
        for eleve in eleves_classe:
            # Logique exacte de la vue exam_list_view
            exams_visibles = Exam.objects.filter(
                classe__nom=eleve.classe,
                statut__in=['publie', 'en_cours']
            ).distinct() if eleve.classe else Exam.objects.none()
            
            if exam in exams_visibles:
                print(f"✅ {eleve.email} peut voir l'examen")
            else:
                print(f"❌ {eleve.email} ne peut PAS voir l'examen")
        
        # 4. Tester la room de composition
        print("\n🏠 Test de la room de composition...")
        
        from compositions.views import composition_room_view
        from django.test import RequestFactory
        
        factory = RequestFactory()
        test_eleve = eleves_classe.first()
        
        if test_eleve:
            request = factory.get(f'/accounts/composition/{exam.id}/')
            request.user = test_eleve
            request.META = {
                'REMOTE_ADDR': '127.0.0.1',
                'HTTP_USER_AGENT': 'Test Browser'
            }
            
            try:
                response = composition_room_view(request, exam.id)
                print(f"✅ Room accessible pour {test_eleve.email}")
                print(f"📄 Template: {response.template_name}")
            except Exception as e:
                print(f"❌ Erreur room: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_student_assignments()
    if success:
        print("\n🎉 ASSIGNATIONS CORRIGÉES AVEC SUCCÈS!")
    else:
        print("\n❌ ÉCHEC DE LA CORRECTION")
