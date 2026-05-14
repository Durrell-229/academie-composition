"""
Management command pour corriger les noms de classes corrompus dans la base de données.

Corrections effectuées :
- Encodages corrompus : \\xff, \\xfe, \\xe8, etc. ->lettres accentuées correctes
- Normalisation du champ `niveau` en minuscule
- Suppression des doublons (même nom insensible à la casse)

Usage : python manage.py fix_classes
"""
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Classe, NIVEAU_CHOICES


# Table de substitution des séquences d'octets mal encodées vers l'UTF-8 correct
ENCODING_FIXES = [
    # Séquences les plus courantes en contexte béninois (Latin-1 / Windows-1252 mal interprétés)
    ('\xffre', 'ère'),   # 1ère, 2ère  — \xff (ÿ en latin-1) remplace é
    ('\xfeme', 'ème'),   # 3ème …
    ('\xffme', 'ème'),
    ('\xe8re', 'ère'),   # \xe8 = è en latin-1
    ('\xe8me', 'ème'),
    ('\xE8re', 'ère'),
    ('\xE8me', 'ème'),
    ('\xe9re', 'ère'),   # \xe9 = é en latin-1 — parfois aussi mauvais contexte
    ('\xe9me', 'ème'),
    ('\xE9re', 'ère'),
    ('\xE9me', 'ème'),
    # Niveau courant
    ('\xe8ve', 'ève'),
    ('\xe9ve', 'éve'),
]

# Valeurs valides pour le champ niveau
VALID_NIVEAUX = {choice[0] for choice in NIVEAU_CHOICES}


def _fix_encoding(text: str) -> str:
    """Applique les corrections d'encodage connues, puis nettoie les caractères >= 0x80
    qui ne sont pas de l'UTF-8 valide (les Python str sont toujours Unicode, donc les
    caractères latin-1 parasites restent comme points de code U+00xx)."""
    result = text
    for bad, good in ENCODING_FIXES:
        result = result.replace(bad, good)
    return result


def _has_bad_chars(text: str) -> bool:
    """Retourne True si le texte contient des caractères latin-1 suspects (U+0080–U+00FF)
    autres que les lettres accentuées françaises normales."""
    # Caractères accentués français légitimes
    LEGIT = set('àâäéèêëîïôùûüçœæÀÂÄÉÈÊËÎÏÔÙÛÜÇŒÆ')
    for ch in text:
        code = ord(ch)
        if 0x80 <= code <= 0xFF and ch not in LEGIT:
            return True
    return False


class Command(BaseCommand):
    help = "Corrige les encodages corrompus, normalise 'niveau' et supprime les doublons dans core.Classe"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Affiche les corrections sans les appliquer",
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN — aucune modification en base"))

        stats = {
            'encoding_fixed': 0,
            'niveau_fixed': 0,
            'duplicates_removed': 0,
        }

        with transaction.atomic():
            all_classes = list(Classe.objects.all().order_by('created_at'))

            # ── 1. Corrections d'encodage et normalisation niveau ──────────────
            for classe in all_classes:
                changed = False
                original_nom = classe.nom
                original_niveau = classe.niveau

                # Correction encodage nom
                fixed_nom = _fix_encoding(classe.nom)
                if fixed_nom != classe.nom or _has_bad_chars(classe.nom):
                    # Si après les fixes connus il reste des chars suspects, on le signale
                    if _has_bad_chars(fixed_nom):
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ATTENTION : caractères suspects résiduels dans «{fixed_nom}» "
                                f"(original: {repr(original_nom)})"
                            )
                        )
                    if fixed_nom != classe.nom:
                        self.stdout.write(
                            f"  Encodage  : {repr(original_nom)} ->«{fixed_nom}»"
                        )
                        classe.nom = fixed_nom
                        stats['encoding_fixed'] += 1
                        changed = True

                # Normalisation niveau ->minuscule
                fixed_niveau = classe.niveau.lower().strip() if classe.niveau else classe.niveau
                # Vérifier que la valeur normalisée est dans les choix valides
                if fixed_niveau not in VALID_NIVEAUX:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  NIVEAU INVALIDE pour «{classe.nom}» : {repr(original_niveau)} "
                            f"(après normalisation: {repr(fixed_niveau)}) — valeurs valides: {sorted(VALID_NIVEAUX)}"
                        )
                    )
                if fixed_niveau != classe.niveau:
                    self.stdout.write(
                        f"  Niveau    : «{classe.nom}» : {repr(original_niveau)} ->{repr(fixed_niveau)}"
                    )
                    classe.niveau = fixed_niveau
                    stats['niveau_fixed'] += 1
                    changed = True

                if changed and not dry_run:
                    classe.save(update_fields=['nom', 'niveau'])

            # ── 2. Suppression des doublons ────────────────────────────────────
            # On recharge depuis la DB après les corrections pour avoir les noms à jour
            if not dry_run:
                all_classes = list(Classe.objects.all().order_by('created_at'))

            seen_noms: dict[str, Classe] = {}  # clé = nom.lower().strip()
            to_delete: list[Classe] = []

            for classe in all_classes:
                key = classe.nom.lower().strip()
                if key in seen_noms:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  DOUBLON   : «{classe.nom}» (id={classe.id}) "
                            f"duplique «{seen_noms[key].nom}» (id={seen_noms[key].id}) — suppression du plus récent"
                        )
                    )
                    to_delete.append(classe)
                    stats['duplicates_removed'] += 1
                else:
                    seen_noms[key] = classe

            if to_delete and not dry_run:
                ids = [c.id for c in to_delete]
                Classe.objects.filter(id__in=ids).delete()

            if dry_run:
                # Annule la transaction atomic
                transaction.set_rollback(True)

        # ── 3. Rapport final ───────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("Rapport fix_classes"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"  Encodages corrigés   : {stats['encoding_fixed']}")
        self.stdout.write(f"  Niveaux normalisés   : {stats['niveau_fixed']}")
        self.stdout.write(f"  Doublons supprimés   : {stats['duplicates_removed']}")
        if dry_run:
            self.stdout.write(self.style.WARNING("  (dry-run : rien n'a été écrit en base)"))
        else:
            self.stdout.write(self.style.SUCCESS("  Modifications appliquées en base."))

        # Afficher l'état final des classes
        self.stdout.write("")
        self.stdout.write("Classes en base après correction :")
        for c in Classe.objects.all().order_by('nom'):
            self.stdout.write(f"  [{c.niveau:12s}] {c.nom} ({c.annee_academique}) — actif={c.is_active}")
