from django.core.management.base import BaseCommand
from core.models import Matiere
from core.constants import MATIERE_CHOICES

MATIERES_DATA = [
    {'code': 'MATHS',    'nom': 'MATHS',    'couleur': '#6366F1', 'icone': 'fa-calculator',       'niveaux': ['primaire', 'secondaire', 'universitaire']},
    {'code': 'PC',       'nom': 'PC',       'couleur': '#F59E0B', 'icone': 'fa-flask',             'niveaux': ['secondaire']},
    {'code': 'SVT',      'nom': 'SVT',      'couleur': '#10B981', 'icone': 'fa-leaf',              'niveaux': ['secondaire']},
    {'code': 'FRANCAIS', 'nom': 'FRANCAIS', 'couleur': '#3B82F6', 'icone': 'fa-book',             'niveaux': ['primaire', 'secondaire']},
    {'code': 'ANGLAIS',  'nom': 'ANGLAIS',  'couleur': '#EF4444', 'icone': 'fa-language',         'niveaux': ['primaire', 'secondaire']},
    {'code': 'HIST_GEO', 'nom': 'HIST_GEO', 'couleur': '#8B5CF6', 'icone': 'fa-globe',           'niveaux': ['secondaire']},
    {'code': 'PHILO',    'nom': 'PHILO',    'couleur': '#EC4899', 'icone': 'fa-brain',             'niveaux': ['secondaire']},
    {'code': 'ESPAGNOL', 'nom': 'ESPAGNOL', 'couleur': '#F97316', 'icone': 'fa-language',         'niveaux': ['secondaire']},
    {'code': 'ALLEMAND', 'nom': 'ALLEMAND', 'couleur': '#6B7280', 'icone': 'fa-language',         'niveaux': ['secondaire']},
    {'code': 'TIC',      'nom': 'TIC',      'couleur': '#06B6D4', 'icone': 'fa-computer',         'niveaux': ['primaire', 'secondaire']},
]


class Command(BaseCommand):
    help = 'Initialise les matieres par defaut dans la base de donnees'

    def handle(self, *args, **options):
        created = 0
        for data in MATIERES_DATA:
            obj, is_new = Matiere.objects.get_or_create(
                code=data['code'],
                defaults={
                    'nom': data['nom'],
                    'couleur': data['couleur'],
                    'icone': data['icone'],
                    'niveaux': data['niveaux'],
                    'is_active': True,
                }
            )
            if is_new:
                created += 1

        total = Matiere.objects.count()
        if created:
            self.stdout.write(self.style.SUCCESS(f'{created} matiere(s) creee(s). Total : {total}'))
        else:
            self.stdout.write(f'Matieres deja presentes ({total} au total). Rien a faire.')
