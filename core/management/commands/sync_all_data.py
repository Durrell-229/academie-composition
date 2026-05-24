from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Synchroniser les données de base vers la production'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Synchronisation des données de base...')

        with transaction.atomic():
            self.create_superuser()
            self.create_matieres()

        self.stdout.write(self.style.SUCCESS('✅ Synchronisation terminée!'))

    def create_superuser(self):
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                email='admin@academie-numerique.fr',
                password='admin2025',
                first_name='Admin',
                last_name='Système',
            )
            self.stdout.write('  ✅ Superuser créé')
        else:
            self.stdout.write('  ℹ️  Superuser déjà existant')

    def create_matieres(self):
        try:
            from core.models import Matiere
        except ImportError:
            self.stdout.write('  ⚠️  Modèle Matiere non disponible, ignoré')
            return

        matieres = [
            ('MATHS', 'Mathématiques', '#6366F1'),
            ('FRANCAIS', 'Français', '#3B82F6'),
            ('PC', 'Physique-Chimie', '#F59E0B'),
            ('SVT', 'Sciences de la Vie et de la Terre', '#10B981'),
            ('HIST_GEO', 'Histoire et Géographie', '#8B5CF6'),
            ('ANGLAIS', 'Anglais', '#06B6D4'),
        ]

        for code, nom, couleur in matieres:
            _, created = Matiere.objects.get_or_create(
                code=code,
                defaults={'nom': nom, 'couleur': couleur}
            )
            if created:
                self.stdout.write(f'  ✅ Matière créée: {nom}')
