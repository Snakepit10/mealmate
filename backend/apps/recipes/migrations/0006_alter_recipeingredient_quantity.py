from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_recipe_cover_image_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipeingredient',
            name='quantity',
            field=models.CharField(
                blank=True,
                max_length=50,
                help_text='Quantità libera, es. "350 g", "2 porzioni", "q.b."',
            ),
        ),
    ]
