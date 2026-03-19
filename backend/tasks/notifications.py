from datetime import date, timedelta
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(name='tasks.check_missing_ingredients')
def check_missing_ingredients():
    """
    Ogni sera alle 20:00.
    Trova tutti i MealEntry di domani con recipe, verifica ingredienti in dispensa,
    e invia notifica push se mancano ingredienti.
    """
    from apps.calendar.models import MealEntry
    from apps.pantry.models import PantryItem
    from apps.notifications.models import Notification, NotificationSettings
    from apps.notifications.utils import create_notification, send_push_notification
    from apps.families.models import FamilyMember

    tomorrow = date.today() + timedelta(days=1)

    entries = (
        MealEntry.objects
        .filter(slot__date=tomorrow, recipe__isnull=False)
        .select_related('slot__calendar__family', 'recipe')
        .prefetch_related('recipe__ingredients__product')
    )

    # Raggruppa per famiglia
    family_entries = {}
    for entry in entries:
        fid = entry.slot.calendar.family_id
        family_entries.setdefault(fid, {'family': entry.slot.calendar.family, 'entries': []})
        family_entries[fid]['entries'].append(entry)

    for family_id, data in family_entries.items():
        family = data['family']
        present_ids = set(
            PantryItem.objects.filter(
                family=family, status=PantryItem.STATUS_PRESENT
            ).values_list('product_id', flat=True)
        )

        all_missing = []
        for entry in data['entries']:
            required = [i for i in entry.recipe.ingredients.all() if not i.is_optional]
            missing = [i.product.name for i in required if i.product_id not in present_ids]
            if missing:
                all_missing.extend(missing)

        if not all_missing:
            continue

        members = FamilyMember.objects.filter(
            family=family, is_registered=True, user__isnull=False
        ).select_related('user')

        unique_missing = list(dict.fromkeys(all_missing))  # dedup preservando ordine
        msg = f'Ingredienti mancanti per domani: {", ".join(unique_missing[:5])}'
        if len(unique_missing) > 5:
            msg += f' e altri {len(unique_missing) - 5}.'

        for member in members:
            try:
                ns, _ = NotificationSettings.objects.get_or_create(user=member.user)
                if not ns.missing_ingredient_enabled:
                    continue
                create_notification(
                    user=member.user,
                    notif_type=Notification.TYPE_MISSING_INGREDIENT,
                    title='Ingredienti mancanti per domani',
                    message=msg,
                )
                send_push_notification(member.user, 'Ingredienti mancanti', msg)
            except Exception as e:
                logger.error(f'Errore notifica ingredienti per utente {member.user_id}: {e}')

    logger.info(f'check_missing_ingredients: processate {len(family_entries)} famiglie.')


@shared_task(name='tasks.send_daily_menu')
def send_daily_menu():
    """
    Ogni mattina all'orario configurato dall'utente (default 08:00).
    Trova tutti i MealEntry di oggi, raggruppa per famiglia,
    invia notifica push con riepilogo pasti del giorno.
    """
    from apps.calendar.models import MealEntry
    from apps.notifications.models import Notification, NotificationSettings
    from apps.notifications.utils import create_notification, send_push_notification
    from apps.families.models import FamilyMember

    today = date.today()

    entries = (
        MealEntry.objects
        .filter(slot__date=today)
        .select_related('slot__calendar__family', 'recipe')
    )

    family_entries = {}
    for entry in entries:
        fid = entry.slot.calendar.family_id
        family_entries.setdefault(fid, {'family': entry.slot.calendar.family, 'entries': []})
        family_entries[fid]['entries'].append(entry)

    for family_id, data in family_entries.items():
        family = data['family']
        meals = []
        for entry in data['entries']:
            label = entry.recipe.title if entry.recipe else entry.note
            meal_type = entry.slot.get_meal_type_display()
            meals.append(f'{meal_type}: {label}')

        if not meals:
            continue

        msg = ' | '.join(meals)

        members = FamilyMember.objects.filter(
            family=family, is_registered=True, user__isnull=False
        ).select_related('user')

        for member in members:
            try:
                ns, _ = NotificationSettings.objects.get_or_create(user=member.user)
                if not ns.menu_today_enabled:
                    continue
                create_notification(
                    user=member.user,
                    notif_type=Notification.TYPE_MENU_TODAY,
                    title=f'Menu di oggi — {today.strftime("%d/%m")}',
                    message=msg,
                )
                send_push_notification(member.user, 'Menu di oggi', msg)
            except Exception as e:
                logger.error(f'Errore notifica menu per utente {member.user_id}: {e}')

    logger.info(f'send_daily_menu: processate {len(family_entries)} famiglie.')
