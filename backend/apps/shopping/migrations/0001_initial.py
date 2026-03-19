import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('families', '0001_initial'),
        ('products', '0001_initial'),
        ('stores', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        # recipes dipendenza aggiunta dopo (punto 9) — nullable quindi safe
    ]

    operations = [
        migrations.CreateModel(
            name='ShoppingItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('checked', models.BooleanField(default=False)),
                ('unavailable', models.BooleanField(default=False)),
                ('added_automatically', models.BooleanField(default=False)),
                ('source_meal_date', models.DateField(blank=True, null=True)),
                ('note', models.CharField(blank=True, max_length=500)),
                ('added_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='shopping_additions',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('family', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shopping_items',
                    to='families.family',
                )),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shopping_items',
                    to='products.product',
                )),
                ('unit', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='shopping_items',
                    to='products.unitofmeasure',
                )),
                ('store', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='shopping_items',
                    to='stores.store',
                )),
                ('store_aisle', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='shopping_items',
                    to='stores.storeaisle',
                )),
                # source_recipe aggiunto in migrazione successiva dopo recipes
            ],
            options={
                'verbose_name': 'prodotto lista spesa',
                'verbose_name_plural': 'prodotti lista spesa',
                'ordering': ('store_aisle__order', 'product__name'),
            },
        ),
        migrations.CreateModel(
            name='ShoppingHistory',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('items', models.JSONField()),
                ('family', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shopping_history',
                    to='families.family',
                )),
                ('completed_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='completed_shoppings',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'spesa completata',
                'verbose_name_plural': 'spese completate',
                'ordering': ('-completed_at',),
            },
        ),
    ]
