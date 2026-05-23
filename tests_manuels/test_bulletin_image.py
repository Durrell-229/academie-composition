#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de test: Génération de bulletin à partir de l'image bulletin.png
"""

import os
import sys
import django

# Forcer UTF-8 sur Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Initialiser Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

from bulletins.image_generator import BulletinImageValidator, ImageBulletinGenerator
from bulletins.data_aggregator import BulletinDataAggregator
from bulletins.models import Bulletin
from accounts.models import User
from core.models import Classe
from django.contrib.auth import get_user_model


def test_image_validity():
    """Test 1: Vérifier que bulletin.png est valide."""
    print("\n" + "="*70)
    print("TEST 1: Validation de l'image bulletin.png")
    print("="*70)

    is_valid, msg = BulletinImageValidator.validate_image()
    print(f"Résultat: {is_valid}")
    print(f"Message: {msg}")

    if not is_valid:
        print("[FAIL] ERREUR: L'image bulletin.png est invalide!")
        return False

    print("[OK] Image valide")
    return True


def test_data_aggregation():
    """Test 2: Vérifier l'agrégation de données."""
    print("\n" + "="*70)
    print("TEST 2: Agrégation de données")
    print("="*70)

    # Chercher un élève pour tester
    User = get_user_model()
    eleves = User.objects.filter(role='eleve')[:1]

    if not eleves:
        print("[FAIL] ERREUR: Aucun élève trouvé dans la base de données")
        return False

    eleve = eleves[0]
    print(f"Élève test: {eleve.full_name} ({eleve.id})")

    # Chercher une classe
    classe = eleve.classe if hasattr(eleve, 'classe') else None
    if not classe:
        print("[WARN] ATTENTION: Aucune classe trouvée pour cet élève")
        return False

    print(f"Classe: {classe}")

    try:
        # Agréger les données
        data = BulletinDataAggregator.aggregate_notes(
            eleve=eleve,
            classe=classe,
            periode='T1',
            annee_scolaire='2025-2026'
        )

        print(f"\nDonnées agrégées:")
        print(f"  - Matieres: {len(data['matieres'])}")
        print(f"  - Moyenne générale: {data['moyenne_generale']}")
        print(f"  - Rang: {data['rang']}")
        print(f"  - Effectif: {data['effectif']}")

        if len(data['matieres']) > 0:
            print(f"\n  Exemple (1ère matière):")
            m = data['matieres'][0]
            print(f"    - Nom: {m['nom']}")
            print(f"    - Coefficient: {m['coefficient']}")
            print(f"    - Moy. Interrogations: {m['moy_interrogations']}")
            print(f"    - Moy. Devoirs: {m['moy_devoirs']}")
            print(f"    - Moy. Finale: {m['moyenne_finale']}")

        print("[OK] Agrégation réussie")
        return True, data, eleve

    except Exception as e:
        print(f"[FAIL] ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_generation(data, eleve):
    """Test 3: Générer un PDF test."""
    print("\n" + "="*70)
    print("TEST 3: Génération du PDF")
    print("="*70)

    # Créer un bulletin test
    try:
        # Chercher ou créer un bulletin
        bulletin = Bulletin.objects.filter(eleve=eleve, periode='T1').first()

        if not bulletin:
            # Créer un bulletin de test
            print("Création d'un bulletin de test...")
            classe = eleve.classe if hasattr(eleve, 'classe') else None
            bulletin = Bulletin.objects.create(
                eleve=eleve,
                classe=str(classe) if classe else '3ème A',
                annee_scolaire='2025-2026',
                periode='T1',
                type_bulletin=Bulletin.TypeBulletin.ADMINISTRATIF,
                moyenne_generale=0,
                rang=1,
                effectif_total=40,
                appreciation_ia="Test de bulletin",
                observation_conseil="Travail satisfaisant. À continuer.",
                decision_conseil="ADMIS"
            )
            print(f"Bulletin créé: {bulletin.id}")

        # Générer le PDF
        print(f"\nGénération du PDF pour: {bulletin.eleve.full_name}")

        pdf_bytes = ImageBulletinGenerator.generate(bulletin, data)

        if not pdf_bytes:
            print("[FAIL] ERREUR: Aucun PDF généré")
            return False

        print(f"[OK] PDF généré: {len(pdf_bytes)} bytes")

        # Sauvegarder le PDF test
        output_path = 'C:/tmp/test_bulletin.pdf'
        os.makedirs('C:/tmp', exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

        print(f"[OK] PDF sauvegardé à: {output_path}")
        print(f"\n[INFO] Conseil: Ouvrez {output_path} pour vérifier visuellement le rendu")

        return True

    except Exception as e:
        print(f"[FAIL] ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Lance tous les tests."""
    print("\n" + "="*70)
    print("TESTS: Système de bulletin par image bulletin.png")
    print("="*70)

    # Test 1
    if not test_image_validity():
        print("\n❌ Les tests suivants seront ignorés (image invalide)")
        return

    # Test 2
    result = test_data_aggregation()
    if isinstance(result, bool) and not result:
        print("\n[FAIL] Les tests suivants seront ignores (donnees invalides)")
        return
    elif isinstance(result, tuple):
        success, data, eleve = result
    else:
        print("\n[FAIL] Erreur dans test_data_aggregation")
        return

    # Test 3
    if not test_pdf_generation(data, eleve):
        print("\n[FAIL] Erreur lors de la generation du PDF")
        return

    print("\n" + "="*70)
    print("[SUCCESS] TOUS LES TESTS SONT PASSES")
    print("="*70)
    print("\n[INFO] Prochaine etape: Deployez en production et testez via l'interface Django")


if __name__ == '__main__':
    main()
