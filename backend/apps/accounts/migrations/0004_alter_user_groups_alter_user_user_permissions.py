from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Sync the accounts.User migration state with Django 5.0's PermissionsMixin.

    Django 4.0 changed the related_name / related_query_name on the groups and
    user_permissions M2M fields from the hard-coded 'user_set' / 'user' values
    to the swappable-model pattern '%(app_label)s_%(class)s_set' /
    '%(app_label)s_%(class)s'.  For accounts.User those patterns resolve to
    'accounts_user_set' and 'accounts_user' respectively.

    Migration 0003 still carried the old 'user_set' / 'user' values, so Django
    kept reporting unapplied changes.  This migration brings the recorded state
    in line with what Django 5.0 auto-generates.
    """

    dependencies = [
        ('accounts', '0003_alter_user_fields'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(
                blank=True,
                help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
                related_name='accounts_user_set',
                related_query_name='accounts_user',
                to='auth.group',
                verbose_name='groups',
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(
                blank=True,
                help_text='Specific permissions for this user.',
                related_name='accounts_user_set',
                related_query_name='accounts_user',
                to='auth.permission',
                verbose_name='user permissions',
            ),
        ),
    ]
