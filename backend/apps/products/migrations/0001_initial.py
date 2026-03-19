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
            name='ProductCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('icon', models.CharField(blank=True, max_length=50)),
                ('order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'categoria prodotto',
                'verbose_name_plural': 'categorie prodotto',
                'ordering': ('order', 'name'),
            },
        ),
        migrations.CreateModel(
            name='UnitOfMeasure',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=50)),
                ('abbreviation', models.CharField(max_length=10)),
                ('is_custom', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'unità di misura',
                'verbose_name_plural': 'unità di misura',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('brand', models.CharField(blank=True, max_length=100)),
                ('barcode', models.CharField(blank=True, max_length=30, null=True, unique=True)),
                ('type', models.CharField(
                    choices=[
                        ('food', 'Alimentare'), ('medicine', 'Farmaco'),
                        ('cleaning', 'Pulizia'), ('bathroom', 'Bagno'), ('other', 'Altro'),
                    ],
                    default='food',
                    max_length=20,
                )),
                ('image_url', models.URLField(blank=True)),
                ('nutriscore', models.CharField(
                    blank=True,
                    choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E')],
                    max_length=1,
                    null=True,
                )),
                ('off_id', models.CharField(blank=True, max_length=50)),
                ('source', models.CharField(
                    choices=[
                        ('manual', 'Manuale'), ('open_food_facts', 'Open Food Facts'), ('import', 'Importazione'),
                    ],
                    default='manual',
                    max_length=20,
                )),
                ('category', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='products',
                    to='products.productcategory',
                )),
                ('default_unit', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='products',
                    to='products.unitofmeasure',
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_products',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'prodotto',
                'verbose_name_plural': 'prodotti',
                'ordering': ('name',),
            },
        ),
    ]
