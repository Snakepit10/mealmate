from django.urls import re_path
from consumers.pantry import PantryConsumer
from consumers.shopping import ShoppingConsumer
from consumers.calendar import CalendarConsumer
from consumers.notifications import NotificationConsumer

websocket_urlpatterns = [
    re_path(r'ws/families/(?P<family_id>[^/]+)/pantry/$', PantryConsumer.as_asgi()),
    re_path(r'ws/families/(?P<family_id>[^/]+)/shopping/$', ShoppingConsumer.as_asgi()),
    re_path(r'ws/families/(?P<family_id>[^/]+)/calendars/$', CalendarConsumer.as_asgi()),
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]
