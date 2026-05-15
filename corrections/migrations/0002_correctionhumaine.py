import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('corrections', '0001_initial'),
        ('compositions', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CorrectionHumaine',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('statut', models.CharField(
                    choices=[
                        ('assignee', 'Assignée'),
                        ('en_cours', 'En cours'),
                        ('terminee', 'Terminée'),
                        ('validee', 'Validée'),
                    ],
                    default='assignee', max_length=20, verbose_name='statut'
                )),
                ('note', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='note')),
                ('note_sur', models.DecimalField(decimal_places=2, default=20, max_digits=5, verbose_name='note sur')),
                ('commentaire', models.TextField(blank=True, verbose_name='commentaire global')),
                ('details_json', models.JSONField(default=list, verbose_name='détails par critère')),
                ('date_limite', models.DateTimeField(blank=True, null=True, verbose_name='date limite')),
                ('rendu_at', models.DateTimeField(blank=True, null=True, verbose_name='rendu le')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('session', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='correction_humaine',
                    to='compositions.compositionsession',
                    verbose_name='session'
                )),
                ('correcteur', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='corrections_humaines_assignees',
                    to=settings.AUTH_USER_MODEL, verbose_name='correcteur'
                )),
                ('assigne_par', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='corrections_humaines_assignees_par',
                    to=settings.AUTH_USER_MODEL, verbose_name='assigné par'
                )),
            ],
            options={
                'verbose_name': 'correction humaine',
                'verbose_name_plural': 'corrections humaines',
                'ordering': ['-created_at'],
            },
        ),
    ]
