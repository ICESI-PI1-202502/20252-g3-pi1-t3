from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('universitaryWellbeing', '0009_alter_notificaciones_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificaciones',
            name='leida',
            field=models.BooleanField(default=False),
        ),
    ]
