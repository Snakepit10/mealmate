import uuid
from django.db import migrations


STORE_CATEGORIES = [
    ('supermarket', '🛒'),
    ('pharmacy', '💊'),
    ('poultry', '🐔'),
    ('fishmonger', '🐟'),
    ('bakery', '🍞'),
    ('butcher', '🥩'),
    ('market', '🏪'),
    ('other', '📦'),
]


def load_store_categories(apps, schema_editor):
    StoreCategory = apps.get_model('stores', 'StoreCategory')
    for name, icon in STORE_CATEGORIES:
        StoreCategory.objects.get_or_create(
            name=name,
            defaults={'icon': icon, 'id': uuid.uuid4()},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_store_categories, migrations.RunPython.noop),
    ]
