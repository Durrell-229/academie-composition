#!/usr/bin/env python
"""
Script de configuration initiale pour la plateforme Académie Numérique
Crée un superutilisateur et des données de démonstration
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import User
from schools.models import Etablissement, Campus, NiveauScolaire, Classe, AnneeScolaire, ConfigurationEtablissement
from core.models import Matiere
from certificats.models import TypeCertificat


def create_superuser():
    """Créer le superutilisateur administrateur"""
    print("=" * 60)
    print("🎓 CRÉATION DU SUPERUTILISATEUR ACADÉMIE NUMÉRIQUE")
    print("=" * 60)
    
    # Vérifier si un superutilisateur existe déjà
    if User.objects.filter(is_superuser=True).exists():
        print("\n⚠️  Un superutilisateur existe déjà.")
        response = input("Voulez-vous créer un nouveau superutilisateur ? (o/n): ")
        if response.lower() != 'o':
            print("⏭️  Passage à la création des données de démonstration...")
            return
    
    print("\n📝 Veuillez entrer les informations du superutilisateur :\n")
    
    username = input("Nom d'utilisateur (admin): ") or "admin"
    email = input("Email: ")
    password = input("Mot de passe: ")
    confirm_password = input("Confirmer le mot de passe: ")
    
    if password != confirm_password:
        print("\n❌ Les mots de passe ne correspondent pas !")
        return
    
    if not password:
        password = "Admin@2024!"
        print(f"\n⚠️  Mot de passe par défaut utilisé: {password}")
    
    try:
        # Créer le superutilisateur
        admin_user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name="Administrateur",
            last_name="Système",
            role="admin",
            phone="+229 00 00 00 00",
            is_staff=True,
            is_superuser=True,
            is_active=True,
            email_verified=True
        )
        
        print(f"\n✅ Superutilisateur créé avec succès !")
        print(f"   👤 Nom d'utilisateur: {username}")
        print(f"   📧 Email: {email}")
        print(f"   🔑 Mot de passe: {'*' * len(password)}")
        print(f"\n🌐 Accès admin: http://127.0.0.1:8000/admin/")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la création: {e}")


def create_demo_data():
    """Créer des données de démonstration"""
    print("\n" + "=" * 60)
    print("🏫 CRÉATION DES DONNÉES DE DÉMONSTRATION")
    print("=" * 60)
    
    # Vérifier s'il y a déjà des données
    if Etablissement.objects.exists():
        print("\n⚠️  Des établissements existent déjà.")
        response = input("Voulez-vous créer des données de démo supplémentaires ? (o/n): ")
        if response.lower() != 'o':
            return
    
    try:
        # 1. Créer l'établissement
        print("\n📍 Création de l'établissement...")
        etablissement = Etablissement.objects.create(
            nom="Lycée Technique de Cotonou",
            code="LTC-COT-001",
            type_etablissement="lycee",
            adresse="Avenue Steinmetz, en face de l'Ecole Police",
            ville="Cotonou",
            pays="Bénin",
            telephone="+229 21 30 00 00",
            email="contact@ltc-cotonou.bj",
            site_web="https://ltc-cotonou.bj",
            numero_agrement="N°001/MESRS/DC/SGM/DESG/2024",
            capacite_max=2000,
            nombre_eleves=1850,
            nombre_professeurs=120,
            annee_scolaire_courante="2024-2025",
            devise="XOF",
            is_active=True,
            is_verified=True
        )
        print(f"   ✅ Établissement créé: {etablissement.nom}")
        
        # 2. Créer la configuration
        ConfigurationEtablissement.objects.create(
            etablissement=etablissement,
            systeme_evaluation="20",
            note_minimale_reussite=10.00,
            couleur_principale="#1e3a8a",
            couleur_secondaire="#e8112d",
            nom_personnalise_bulletin="Bulletin du Lycée Technique de Cotonou"
        )
        print("   ✅ Configuration créée")
        
        # 3. Créer le campus principal
        campus = Campus.objects.create(
            etablissement=etablissement,
            nom="Campus Principal",
            code="CP-01",
            adresse="Avenue Steinmetz",
            ville="Cotonou",
            pays="Bénin",
            nombre_salles=45,
            nombre_batiments=8,
            is_principal=True,
            is_active=True
        )
        print(f"   ✅ Campus créé: {campus.nom}")
        
        # 4. Créer les niveaux scolaires
        niveaux_data = [
            {"nom": "6ème", "code": "6E", "ordre": 1, "duree_annees": 1},
            {"nom": "5ème", "code": "5E", "ordre": 2, "duree_annees": 1},
            {"nom": "4ème", "code": "4E", "ordre": 3, "duree_annees": 1},
            {"nom": "3ème", "code": "3E", "ordre": 4, "duree_annees": 1},
            {"nom": "2nde", "code": "2ND", "ordre": 5, "duree_annees": 1},
            {"nom": "1ère", "code": "1ER", "ordre": 6, "duree_annees": 1},
            {"nom": "Terminale", "code": "TLE", "ordre": 7, "duree_annees": 1},
        ]
        
        niveaux_crees = []
        for niv_data in niveaux_data:
            niveau = NiveauScolaire.objects.create(
                etablissement=etablissement,
                **niv_data
            )
            niveaux_crees.append(niveau)
            print(f"   ✅ Niveau créé: {niveau.nom}")
        
        # 5. Créer les matières
        print("\n📚 Création des matières...")
        matieres_data = [
            {"nom": "Mathématiques", "code": "MATH"},
            {"nom": "Physique-Chimie", "code": "PC"},
            {"nom": "Sciences de la Vie et de la Terre", "code": "SVT"},
            {"nom": "Français", "code": "FR"},
            {"nom": "Anglais", "code": "ANG"},
            {"nom": "Histoire-Géographie", "code": "HG"},
            {"nom": "Philosophie", "code": "PHILO"},
            {"nom": "Éducation Civique", "code": "EC"},
        ]
        
        for mat_data in matieres_data:
            Matiere.objects.create(**mat_data)
            print(f"   ✅ Matière créée: {mat_data['nom']}")
        
        # 6. Créer les classes
        print("\n🏫 Création des classes...")
        for niveau in niveaux_crees:
            for section in ['A', 'B']:
                Classe.objects.create(
                    etablissement=etablissement,
                    campus=campus,
                    niveau=niveau,
                    nom=f"{niveau.nom} {section}",
                    code=f"{niveau.code}-{section}-2024",
                    section=section,
                    capacite_max=50,
                    effectif_actuel=45,
                    annee_scolaire="2024-2025",
                    is_active=True
                )
                print(f"   ✅ Classe créée: {niveau.nom} {section}")
        
        # 7. Créer les types de certificats
        print("\n🎓 Création des types de certificats...")
        types_certificats = [
            {
                "code": "BEPC",
                "nom": "Brevet d'Études du Premier Cycle (BEPC)",
                "niveau_scolaire": "secondaire_1",
                "mention_reussite": "ADMIS AU BEPC",
                "mention_echec": "REFUSÉ AU BEPC"
            },
            {
                "code": "BAC",
                "nom": "Baccalauréat",
                "niveau_scolaire": "secondaire_2",
                "mention_reussite": "ADMIS AU BACCALAURÉAT",
                "mention_echec": "REFUSÉ AU BACCALAURÉAT"
            },
        ]
        
        for tc_data in types_certificats:
            TypeCertificat.objects.create(
                etablissement=etablissement,
                **tc_data
            )
            print(f"   ✅ Type de certificat créé: {tc_data['nom']}")
        
        print("\n" + "=" * 60)
        print("✅ DONNÉES DE DÉMONSTRATION CRÉÉES AVEC SUCCÈS !")
        print("=" * 60)
        print(f"\n🏫 Établissement: {etablissement.nom}")
        print(f"📍 Localisation: {etablissement.ville}, {etablissement.pays}")
        print(f"🏢 Campus: {campus.nom}")
        print(f"📚 Classes: {Classe.objects.filter(etablissement=etablissement).count()}")
        print(f"🎓 Types de certificats: {TypeCertificat.objects.filter(etablissement=etablissement).count()}")
        print("\n🌐 Accès à la plateforme: http://127.0.0.1:8000/")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la création des données: {e}")
        import traceback
        traceback.print_exc()


def print_summary():
    """Afficher le résumé final"""
    print("\n" + "=" * 60)
    print("🎉 CONFIGURATION TERMINÉE !")
    print("=" * 60)
    print("""
┌─────────────────────────────────────────────────────────────┐
│                    PROCHAINES ÉTAPES                       │
├─────────────────────────────────────────────────────────────┤
│  1. 🚀 Démarrer le serveur:                                 │
│     python manage.py runserver                              │
│                                                             │
│  2. 🌐 Accéder à l'admin:                                   │
│     http://127.0.0.1:8000/admin/                          │
│                                                             │
│  3. 📊 Dashboard principal:                                 │
│     http://127.0.0.1:8000/                                  │
│                                                             │
│  4. 🎓 Gestion des certificats:                             │
│     http://127.0.0.1:8000/certificats/                    │
│                                                             │
│  5. 💰 Gestion des paiements:                             │
│     http://127.0.0.1:8000/payments/                       │
│                                                             │
│  📧 Support: support@academie-numerique.bj               │
└─────────────────────────────────────────────────────────────┘
""")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         🎓 ACADÉMIE NUMÉRIQUE - CONFIGURATION INITIALE       ║
║                                                              ║
║         Plateforme éducative internationale complète         ║
║         Adaptée au système scolaire du Bénin 🇧🇯             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Créer le superutilisateur
    create_superuser()
    
    # Créer les données de démo
    create_demo_data()
    
    # Afficher le résumé
    print_summary()
    
    input("\nAppuyez sur Entrée pour quitter...")
