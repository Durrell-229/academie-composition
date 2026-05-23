#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

from core.redis_tasks import get_redis_connection
from compositions.models import CompositionSession, Resultat
from django.contrib.auth import get_user_model

User = get_user_model()

def check_redis_status():
    print("=== VÉRIFICATION REDIS ===\n")
    
    try:
        redis_conn = get_redis_connection()
        print(f"✅ Connexion Redis établie")
        
        # Tester une opération simple
        redis_conn.set('test_key', 'test_value')
        test_value = redis_conn.get('test_key')
        print(f"✅ Test Redis: {test_value.decode()}")
        
        # Vérifier les files d'attente
        queues = ['default', 'high_priority', 'low_priority']
        for queue in queues:
            length = redis_conn.llen(queue)
            print(f"📋 Queue '{queue}': {length} tâches en attente")
            
            if length > 0:
                # Afficher les premières tâches
                for i in range(min(3, length)):
                    task_data = redis_conn.lindex(queue, i)
                    if task_data:
                        try:
                            task = json.loads(task_data)
                            print(f"   Tâche {i+1}: {task.get('task_name', 'Inconnue')} - {task.get('args', [])}")
                        except:
                            print(f"   Tâche {i+1}: {task_data[:50]}...")
        
        redis_conn.delete('test_key')
        
    except Exception as e:
        print(f"❌ Erreur Redis: {e}")
        print("   Redis est-il démarré ?")
        print("   Commande: redis-server")

def check_task_worker():
    print("\n=== VÉRIFICATION WORKER ===\n")
    
    try:
        import subprocess
        result = subprocess.run(['python', 'manage.py', 'worker_status'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Worker actif")
        else:
            print("❌ Worker inactif")
            print("   Commande pour démarrer: python manage.py run_worker")
    except Exception as e:
        print(f"❌ Erreur vérification worker: {e}")
        print("   Démarrer le worker avec: python manage.py run_worker")

def manual_correction():
    print("\n=== CORRECTION MANUELLE TEST ===\n")
    
    # Trouver une session en cours
    sessions = CompositionSession.objects.filter(statut='en_cours')
    if not sessions:
        print("❌ Aucune session en cours trouvée")
        return
    
    session = sessions.first()
    print(f"📝 Session trouvée: {session.exam.titre}")
    print(f"   Élève: {session.eleve.email}")
    print(f"   Statut: {session.statut}")
    
    # Vérifier s'il y a des fichiers ou réponses
    files = session.submission_files.all()
    answers = session.answers.all()
    
    if not files.exists() and not answers.exists():
        print("❌ Aucun fichier ou réponse à corriger")
        print("   L'élève doit d'abord soumettre sa composition")
        return
    
    print(f"📁 Fichiers: {files.count()}")
    print(f"✍️ Réponses: {answers.count()}")
    
    # Lancer la correction manuellement
    try:
        from compositions.tasks import process_ia_correction
        print("🚀 Lancement correction manuelle...")
        result = process_ia_correction(str(session.id))
        print(f"✅ Résultat: {result}")
        
        # Vérifier si le bulletin a été généré
        try:
            resultat = Resultat.objects.get(session=session)
            if resultat.bulletin_pdf:
                print("✅ Bulletin PDF généré")
                print(f"   Fichier: {resultat.bulletin_pdf.name}")
            else:
                print("❌ Bulletin PDF non généré")
        except Resultat.DoesNotExist:
            print("❌ Pas de résultat créé")
            
    except Exception as e:
        print(f"❌ Erreur correction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_redis_status()
    check_task_worker()
    manual_correction()
