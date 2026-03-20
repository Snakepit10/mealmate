from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_alter_reciperating_id_alter_recipereport_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cook_time',
            field=models.PositiveSmallIntegerField(blank=True, help_text='Minuti', null=True),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='prep_time',
            field=models.PositiveSmallIntegerField(blank=True, help_text='Minuti', null=True),
        ),
    ]
