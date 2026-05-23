from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_alter_user_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='type_candidat',
            field=models.CharField(
                blank=True,
                choices=[
                    ('academie', 'Candidat Académie Numérique'),
                    ('libre', 'Candidat Libre'),
                    ('non_defini', 'Non défini'),
                ],
                db_index=True,
                default='non_defini',
                max_length=20,
                verbose_name='type de candidat',
            ),
        ),
    ]
