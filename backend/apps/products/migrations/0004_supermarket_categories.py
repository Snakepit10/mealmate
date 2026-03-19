"""
Replace generic categories with supermarket-style sections.
Alimentari = is_food=True, Non alimentari = is_food=False.
"""
import uuid
from django.db import migrations

# (name, icon, order, is_food)
SUPERMARKET_CATEGORIES = [
    # ── ALIMENTARI ──────────────────────────────────────
    ('Frutta e verdura',       '🥦', 1,  True),
    ('Pane e prodotti da forno','🍞', 2,  True),
    ('Colazione e cereali',    '🥣', 3,  True),
    ('Macelleria',             '🥩', 4,  True),
    ('Pesce e surgelati',      '🐟', 5,  True),
    ('Salumi e formaggi',      '🧀', 6,  True),
    ('Latticini e uova',       '🥛', 7,  True),
    ('Pasta, riso e legumi',   '🍝', 8,  True),
    ('Conserve e sughi',       '🫙', 9,  True),
    ('Condimenti e spezie',    '🧂', 10, True),
    ('Snack e dolci',          '🍫', 11, True),
    ('Bevande',                '🥤', 12, True),
    ('Surgelati',              '❄️', 13, True),
    ('Prodotti biologici',     '🌿', 14, True),
    # ── NON ALIMENTARI ─────────────────────────────────
    ('Igiene personale',       '🧴', 20, False),
    ('Prodotti per il bagno',  '🚿', 21, False),
    ('Pulizia casa',           '🧹', 22, False),
    ('Detersivi e lavanderia', '🧺', 23, False),
    ('Farmaci e parafarmacia', '💊', 24, False),
    ('Cartoleria e ufficio',   '📎', 25, False),
    ('Animali domestici',      '🐾', 26, False),
    ('Altro',                  '📦', 99, True),
]


def replace_categories(apps, schema_editor):
    ProductCategory = apps.get_model('products', 'ProductCategory')

    # Mappa vecchio nome → nuovo nome per aggiornare i prodotti già categorizzati
    rename_map = {
        'Carne e pesce': 'Macelleria',
        'Condimenti e salse': 'Conserve e sughi',
        'Igiene personale': 'Igiene personale',
        'Pulizia casa': 'Pulizia casa',
        'Farmaci': 'Farmaci e parafarmacia',
    }

    # Crea o aggiorna le nuove categorie
    category_objects = {}
    for name, icon, order, is_food in SUPERMARKET_CATEGORIES:
        obj, _ = ProductCategory.objects.update_or_create(
            name=name,
            defaults={'icon': icon, 'order': order, 'is_food': is_food},
        )
        category_objects[name] = obj

    # Migra i prodotti dalle vecchie categorie alle nuove
    Product = apps.get_model('products', 'Product')
    for old_name, new_name in rename_map.items():
        old_cats = ProductCategory.objects.filter(name=old_name)
        if old_cats.exists() and new_name in category_objects:
            Product.objects.filter(category__in=old_cats).update(
                category=category_objects[new_name]
            )

    # Elimina le categorie obsolete (non presenti nella nuova lista)
    new_names = [name for name, *_ in SUPERMARKET_CATEGORIES]
    ProductCategory.objects.exclude(name__in=new_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_category_is_food'),
    ]

    operations = [
        migrations.RunPython(replace_categories, migrations.RunPython.noop),
    ]
