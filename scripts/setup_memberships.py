"""
Script de peuplement : rattache les utilisateurs existants aux établissements.

Usage :
    python manage.py shell < scripts/setup_memberships.py
  ou
    python scripts/setup_memberships.py  (si DJANGO_SETTINGS_MODULE est défini)

Règles appliquées :
  - Tous les admins/superusers → ajoutés à TOUS les établissements avec rôle admin
  - Tous les professeurs       → ajoutés au premier établissement actif (rôle professeur)
  - Tous les élèves            → ajoutés au premier établissement actif (rôle eleve)
  - Le premier établissement devient l'établissement principal pour chaque utilisateur
"""

import os
import sys
import django

# Bootstrap Django si exécuté directement
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from accounts.models import User, MembreEtablissement
from schools.models import Etablissement


def run():
    etablissements = list(Etablissement.objects.filter(is_active=True).order_by('nom'))

    if not etablissements:
        print("❌  Aucun établissement actif trouvé. Créez d'abord un établissement via /schools/create/")
        return

    principal = etablissements[0]
    created_total = 0
    skipped_total = 0

    print(f"\n✅  {len(etablissements)} établissement(s) actif(s) trouvé(s).")
    print(f"    Établissement principal par défaut : {principal.nom}\n")

    # ── Admins & Superusers → tous les établissements ──────────────────────
    admins = User.objects.filter(is_active=True).filter(
        models_Q(role='admin') | models_Q(is_superuser=True)
    )
    print(f"👤  Traitement de {admins.count()} admin(s)…")
    for user in admins:
        for i, etab in enumerate(etablissements):
            m, created = MembreEtablissement.objects.get_or_create(
                user=user,
                etablissement=etab,
                defaults={
                    'role': MembreEtablissement.Role.ADMIN,
                    'is_active': True,
                    'est_principal': (i == 0),
                }
            )
            if created:
                created_total += 1
                print(f"   + {user.full_name} → {etab.nom} (admin)")
            else:
                skipped_total += 1

    # ── Professeurs → établissement principal ──────────────────────────────
    profs = User.objects.filter(role='professeur', is_active=True)
    print(f"\n👤  Traitement de {profs.count()} professeur(s)…")
    for user in profs:
        m, created = MembreEtablissement.objects.get_or_create(
            user=user,
            etablissement=principal,
            defaults={
                'role': MembreEtablissement.Role.PROFESSEUR,
                'is_active': True,
                'est_principal': True,
            }
        )
        if created:
            created_total += 1
            print(f"   + {user.full_name} → {principal.nom} (professeur)")
        else:
            skipped_total += 1

    # ── Élèves → établissement principal ──────────────────────────────────
    eleves = User.objects.filter(role='eleve', is_active=True)
    print(f"\n👤  Traitement de {eleves.count()} élève(s)…")
    for user in eleves:
        m, created = MembreEtablissement.objects.get_or_create(
            user=user,
            etablissement=principal,
            defaults={
                'role': MembreEtablissement.Role.ELEVE,
                'is_active': True,
                'est_principal': True,
            }
        )
        if created:
            created_total += 1
        else:
            skipped_total += 1
    print(f"   {eleves.count()} élève(s) traité(s)")

    # ── Conseillers → établissement principal ─────────────────────────────
    conseillers = User.objects.filter(role='conseiller', is_active=True)
    print(f"\n👤  Traitement de {conseillers.count()} conseiller(s)…")
    for user in conseillers:
        m, created = MembreEtablissement.objects.get_or_create(
            user=user,
            etablissement=principal,
            defaults={
                'role': MembreEtablissement.Role.CONSEILLER,
                'is_active': True,
                'est_principal': True,
            }
        )
        if created:
            created_total += 1
        else:
            skipped_total += 1

    print(f"\n{'─'*50}")
    print(f"✅  Terminé : {created_total} lien(s) créé(s), {skipped_total} existant(s) ignoré(s).")


# Import nécessaire pour les admins (Q object)
from django.db.models import Q as models_Q

run()
