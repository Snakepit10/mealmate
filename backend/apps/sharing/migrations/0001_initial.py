import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('families', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SharedResource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('resource_type', models.CharField(
                    choices=[
                        ('recipe', 'Ricetta'), ('calendar', 'Calendario'),
                        ('shopping', 'Lista spesa'), ('pantry', 'Dispensa'),
                    ],
                    max_length=10,
                )),
                ('resource_id', models.UUIDField()),
                ('permission', models.CharField(
                    choices=[('read', 'Lettura'), ('write', 'Scrittura')],
                    default='read',
                    max_length=5,
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'In attesa'), ('accepted', 'Accettato'), ('rejected', 'Rifiutato'),
                    ],
                    default='pending',
                    max_length=10,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('shared_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shares_sent',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('shared_with_family', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shares_received',
                    to='families.family',
                )),
                ('shared_with_user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shares_received',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'risorsa condivisa',
                'verbose_name_plural': 'risorse condivise',
                'ordering': ('-created_at',),
            },
        ),
    ]
