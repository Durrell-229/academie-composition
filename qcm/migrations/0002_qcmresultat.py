import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('qcm', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='QCMResultat',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('matiere', models.CharField(max_length=100)),
                ('classe', models.CharField(max_length=100)),
                ('theme', models.CharField(blank=True, default='', max_length=200)),
                ('note_sur_20', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('bonnes_reponses', models.PositiveIntegerField(default=0)),
                ('total_questions', models.PositiveIntegerField(default=0)),
                ('questions_data', models.JSONField(default=dict, verbose_name='détails des questions/réponses')),
                ('feedback_ia', models.JSONField(default=dict, verbose_name='feedback IA')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('eleve', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='qcm_resultats', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'résultat QCM',
                'verbose_name_plural': 'résultats QCM',
                'ordering': ['-created_at'],
            },
        ),
    ]
