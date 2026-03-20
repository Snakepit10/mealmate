from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_alter_recipe_cook_time_alter_recipe_prep_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='cover_image_url',
            field=models.URLField(
                blank=True,
                help_text="URL esterno immagine copertina (fallback quando non c'è cover_image)",
            ),
        ),
    ]
