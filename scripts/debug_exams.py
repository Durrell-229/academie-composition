#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def debug_exams_system():
    """Diagnostic complet du système d'examens et compositions"""
    print("🔍 DIAGNOSTIC SYSTÈME D'EXAMENS ET COMPOSITIONS")
    print("=" * 70)
    
    tests = []
    
    # Test 1: Vérification des modèles Exam
    try:
        from exams.models import Exam, ExamFile, ExamAssignment
        from core.models import Matiere, Classe
        
        # Compter les objets existants
        exam_count = Exam.objects.count()
        matiere_count = Matiere.objects.count()
        classe_count = Classe.objects.count()
        
        tests.append(("✅ Modèles Exam", f"{exam_count} examens, {matiere_count} matières, {classe_count} classes"))
        
        # Vérifier les examens existants
        if exam_count > 0:
            sample_exam = Exam.objects.first()
            tests.append(("✅ Exemple examen", f"'{sample_exam.titre}' - Statut: {sample_exam.statut}"))
        else:
            tests.append(("⚠️ Examen exemple", "Aucun examen existant"))
            
    except Exception as e:
        tests.append(("❌ Modèles Exam", str(e)))
    
    # Test 2: Vérifier les élèves et leurs classes
    try:
        from accounts.models import User
        
        eleves = User.objects.filter(role='eleve')
        eleves_sans_classe = eleves.filter(classe__isnull=True).count()
        eleves_avec_classe = eleves.filter(classe__isnull=False).count()
        
        tests.append(("✅ Élèves", f"{eleves.count()} total, {eleves_avec_classe} avec classe, {eleves_sans_classe} sans classe"))
        
        # Vérifier les classes des élèves
        if eleves_avec_classe > 0:
            sample_eleve = User.objects.filter(role='eleve', classe__isnull=False).first()
            tests.append(("✅ Élève exemple", f"{sample_eleve.email} - Classe: {sample_eleve.classe}"))
        
    except Exception as e:
        tests.append(("❌ Vérification élèves", str(e)))
    
    # Test 3: Vérifier la logique de filtrage des examens pour les élèves
    try:
        from accounts.models import User
        from exams.models import Exam
        from django.utils import timezone
        
        # Simuler la vue exam_list_view pour un élève
        eleve = User.objects.filter(role='eleve', classe__isnull=False).first()
        
        if eleve:
            # Logique exacte de la vue
            exams_visibles = Exam.objects.filter(
                classe__nom=eleve.classe,
                statut__in=['publie', 'en_cours']
            ).distinct() if eleve.classe else Exam.objects.none()
            
            exams_tous = Exam.objects.all()
            
            tests.append(("✅ Filtrage examens élève", f"{exams_visibles.count()} visibles sur {exams_tous.count()} total"))
            
            # Détail des examens visibles
            for exam in exams_visibles[:3]:
                tests.append(("  📋 Examen visible", f"'{exam.titre}' - {exam.matiere.nom if exam.matiere else 'N/A'}"))
        else:
            tests.append(("⚠️ Filtrage examens", "Aucun élève avec classe trouvé"))
            
    except Exception as e:
        tests.append(("❌ Filtrage examens", str(e)))
    
    # Test 4: Vérifier les assignments d'examens
    try:
        from exams.models import ExamAssignment
        
        assignments = ExamAssignment.objects.all()
        assignments_count = assignments.count()
        
        tests.append(("✅ Assignments examens", f"{assignments_count} assignments"))
        
        # Vérifier si les élèves ont des assignments
        if assignments_count > 0:
            for assignment in assignments[:3]:
                tests.append(("  📝 Assignment", f"Élève: {assignment.eleve.email if assignment.eleve else 'Classe'} - Examen: {assignment.exam.titre}"))
        
    except Exception as e:
        tests.append(("❌ Assignments", str(e)))
    
    # Test 5: Vérifier les vues de composition
    try:
        from compositions.views import composition_room_view, submit_paper_view
        from compositions.models import CompositionSession
        
        sessions = CompositionSession.objects.all()
        sessions_count = sessions.count()
        
        tests.append(("✅ Sessions composition", f"{sessions_count} sessions"))
        
        # État des sessions
        if sessions_count > 0:
            en_attente = sessions.filter(statut='en_attente').count()
            en_cours = sessions.filter(statut='en_cours').count()
            soumis = sessions.filter(statut='soumis').count()
            
            tests.append(("  📊 Stats sessions", f"En attente: {en_attente}, En cours: {en_cours}, Soumis: {soumis}"))
        
    except Exception as e:
        tests.append(("❌ Sessions composition", str(e)))
    
    # Test 6: Vérifier les fichiers d'examens
    try:
        from exams.models import ExamFile
        
        files = ExamFile.objects.all()
        files_count = files.count()
        
        epreuves = files.filter(type_fichier='epreuve').count()
        corriges = files.filter(type_fichier='corrige_type').count()
        
        tests.append(("✅ Fichiers examens", f"{files_count} total: {epreuves} épreuves, {corriges} corrigés"))
        
    except Exception as e:
        tests.append(("❌ Fichiers examens", str(e)))
    
    # Test 7: Vérifier les URLs
    try:
        from django.urls import reverse
        
        exam_list_url = reverse('exam_list')
        exam_create_url = reverse('exam_create')
        composition_room_url = reverse('composition_room', args=['test-id'])
        
        tests.append(("✅ URLs", f"Liste: {exam_list_url}, Créer: {exam_create_url}"))
        
    except Exception as e:
        tests.append(("❌ URLs", str(e)))
    
    # Test 8: Vérifier les templates
    try:
        from django.template.loader import get_template
        
        templates_to_check = [
            'exams/exam_list.html',
            'exams/exam_form.html',
            'exams/exam_detail.html',
            'compositions/room.html',
            'compositions/submit_paper.html'
        ]
        
        for template in templates_to_check:
            try:
                get_template(template)
                tests.append((f"✅ Template {template}", "Trouvé"))
            except Exception:
                tests.append((f"❌ Template {template}", "Manquant"))
                
    except Exception as e:
        tests.append(("❌ Templates", str(e)))
    
    # Affichage des résultats
    for test, result in tests:
        print(f"{test}: {result}")
    
    # Compte des erreurs
    errors = [test for test in tests if isinstance(test[1], str) and test[1].startswith('❌')]
    warnings = [test for test in tests if isinstance(test[1], str) and test[1].startswith('⚠️')]
    
    print(f"\n📊 RÉSULTAT: {len(tests) - len(errors)}/{len(tests)} tests OK")
    if warnings:
        print(f"⚠️ AVERTISSEMENTS: {len(warnings)}")
    
    if errors:
        print("\n❌ ERREURS DÉTECTÉES:")
        for test, error in errors:
            print(f"  - {test}: {error}")
    
    return len(errors) == 0

if __name__ == "__main__":
    debug_exams_system()
