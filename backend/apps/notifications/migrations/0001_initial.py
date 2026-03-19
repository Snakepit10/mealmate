import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('type', models.CharField(
                    choices=[
                        ('expiry', 'Scadenza prodotto'),
                        ('missing_ingredient', 'Ingrediente mancante'),
                        ('shopping_updated', 'Lista spesa aggiornata'),
                        ('menu_today', 'Menu di oggi'),
                        ('member_joined', 'Nuovo membro'),
                        ('recipe_rated', 'Ricetta valutata'),
                        ('recipe_shared', 'Ricetta condivisa'),
                    ],
                    max_length=25,
                )),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('read', models.BooleanField(default=False)),
                ('related_type', models.CharField(blank=True, max_length=50)),
                ('related_id', models.UUIDField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'notifica',
                'verbose_name_plural': 'notifiche',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='PushSubscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('endpoint', models.URLField(max_length=500, unique=True)),
                ('p256dh', models.TextField()),
                ('auth', models.TextField()),
                ('user_agent', models.CharField(blank=True, max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='push_subscriptions',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'sottoscrizione push',
                'verbose_name_plural': 'sottoscrizioni push',
            },
        ),
        migrations.CreateModel(
            name='NotificationSettings',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('expiry_enabled', models.BooleanField(default=True)),
                ('expiry_days_before', models.PositiveSmallIntegerField(default=2)),
                ('missing_ingredient_enabled', models.BooleanField(default=True)),
                ('shopping_updated_enabled', models.BooleanField(default=True)),
                ('menu_today_enabled', models.BooleanField(default=True)),
                ('menu_today_time', models.TimeField(default='08:00')),
                ('recipe_rated_enabled', models.BooleanField(default=True)),
                ('recipe_shared_enabled', models.BooleanField(default=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notification_settings',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'impostazioni notifiche',
                'verbose_name_plural': 'impostazioni notifiche',
            },
        ),
    ]
