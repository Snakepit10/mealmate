import uuid
from django.db import migrations


CATEGORIES = [
    ('Frutta e verdura', '🥦', 1),
    ('Carne e pesce', '🥩', 2),
    ('Latticini e uova', '🥛', 3),
    ('Pane e cereali', '🍞', 4),
    ('Pasta, riso e legumi', '🍝', 5),
    ('Surgelati', '❄️', 6),
    ('Condimenti e salse', '🫙', 7),
    ('Bevande', '🥤', 8),
    ('Snack e dolci', '🍫', 9),
    ('Pulizia casa', '🧹', 10),
    ('Igiene personale', '🧴', 11),
    ('Farmaci', '💊', 12),
    ('Altro', '📦', 99),
]

UNITS = [
    ('grammi', 'g'),
    ('kilogrammi', 'kg'),
    ('millilitri', 'ml'),
    ('litri', 'l'),
    ('pezzi', 'pz'),
    ('cucchiai', 'cucchiai'),
    ('cucchiaini', 'cucchiaini'),
    ('fette', 'fette'),
    ('spicchi', 'spicchi'),
    ('q.b.', 'q.b.'),
]


def load_initial_data(apps, schema_editor):
    ProductCategory = apps.get_model('products', 'ProductCategory')
    UnitOfMeasure = apps.get_model('products', 'UnitOfMeasure')

    for name, icon, order in CATEGORIES:
        ProductCategory.objects.get_or_create(
            name=name,
            defaults={'icon': icon, 'order': order, 'id': uuid.uuid4()},
        )

    for name, abbreviation in UNITS:
        UnitOfMeasure.objects.get_or_create(
            name=name,
            defaults={'abbreviation': abbreviation, 'is_custom': False, 'id': uuid.uuid4()},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data, migrations.RunPython.noop),
    ]
