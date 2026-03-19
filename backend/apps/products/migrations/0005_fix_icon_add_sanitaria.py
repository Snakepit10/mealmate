"""Fix 🫙 (U+1FAD9, poco supportato) → 🥫, e aggiunge la categoria Sanitaria."""
import uuid
from django.db import migrations


def fix_categories(apps, schema_editor):
    ProductCategory = apps.get_model('products', 'ProductCategory')
    # Fix icona conserve
    ProductCategory.objects.filter(name='Conserve e sughi').update(icon='🥫')
    # Aggiungi Sanitaria (non alimentare)
    ProductCategory.objects.get_or_create(
        name='Sanitaria',
        defaults={'icon': '🏥', 'order': 27, 'is_food': False, 'id': uuid.uuid4()},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_supermarket_categories'),
    ]

    operations = [
        migrations.RunPython(fix_categories, migrations.RunPython.noop),
    ]
