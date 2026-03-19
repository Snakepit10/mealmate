import uuid
from django.db import migrations

CATEGORIES_L1 = [
    ('Colazione', 1),
    ('Antipasti', 2),
    ('Primi', 3),
    ('Secondi', 4),
    ('Contorni', 5),
    ('Dolci', 6),
    ('Bevande', 7),
    ('Snack', 8),
]

# (nome, parent_name)
CATEGORIES_L2 = [
    ('Carne', 'Secondi'),
    ('Pesce', 'Secondi'),
    ('Vegetariano', 'Secondi'),
    ('Vegano', 'Secondi'),
    ('Uova', 'Secondi'),
]


def load_recipe_categories(apps, schema_editor):
    RecipeCategory = apps.get_model('recipes', 'RecipeCategory')
    parent_map = {}

    for name, order in CATEGORIES_L1:
        cat, _ = RecipeCategory.objects.get_or_create(
            name=name, level=1,
            defaults={'order': order, 'id': uuid.uuid4()},
        )
        parent_map[name] = cat

    for name, parent_name in CATEGORIES_L2:
        parent = parent_map.get(parent_name)
        RecipeCategory.objects.get_or_create(
            name=name, level=2,
            defaults={'parent': parent, 'order': 0, 'id': uuid.uuid4()},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_recipe_categories, migrations.RunPython.noop),
    ]
