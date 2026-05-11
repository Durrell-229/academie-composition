#!/usr/bin/env python
"""
Script d'installation et configuration de Redis pour Windows
"""
import os
import subprocess
import sys
import urllib.request
import zipfile
import shutil

def download_redis():
    """Télécharge Redis pour Windows"""
    print("📥 Téléchargement de Redis pour Windows...")
    
    # URL de Redis pour Windows (version portable)
    redis_url = "https://github.com/tporadowski/redis/releases/download/v5.0.14.1/redis-5.0.14.1.zip"
    
    try:
        urllib.request.urlretrieve(redis_url, "redis.zip")
        print("✅ Redis téléchargé avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur téléchargement Redis: {e}")
        return False

def extract_redis():
    """Extrait Redis dans le dossier du projet"""
    print("📦 Extraction de Redis...")
    
    try:
        with zipfile.ZipFile("redis.zip", 'r') as zip_ref:
            zip_ref.extractall("redis")
        print("✅ Redis extrait avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur extraction Redis: {e}")
        return False

def setup_redis_config():
    """Configure Redis pour le projet"""
    print("⚙️ Configuration de Redis...")
    
    config_content = """
# Configuration Redis pour Académie Numérique
port 6379
bind 127.0.0.1
timeout 300
keepalive 60
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
"""
    
    try:
        with open("redis/redis.conf", "w") as f:
            f.write(config_content.strip())
        print("✅ Configuration Redis créée")
        return True
    except Exception as e:
        print(f"❌ Erreur configuration Redis: {e}")
        return False

def create_redis_bat():
    """Crée des fichiers batch pour démarrer Redis"""
    
    # Fichier de démarrage
    start_bat = """@echo off
echo Démarrage Redis Server...
cd /d "%~dp0"
redis-server.exe redis.conf
pause
"""
    
    # Fichier d'arrêt
    stop_bat = """@echo off
echo Arrêt de Redis Server...
redis-cli.exe shutdown
pause
"""
    
    try:
        with open("redis/start_redis.bat", "w") as f:
            f.write(start_bat)
        with open("redis/stop_redis.bat", "w") as f:
            f.write(stop_bat)
        print("✅ Fichiers batch créés")
        return True
    except Exception as e:
        print(f"❌ Erreur création fichiers batch: {e}")
        return False

def test_redis():
    """Test la connexion Redis"""
    print("🧪 Test de connexion Redis...")
    
    try:
        # Importer les modules Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
        import django
        django.setup()
        
        from core.redis_tasks import get_redis_connection
        
        redis_conn = get_redis_connection()
        redis_conn.set('test_key', 'test_value')
        test_value = redis_conn.get('test_key')
        
        if test_value and test_value.decode() == 'test_value':
            print("✅ Redis fonctionne parfaitement!")
            redis_conn.delete('test_key')
            return True
        else:
            print("❌ Test Redis échoué")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test Redis: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 INSTALLATION REDIS POUR ACADÉMIE NUMÉRIQUE")
    print("=" * 50)
    
    # Vérifier si Redis existe déjà
    if os.path.exists("redis/redis-server.exe"):
        print("✅ Redis déjà installé")
        if test_redis():
            print("\n🎉 Redis est prêt à utiliser!")
            print("\n📋 COMMANDES UTILES:")
            print("   Démarrer: redis/start_redis.bat")
            print("   Arrêter: redis/stop_redis.bat")
            print("   Worker: python manage.py run_worker")
            return
        else:
            print("⚠️ Redis installé mais non fonctionnel")
    
    # Installation complète
    steps = [
        ("Téléchargement", download_redis),
        ("Extraction", extract_redis),
        ("Configuration", setup_redis_config),
        ("Fichiers batch", create_redis_bat),
        ("Test", test_redis)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            print(f"❌ Échec à l'étape: {step_name}")
            return
    
    print("\n🎉 INSTALLATION RÉUSSIE!")
    print("\n📋 PROCHAINES ÉTAPES:")
    print("1. Démarrez Redis: double-cliquez sur redis/start_redis.bat")
    print("2. Démarrez le worker: python manage.py run_worker")
    print("3. Testez la soumission d'une composition")
    
    print("\n⚠️ IMPORTANT:")
    print("- Redis doit tourner en arrière-plan")
    print("- Le worker doit être actif pour les corrections IA")
    print("- Les bulletins seront générés automatiquement")

if __name__ == "__main__":
    main()
