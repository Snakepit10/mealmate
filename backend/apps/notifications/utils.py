"""
Funzioni helper per creare notifiche in-app e inviare push Web.
"""
import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def create_notification(user, notif_type: str, title: str, message: str,
                        related_type: str = '', related_id=None):
    """
    Crea una Notification in-app e la invia via WebSocket al client connesso.
    """
    from .models import Notification
    notif = Notification.objects.create(
        user=user,
        type=notif_type,
        title=title,
        message=message,
        related_type=related_type,
        related_id=related_id,
    )
    _send_ws(user, notif)
    return notif


def _send_ws(user, notif):
    """Invia la notifica via WebSocket al canale personale dell'utente."""
    try:
        channel_layer = get_channel_layer()
        group_name = f'notifications_{user.id}'
        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'notification_new',
            'data': {
                'type': 'notification.new',
                'data': {
                    'id': str(notif.id),
                    'notif_type': notif.type,
                    'title': notif.title,
                    'message': notif.message,
                    'created_at': notif.created_at.isoformat(),
                },
            },
        })
    except Exception as e:
        logger.warning(f'WebSocket push fallito per utente {user.id}: {e}')


def send_push_notification(user, title: str, body: str, data: dict = None):
    """
    Invia una Web Push notification a tutte le sottoscrizioni attive dell'utente.
    Usa pywebpush. Richiede VAPID_PRIVATE_KEY e VAPID_CLAIMS in settings.
    """
    from django.conf import settings
    from .models import PushSubscription

    subscriptions = PushSubscription.objects.filter(user=user)
    if not subscriptions.exists():
        return

    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.warning('pywebpush non installato, skip push notification.')
        return

    payload = json.dumps({'title': title, 'body': body, **(data or {})})
    vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
    vapid_claims = getattr(settings, 'VAPID_CLAIMS', None)

    if not vapid_private_key or not vapid_claims:
        logger.warning('VAPID_PRIVATE_KEY o VAPID_CLAIMS non configurati, skip push.')
        return

    dead_endpoints = []
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=payload,
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims,
            )
        except WebPushException as e:
            if e.response and e.response.status_code in (404, 410):
                dead_endpoints.append(sub.id)
            else:
                logger.warning(f'Push fallita per {sub.endpoint[:60]}: {e}')

    if dead_endpoints:
        PushSubscription.objects.filter(id__in=dead_endpoints).delete()


def notify_family_members(family, notif_type: str, title: str, message: str,
                          related_type: str = '', related_id=None,
                          exclude_user=None):
    """
    Crea notifiche in-app per tutti i membri registrati di una famiglia.
    """
    from apps.families.models import FamilyMember
    members = FamilyMember.objects.filter(
        family=family, is_registered=True, user__isnull=False
    ).select_related('user')
    for member in members:
        if exclude_user and member.user == exclude_user:
            continue
        settings_obj = _get_settings(member.user)
        if not _is_type_enabled(settings_obj, notif_type):
            continue
        notif = create_notification(
            member.user, notif_type, title, message, related_type, related_id
        )
        send_push_notification(member.user, title, message)


def _get_settings(user):
    from .models import NotificationSettings
    settings_obj, _ = NotificationSettings.objects.get_or_create(user=user)
    return settings_obj


def _is_type_enabled(settings_obj, notif_type: str) -> bool:
    from .models import Notification
    mapping = {
        Notification.TYPE_EXPIRY: settings_obj.expiry_enabled,
        Notification.TYPE_MISSING_INGREDIENT: settings_obj.missing_ingredient_enabled,
        Notification.TYPE_SHOPPING_UPDATED: settings_obj.shopping_updated_enabled,
        Notification.TYPE_MENU_TODAY: settings_obj.menu_today_enabled,
        Notification.TYPE_RECIPE_RATED: settings_obj.recipe_rated_enabled,
        Notification.TYPE_RECIPE_SHARED: settings_obj.recipe_shared_enabled,
        Notification.TYPE_MEMBER_JOINED: True,
    }
    return mapping.get(notif_type, True)
