#!/usr/bin/env python
"""
Script d'installation du système temps réel
"""
import subprocess
import sys

def install_realtime():
    """Installer les dépendances temps réel"""
    print("🚀 Installation du système temps réel...")
    
    try:
        # Installer les dépendances
        print("1. Installation des dépendances...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'channels', 'channels-redis', 'daphne', 'django-redis', 'redis'], check=True)
        
        print("2. Installation Redis...")
        print("   Veuillez installer Redis sur votre système:")
        print("   - Windows: Télécharger depuis https://redis.io/download")
        print("   - Linux: sudo apt-get install redis-server")
        print("   - Mac: brew install redis")
        
        print("3. Démarrer Redis...")
        print("   redis-server")
        
        print("4. Migrer la base de données...")
        subprocess.run([sys.executable, 'manage.py', 'makemigrations', 'realtime'], check=True)
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        
        print("5. Lancer le serveur avec Daphne...")
        print("   daphne -b 0.0.0.0 -p 8000 academie_numerique.asgi:application")
        
        print("✅ Installation terminée!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_realtime()
