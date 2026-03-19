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
            name='RecipeCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('level', models.PositiveSmallIntegerField(
                    choices=[(1, 'Livello 1'), (2, 'Livello 2')], default=1
                )),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('parent', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='children',
                    to='recipes.recipecategory',
                )),
            ],
            options={
                'verbose_name': 'categoria ricetta',
                'verbose_name_plural': 'categorie ricetta',
                'ordering': ('order', 'name'),
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('cover_image', models.ImageField(blank=True, null=True, upload_to='recipes/')),
                ('external_link', models.URLField(blank=True)),
                ('servings', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('prep_time', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('cook_time', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('difficulty', models.CharField(
                    choices=[('easy', 'Facile'), ('medium', 'Media'), ('hard', 'Difficile')],
                    default='medium', max_length=10,
                )),
                ('is_public', models.BooleanField(default=False)),
                ('is_draft', models.BooleanField(default=True)),
                ('average_rating', models.FloatField(default=0.0)),
                ('ratings_count', models.PositiveIntegerField(default=0)),
                ('category', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='recipes',
                    to='recipes.recipecategory',
                )),
                ('family', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recipes',
                    to='families.family',
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_recipes',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('forked_from', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='forks',
                    to='recipes.recipe',
                )),
            ],
            options={
                'verbose_name': 'ricetta',
                'verbose_name_plural': 'ricette',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='RecipeIngredient',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('is_optional', models.BooleanField(default=False)),
                ('note', models.CharField(blank=True, max_length=200)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recipe_ingredients',
                    to='products.product',
                )),
                ('recipe', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ingredients',
                    to='recipes.recipe',
                )),
                ('unit', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='recipe_ingredients',
                    to='products.unitofmeasure',
                )),
            ],
            options={
                'verbose_name': 'ingrediente',
                'verbose_name_plural': 'ingredienti',
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='RecipeInstruction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('step_number', models.PositiveSmallIntegerField()),
                ('text', models.TextField()),
                ('image', models.ImageField(blank=True, null=True, upload_to='instructions/')),
                ('recipe', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='instructions',
                    to='recipes.recipe',
                )),
            ],
            options={
                'verbose_name': 'istruzione',
                'verbose_name_plural': 'istruzioni',
                'ordering': ('step_number',),
            },
        ),
        migrations.AlterUniqueTogether(
            name='recipeinstruction',
            unique_together={('recipe', 'step_number')},
        ),
        migrations.CreateModel(
            name='RecipeRating',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('score', models.PositiveSmallIntegerField()),
                ('comment', models.TextField(blank=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='ratings/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('recipe', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ratings',
                    to='recipes.recipe',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recipe_ratings',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'valutazione',
                'verbose_name_plural': 'valutazioni',
                'ordering': ('-created_at',),
            },
        ),
        migrations.AlterUniqueTogether(
            name='reciperating',
            unique_together={('recipe', 'user')},
        ),
        migrations.CreateModel(
            name='RecipeReport',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('reason', models.CharField(
                    choices=[
                        ('wrong_content', 'Contenuto errato'),
                        ('spam', 'Spam'),
                        ('inappropriate', 'Inappropriato'),
                    ],
                    max_length=20,
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'In attesa'),
                        ('reviewed', 'Revisionato'),
                        ('resolved', 'Risolto'),
                    ],
                    default='pending',
                    max_length=10,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recipe', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reports',
                    to='recipes.recipe',
                )),
                ('reported_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recipe_reports',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'segnalazione ricetta',
                'verbose_name_plural': 'segnalazioni ricette',
            },
        ),
        migrations.AlterUniqueTogether(
            name='recipereport',
            unique_together={('recipe', 'reported_by')},
        ),
    ]
