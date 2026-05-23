#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def create_test_exam():
    """Créer un examen de test complet avec tous les éléments nécessaires"""
    print("🔧 CRÉATION D'EXAMEN DE TEST COMPLET")
    print("=" * 50)
    
    try:
        from exams.models import Exam, ExamFile, ExamAssignment
        from core.models import Matiere, Classe
        from accounts.models import User
        from django.utils import timezone
        from datetime import timedelta
        from django.core.files.base import ContentFile
        
        # 1. Trouver ou créer les éléments nécessaires
        print("📋 Recherche des éléments nécessaires...")
        
        # Matière
        matiere = Matiere.objects.filter(nom='Mathématiques').first()
        if not matiere:
            matiere = Matiere.objects.create(
                nom='Mathématiques',
                code='MATH',
                description='Mathématiques',
                is_active=True
            )
            print(f"✅ Matière créée: {matiere.nom}")
        
        # Classe
        classe = Classe.objects.filter(nom='Terminale S1').first()
        if not classe:
            classe = Classe.objects.create(
                nom='Terminale S1',
                niveau='Secondaire',
                is_active=True
            )
            print(f"✅ Classe créée: {classe.nom}")
        
        # Professeur
        prof = User.objects.filter(role='professeur').first()
        if not prof:
            prof = User.objects.create_user(
                email='prof@test.com',
                password='testpass123',
                first_name='Professeur',
                last_name='Test',
                role='professeur'
            )
            print(f"✅ Professeur créé: {prof.email}")
        
        # Élèves
        eleves = User.objects.filter(role='eleve', classe__isnull=True)
        for eleve in eleves[:2]:
            eleve.classe = classe.nom
            eleve.save()
            print(f"✅ Élève {eleve.email} assigné à la classe {classe.nom}")
        
        # 2. Créer l'examen
        print("\n📝 Création de l'examen...")
        
        now = timezone.now()
        exam = Exam.objects.create(
            titre='Composition de Mathématiques - Test',
            description='Examen de test pour vérifier le fonctionnement complet du système',
            type_exam='composition',
            matiere=matiere,
            classe=classe,
            createur=prof,
            duree_minutes=120,
            date_debut=now,
            date_fin=now + timedelta(minutes=120),
            note_maximale=20,
            coefficient=1,
            statut='en_cours',  # Directement en cours pour les tests
            est_public=True,
            approval_status='approved'
        )
        
        print(f"✅ Examen créé: {exam.titre}")
        print(f"   - ID: {exam.id}")
        print(f"   - Matière: {exam.matiere.nom}")
        print(f"   - Classe: {exam.classe.nom}")
        print(f"   - Statut: {exam.statut}")
        
        # 3. Créer des fichiers d'examen (fichiers PDF factices)
        print("\n📄 Création des fichiers d'examen...")
        
        # Épreuve
        epreuve_content = """%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Epreuve de Mathematiques) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000349 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
423
%%EOF""".encode('utf-8')
        
        epreuve_file = ExamFile.objects.create(
            exam=exam,
            type_fichier='epreuve',
            fichier=ContentFile(epreuve_content, name='epreuve_test.pdf'),
            nom_original='epreuve_mathematiques.pdf'
        )
        print(f"✅ Fichier épreuve créé: {epreuve_file.nom_original}")
        
        # Corrigé type
        corrige_content = """%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 48
>>
stream
BT
/F1 12 Tf
72 720 Td
(Corrige Type Mathematiques) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000349 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
423
%%EOF""".encode('utf-8')
        
        corrige_file = ExamFile.objects.create(
            exam=exam,
            type_fichier='corrige_type',
            fichier=ContentFile(corrige_content, name='corrige_test.pdf'),
            nom_original='corrige_mathematiques.pdf'
        )
        print(f"✅ Fichier corrigé créé: {corrige_file.nom_original}")
        
        # 4. Créer les assignments pour les élèves
        print("\n👥 Création des assignments pour les élèves...")
        
        eleves_classe = User.objects.filter(role='eleve', classe=classe.nom)
        assignments_created = 0
        
        for eleve in eleves_classe:
            assignment, created = ExamAssignment.objects.get_or_create(
                exam=exam,
                eleve=eleve,
                defaults={'date_assignation': now}
            )
            if created:
                assignments_created += 1
                print(f"✅ Assignment créé pour: {eleve.email}")
        
        print(f"📊 Total assignments créés: {assignments_created}")
        
        # 5. Vérifier que les élèves peuvent voir l'examen
        print("\n🔍 Vérification de la visibilité pour les élèves...")
        
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
        
        print("\n🎉 EXAMEN DE TEST CRÉÉ AVEC SUCCÈS!")
        print(f"📋 ID de l'examen: {exam.id}")
        print(f"🔗 URL composition: /accounts/composition/{exam.id}/")
        print(f"👥 Élèves concernés: {eleves_classe.count()}")
        
        return exam.id
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    exam_id = create_test_exam()
    if exam_id:
        print(f"\n✨ Vous pouvez maintenant tester avec l'ID d'examen: {exam_id}")
    else:
        print("\n❌ Échec de la création de l'examen de test")
