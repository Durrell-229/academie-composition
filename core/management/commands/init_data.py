from django.core.management.base import BaseCommand
from core.models import Matiere, Classe
from gamification.models import Badge


class Command(BaseCommand):
    help = 'Initialise les données de base (matières, classes)'

    def handle(self, *args, **options):
        matieres_data = [
            {'nom': 'Mathématiques', 'code': 'MATH', 'couleur': '#6366F1'},
            {'nom': 'Physique-Chimie', 'code': 'PC', 'couleur': '#8B5CF6'},
            {'nom': 'Sciences de la Vie et de la Terre', 'code': 'SVT', 'couleur': '#10B981'},
            {'nom': 'Français', 'code': 'FR', 'couleur': '#F59E0B'},
            {'nom': 'Anglais', 'code': 'ANG', 'couleur': '#EF4444'},
            {'nom': 'Histoire-Géographie', 'code': 'HG', 'couleur': '#06B6D4'},
            {'nom': 'Philosophie', 'code': 'PHILO', 'couleur': '#EC4899'},
            {'nom': 'Informatique', 'code': 'INFO', 'couleur': '#14B8A6'},
        ]

        created_count = 0
        for data in matieres_data:
            _, created = Matiere.objects.get_or_create(code=data['code'], defaults=data)
            if created:
                created_count += 1

        classes_data = [
            {'nom': 'Sixième', 'niveau': 'primaire', 'annee_academique': '2025-2026'},
            {'nom': 'Cinquième', 'niveau': 'secondaire', 'annee_academique': '2025-2026'},
            {'nom': 'Quatrième', 'niveau': 'secondaire', 'annee_academique': '2025-2026'},
            {'nom': 'Troisième', 'niveau': 'secondaire', 'annee_academique': '2025-2026'},
            {'nom': 'Seconde', 'niveau': 'secondaire', 'annee_academique': '2025-2026'},
            {'nom': 'Première', 'niveau': 'secondaire', 'annee_academique': '2025-2026'},
            {'nom': 'Terminale', 'niveau': 'secondaire', 'annee_academique': '2025-2026'},
            {'nom': 'Licence 1', 'niveau': 'universitaire', 'annee_academique': '2025-2026'},
            {'nom': 'Licence 2', 'niveau': 'universitaire', 'annee_academique': '2025-2026'},
            {'nom': 'Licence 3', 'niveau': 'universitaire', 'annee_academique': '2025-2026'},
            {'nom': 'Master 1', 'niveau': 'universitaire', 'annee_academique': '2025-2026'},
            {'nom': 'Master 2', 'niveau': 'universitaire', 'annee_academique': '2025-2026'},
        ]

        for data in classes_data:
            _, created = Classe.objects.get_or_create(nom=data['nom'], annee_academique=data['annee_academique'], defaults=data)
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'{created_count} entrées créées avec succès.'))

        # Créer les badges
        badges_data = [
            # Académique
            {'nom': 'Major de promotion', 'description': 'Obtenir la première place du classement trimestriel', 'icone': '🥇', 'categorie': 'academique', 'points': 100, 'rarete': 'legendaire', 'condition_obtention': {'type': 'classement', 'rang': 1}},
            {'nom': 'Excellent', 'description': 'Obtenir une moyenne supérieure à 18/20', 'icone': '⭐', 'categorie': 'academique', 'points': 50, 'rarete': 'epique', 'condition_obtention': {'type': 'moyenne', 'min': 18}},
            {'nom': 'Bon élève', 'description': 'Obtenir une moyenne supérieure à 15/20', 'icone': '🌟', 'categorie': 'academique', 'points': 30, 'rarete': 'rare', 'condition_obtention': {'type': 'moyenne', 'min': 15}},
            {'nom': 'Assidu', 'description': 'Avoir une présence régulière en cours pendant un mois', 'icone': '📚', 'categorie': 'academique', 'points': 20, 'rarete': 'commun', 'condition_obtention': {'type': 'presence', 'duree': '1 mois'}},

            # Participation
            {'nom': 'Participant actif', 'description': 'Participer à plus de 10 cours en posant des questions', 'icone': '🙋', 'categorie': 'participation', 'points': 25, 'rarete': 'commun', 'condition_obtention': {'type': 'participation', 'min': 10}},
            {'nom': 'Intervenant brillant', 'description': 'Apporter une contribution remarquée en classe 25 fois', 'icone': '💡', 'categorie': 'participation', 'points': 40, 'rarete': 'rare', 'condition_obtention': {'type': 'participation', 'min': 25}},

            # Excellence
            {'nom': 'Perfectionniste', 'description': 'Obtenir 20/20 à un examen ou QCM', 'icone': '💎', 'categorie': 'excellence', 'points': 75, 'rarete': 'epique', 'condition_obtention': {'type': 'note_parfaite'}},
            {'nom': 'Sans faute', 'description': 'Obtenir 100% à un QCM complet', 'icone': '🎯', 'categorie': 'excellence', 'points': 60, 'rarete': 'rare', 'condition_obtention': {'type': 'qcm_parfait'}},

            # Progression
            {'nom': 'En progrès', 'description': 'Améliorer sa moyenne de 2 points en un trimestre', 'icone': '📈', 'categorie': 'progression', 'points': 35, 'rarete': 'rare', 'condition_obtention': {'type': 'progression', 'min': 2}},
            {'nom': 'Persévérant', 'description': 'Repasser un QCM après un échec et réussir', 'icone': '💪', 'categorie': 'progression', 'points': 20, 'rarete': 'commun', 'condition_obtention': {'type': 'retry_reussi'}},

            # Social
            {'nom': 'Entraideur', 'description': 'Aider 10 camarades à comprendre un concept', 'icone': '🤝', 'categorie': 'social', 'points': 30, 'rarete': 'rare', 'condition_obtention': {'type': 'entraide', 'min': 10}},
            {'nom': 'Collaborateur', 'description': 'Participer à 5 travaux de groupe', 'icone': '👥', 'categorie': 'social', 'points': 20, 'rarete': 'commun', 'condition_obtention': {'type': 'groupe', 'min': 5}},

            # Spécial
            {'nom': 'Pionnier', 'description': 'Être parmi les premiers inscrits de la plateforme', 'icone': '🚀', 'categorie': 'special', 'points': 50, 'rarete': 'legendaire', 'condition_obtention': {'type': 'early_adopter'}},
            {'nom': 'Explorateur', 'description': 'Tester toutes les fonctionnalités de la plateforme', 'icone': '🗺️', 'categorie': 'special', 'points': 40, 'rarete': 'epique', 'condition_obtention': {'type': 'all_features'}},
        ]

        badge_count = 0
        for data in badges_data:
            _, created = Badge.objects.get_or_create(nom=data['nom'], defaults=data)
            if created:
                badge_count += 1

        if badge_count > 0:
            self.stdout.write(self.style.SUCCESS(f'{badge_count} badges créés avec succès.'))
        else:
            self.stdout.write(self.style.SUCCESS('Les badges existent déjà.'))
