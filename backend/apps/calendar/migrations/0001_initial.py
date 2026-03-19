import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('families', '0001_initial'),
        ('recipes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MealCalendar',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('color', models.CharField(default='#4CAF50', max_length=7)),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_calendars',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('family', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='calendars',
                    to='families.family',
                )),
            ],
            options={
                'verbose_name': 'calendario pasti',
                'verbose_name_plural': 'calendari pasti',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='MealSlot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField()),
                ('meal_type', models.CharField(
                    choices=[
                        ('breakfast', 'Colazione'), ('lunch', 'Pranzo'),
                        ('dinner', 'Cena'), ('snack', 'Spuntino'),
                    ],
                    max_length=10,
                )),
                ('calendar', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='slots',
                    to='calendar.mealcalendar',
                )),
            ],
            options={
                'verbose_name': 'slot pasto',
                'verbose_name_plural': 'slot pasto',
                'ordering': ('date', 'meal_type'),
            },
        ),
        migrations.AlterUniqueTogether(
            name='mealslot',
            unique_together={('calendar', 'date', 'meal_type')},
        ),
        migrations.CreateModel(
            name='MealEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('note', models.CharField(blank=True, max_length=500)),
                ('added_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='meal_additions',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('recipe', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='meal_entries',
                    to='recipes.recipe',
                )),
                ('slot', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='entries',
                    to='calendar.mealslot',
                )),
                ('assigned_members', models.ManyToManyField(
                    blank=True,
                    related_name='meal_entries',
                    to='families.familymember',
                )),
            ],
            options={
                'verbose_name': 'voce pasto',
                'verbose_name_plural': 'voci pasto',
                'ordering': ('created_at',),
            },
        ),
        migrations.CreateModel(
            name='MealCalendarShare',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('permission', models.CharField(
                    choices=[('read', 'Lettura'), ('write', 'Scrittura')],
                    default='read',
                    max_length=5,
                )),
                ('calendar', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shares',
                    to='calendar.mealcalendar',
                )),
                ('shared_with_family', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='calendar_shares',
                    to='families.family',
                )),
                ('shared_with_user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='calendar_shares',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'condivisione calendario',
                'verbose_name_plural': 'condivisioni calendario',
            },
        ),
    ]
