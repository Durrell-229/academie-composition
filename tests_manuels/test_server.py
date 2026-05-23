#!/usr/bin/env python
import requests
import time

def test_server():
    """Test si le serveur répond correctement"""
    try:
        response = requests.get('http://localhost:8000/', timeout=5)
        if response.status_code == 200:
            print("✅ Serveur répond correctement")
            print(f"Status: {response.status_code}")
            return True
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Serveur inaccessible")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("Test du serveur Django...")
    time.sleep(2)  # Attendre que le serveur démarre
    test_server()
