import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('families', '0001_initial'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoreCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(
                    choices=[
                        ('supermarket', 'Supermercato'), ('pharmacy', 'Farmacia'),
                        ('poultry', 'Polleria'), ('fishmonger', 'Pescheria'),
                        ('bakery', 'Panetteria'), ('butcher', 'Macelleria'),
                        ('market', 'Mercato'), ('other', 'Altro'),
                    ],
                    max_length=20,
                    unique=True,
                )),
                ('icon', models.CharField(blank=True, max_length=50)),
            ],
            options={
                'verbose_name': 'categoria negozio',
                'verbose_name_plural': 'categorie negozio',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=150)),
                ('is_default', models.BooleanField(default=False)),
                ('family', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='stores',
                    to='families.family',
                )),
                ('store_category', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='stores',
                    to='stores.storecategory',
                )),
            ],
            options={
                'verbose_name': 'negozio',
                'verbose_name_plural': 'negozi',
                'ordering': ('-is_default', 'name'),
            },
        ),
        migrations.CreateModel(
            name='StoreAisle',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('store', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='aisles',
                    to='stores.store',
                )),
            ],
            options={
                'verbose_name': 'corsia',
                'verbose_name_plural': 'corsie',
                'ordering': ('order', 'name'),
            },
        ),
        migrations.CreateModel(
            name='ProductStore',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('preferred', models.BooleanField(default=False)),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='store_links',
                    to='products.product',
                )),
                ('store', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='product_links',
                    to='stores.store',
                )),
                ('store_aisle', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='product_links',
                    to='stores.storeaisle',
                )),
            ],
            options={
                'verbose_name': 'prodotto-negozio',
                'verbose_name_plural': 'prodotti-negozio',
            },
        ),
        migrations.AlterUniqueTogether(
            name='productstore',
            unique_together={('product', 'store')},
        ),
    ]
