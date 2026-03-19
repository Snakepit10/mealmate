"""
Helper per inviare eventi WebSocket ai gruppi Channels dall'interno delle view Django (sync).
"""
from asgiref.sync import async_to_sync
try:
    from channels.layers import get_channel_layer
except ImportError:
    get_channel_layer = lambda: None


def send_family_event(group_prefix: str, family_id: str, event_type: str, data: dict):
    """
    Invia un evento al gruppo WebSocket di una famiglia.

    Args:
        group_prefix: 'pantry' | 'shopping' | 'calendar'
        family_id: UUID della famiglia (stringa)
        event_type: es. 'pantry.item_finished'
        data: payload dell'evento
    """
    channel_layer = get_channel_layer()
    group_name = f'{group_prefix}_{family_id}'
    message = {
        'type': f'{group_prefix}_updated',   # deve corrispondere al metodo nel consumer
        'data': {
            'type': event_type,
            'data': data,
        },
    }
    async_to_sync(channel_layer.group_send)(group_name, message)
