from datetime import date, timedelta
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(name='tasks.check_expiring_products')
def check_expiring_products():
    """
    Ogni mattina alle 07:00.
    Trova tutti i PantryItem con expiry_date entro N giorni (N da NotificationSettings)
    e invia notifica push + in-app a tutti i membri della famiglia.
    """
    from apps.pantry.models import PantryItem
    from apps.notifications.models import Notification, NotificationSettings
    from apps.notifications.utils import create_notification, send_push_notification
    from apps.families.models import FamilyMember

    today = date.today()
    # Recupera tutti i pantry item con scadenza imminente (status=present)
    expiring_items = (
        PantryItem.objects
        .filter(
            status=PantryItem.STATUS_PRESENT,
            expiry_date__isnull=False,
            expiry_date__gte=today,
        )
        .select_related('product', 'family')
    )

    # Raggruppa per famiglia
    family_items = {}
    for item in expiring_items:
        family_items.setdefault(item.family_id, {'family': item.family, 'items': []})
        family_items[item.family_id]['items'].append(item)

    for family_id, data in family_items.items():
        family = data['family']
        members = FamilyMember.objects.filter(
            family=family, is_registered=True, user__isnull=False
        ).select_related('user')

        for member in members:
            try:
                ns, _ = NotificationSettings.objects.get_or_create(user=member.user)
                if not ns.expiry_enabled:
                    continue
                threshold = today + timedelta(days=ns.expiry_days_before)
                # Filtra solo gli items entro la soglia dell'utente
                relevant = [i for i in data['items'] if i.expiry_date <= threshold]
                if not relevant:
                    continue

                for item in relevant:
                    days_left = (item.expiry_date - today).days
                    if days_left == 0:
                        msg = f'{item.product.name} scade oggi!'
                    else:
                        msg = f'{item.product.name} scade tra {days_left} giorni ({item.expiry_date}).'

                    notif = create_notification(
                        user=member.user,
                        notif_type=Notification.TYPE_EXPIRY,
                        title='Prodotto in scadenza',
                        message=msg,
                        related_type='pantry_item',
                        related_id=item.id,
                    )
                    send_push_notification(member.user, 'Prodotto in scadenza', msg)
            except Exception as e:
                logger.error(f'Errore notifica scadenza per utente {member.user_id}: {e}')

    logger.info(f'check_expiring_products: processate {len(family_items)} famiglie.')
