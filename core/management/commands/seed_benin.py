"""
Django management command pour seed les données du système béninois.
Usage: python manage.py seed_benin
"""
from django.core.management.base import BaseCommand
from core.models import Matiere, Classe


class Command(BaseCommand):
    help = "Seed les matières et classes du système éducatif béninois"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding du systeme beninois...")

        # ═══ MATIÈRES ═══
        matieres = [
            {"nom": "Français", "code": "FR", "couleur": "#E74C3C", "icone": "fa-book"},
            {"nom": "Mathématiques", "code": "MATH", "couleur": "#3498DB", "icone": "fa-calculator"},
            {"nom": "SVT", "code": "SVT", "couleur": "#2ECC71", "icone": "fa-leaf", "description": "Sciences de la Vie et de la Terre"},
            {"nom": "PCT", "code": "PCT", "couleur": "#9B59B6", "icone": "fa-flask", "description": "Physique-Chimie-Technologie"},
            {"nom": "Histoire-Géographie", "code": "HG", "couleur": "#F39C12", "icone": "fa-globe"},
            {"nom": "Anglais", "code": "ANG", "couleur": "#1ABC9C", "icone": "fa-language"},
            {"nom": "Espagnol", "code": "ESP", "couleur": "#E67E22", "icone": "fa-comments"},
            {"nom": "Philosophie", "code": "PHILO", "couleur": "#8E44AD", "icone": "fa-brain"},
            {"nom": "Éducation Physique et Sportive", "code": "EPS", "couleur": "#27AE60", "icone": "fa-running"},
            {"nom": "Économie", "code": "ECO", "couleur": "#D35400", "icone": "fa-chart-line"},
            {"nom": "Droit", "code": "DROIT", "couleur": "#C0392B", "icone": "fa-gavel"},
            {"nom": "Mathématiques Appliquées", "code": "MATH_APP", "couleur": "#2980B9", "icone": "fa-square-root-alt"},
            {"nom": "Physique-Chimie", "code": "PC", "couleur": "#8E44AD", "icone": "fa-atom"},
            {"nom": "Technologie Industrielle", "code": "TECH_IND", "couleur": "#7F8C8D", "icone": "fa-cogs"},
            {"nom": "Techniques Commerciales", "code": "TECH_COM", "couleur": "#16A085", "icone": "fa-store"},
            {"nom": "Comptabilité", "code": "COMPTA", "couleur": "#2C3E50", "icone": "fa-file-invoice-dollar"},
            {"nom": "Langue Nationale", "code": "LN", "couleur": "#F1C40F", "icone": "fa-comments"},
            {"nom": "Allemand", "code": "ALL", "couleur": "#34495E", "icone": "fa-language"},
            {"nom": "Sciences de la Vie et de la Terre", "code": "SVT_FULL", "couleur": "#2ECC71", "icone": "fa-leaf"},
            {"nom": "Physique-Chimie-Technologie", "code": "PCT_FULL", "couleur": "#9B59B6", "icone": "fa-flask"},
            {"nom": "Communication Écrite", "code": "COMM", "couleur": "#E74C3C", "icone": "fa-pen"},
            {"nom": "Techniques de Base de Secrétariat", "code": "TBS", "couleur": "#95A5A6", "icone": "fa-keyboard"},
            {"nom": "Étude de Cas", "code": "ETUDE", "couleur": "#34495E", "icone": "fa-briefcase"},
        ]

        created_matiere = 0
        for data in matieres:
            obj, created = Matiere.objects.get_or_create(code=data["code"], defaults=data)
            if created:
                created_matiere += 1
                self.stdout.write(f"  + Matiere: {obj.nom}")

        # ═══ CLASSES ═══
        classes = [
            {"nom": "6ème A", "niveau": "secondaire", "section": ""},
            {"nom": "6ème B", "niveau": "secondaire", "section": ""},
            {"nom": "5ème A", "niveau": "secondaire", "section": ""},
            {"nom": "5ème B", "niveau": "secondaire", "section": ""},
            {"nom": "4ème A", "niveau": "secondaire", "section": ""},
            {"nom": "4ème B", "niveau": "secondaire", "section": ""},
            {"nom": "3ème A", "niveau": "secondaire", "section": ""},
            {"nom": "3ème B", "niveau": "secondaire", "section": ""},
            {"nom": "Seconde A", "niveau": "secondaire", "section": ""},
            {"nom": "Seconde B", "niveau": "secondaire", "section": ""},
            {"nom": "Première A1", "niveau": "secondaire", "section": "A1"},
            {"nom": "Première A2", "niveau": "secondaire", "section": "A2"},
            {"nom": "Première B", "niveau": "secondaire", "section": "B"},
            {"nom": "Première C", "niveau": "secondaire", "section": "C"},
            {"nom": "Première D", "niveau": "secondaire", "section": "D"},
            {"nom": "Première E", "niveau": "secondaire", "section": "E"},
            {"nom": "Terminale A1", "niveau": "secondaire", "section": "A1"},
            {"nom": "Terminale A2", "niveau": "secondaire", "section": "A2"},
            {"nom": "Terminale B", "niveau": "secondaire", "section": "B"},
            {"nom": "Terminale C", "niveau": "secondaire", "section": "C"},
            {"nom": "Terminale D", "niveau": "secondaire", "section": "D"},
            {"nom": "Terminale E", "niveau": "secondaire", "section": "E"},
            {"nom": "Terminale G1", "niveau": "secondaire", "section": "G1"},
            {"nom": "Terminale G2", "niveau": "secondaire", "section": "G2"},
            {"nom": "Terminale G3", "niveau": "secondaire", "section": "G3"},
        ]

        annee = "2025-2026"
        created_classe = 0
        for data in classes:
            obj, created = Classe.objects.get_or_create(
                nom=data["nom"],
                annee_academique=annee,
                defaults=data
            )
            if created:
                created_classe += 1
                self.stdout.write(f"  + Classe: {obj.nom}")

        self.stdout.write(self.style.SUCCESS(
            f"\nSeed termine ! {created_matiere} matieres, {created_classe} classes creees."
        ))
