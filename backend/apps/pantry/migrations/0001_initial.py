import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('families', '0001_initial'),
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PantryItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(
                    choices=[('present', 'Presente'), ('finished', 'Terminato')],
                    default='present',
                    max_length=10,
                )),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('note', models.CharField(blank=True, max_length=500)),
                ('family', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pantry_items',
                    to='families.family',
                )),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pantry_items',
                    to='products.product',
                )),
                ('updated_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='pantry_updates',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'prodotto dispensa',
                'verbose_name_plural': 'prodotti dispensa',
                'ordering': ('product__name',),
            },
        ),
        migrations.AlterUniqueTogether(
            name='pantryitem',
            unique_together={('family', 'product')},
        ),
        migrations.CreateModel(
            name='PantryHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[('added', 'Aggiunto'), ('finished', 'Terminato'), ('updated', 'Aggiornato')],
                    max_length=10,
                )),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('pantry_item', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='history',
                    to='pantry.pantryitem',
                )),
                ('performed_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='pantry_history',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'storico dispensa',
                'verbose_name_plural': 'storico dispensa',
                'ordering': ('-timestamp',),
            },
        ),
    ]
