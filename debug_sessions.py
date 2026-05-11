#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

from compositions.models import CompositionSession, Resultat
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def check_sessions():
    print("=== DIAGNOSTIC DES SESSIONS DE COMPOSITION ===\n")
    
    sessions = CompositionSession.objects.all().order_by('-created_at')
    print(f"Total sessions: {sessions.count()}\n")
    
    for session in sessions:
        print(f"📝 SESSION: {session.id}")
        print(f"   Examen: {session.exam.titre}")
        print(f"   Élève: {session.eleve.email} ({session.eleve.full_name})")
        print(f"   Statut: {session.statut}")
        print(f"   Créée: {session.created_at}")
        print(f"   Début: {session.started_at}")
        print(f"   Soumission: {session.submitted_at}")
        print(f"   Temps passé: {session.time_spent_seconds} secondes")
        
        # Vérifier les fichiers soumis
        files = session.submission_files.all()
        print(f"   Fichiers: {files.count()} fichier(s)")
        for f in files:
            print(f"     - Page {f.page_number}: {f.fichier.name}")
        
        # Vérifier les réponses texte
        answers = session.answers.all()
        print(f"   Réponses texte: {answers.count()} réponse(s)")
        for a in answers:
            print(f"     - Question {a.question_number}: {len(a.content)} caractères")
        
        # Vérifier le résultat
        try:
            resultat = Resultat.objects.get(session=session)
            print(f"   📊 RÉSULTAT: {resultat.note}/{resultat.note_sur}")
            print(f"   Mention: {resultat.mention}")
            print(f"   Bulletin PDF: {'OUI' if resultat.bulletin_pdf else 'NON'}")
            print(f"   Corrigé par IA: {'OUI' if resultat.corrige_par_ia else 'NON'}")
            print(f"   Date correction: {resultat.corrige_at}")
        except Resultat.DoesNotExist:
            print(f"   ❌ PAS DE RÉSULTAT")
        
        print("\n" + "="*60 + "\n")

def check_redis_tasks():
    print("=== VÉRIFICATION DES TÂCHES REDIS ===\n")
    
    try:
        from core.redis_tasks import get_redis_client
        redis_client = get_redis_client()
        
        # Vérifier les files d'attente
        queues = ['default', 'high_priority', 'low_priority']
        for queue in queues:
            length = redis_client.llen(queue)
            print(f"Queue '{queue}': {length} tâches en attente")
            
            if length > 0:
                print(f"  Première tâche: {redis_client.lindex(queue, 0)}")
        
        print("\n")
    except Exception as e:
        print(f"Erreur Redis: {e}\n")

if __name__ == "__main__":
    check_sessions()
    check_redis_tasks()
