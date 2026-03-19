from django.urls import path

from .views import (
    NotificationListView,
    NotificationReadView,
    NotificationReadAllView,
    NotificationDeleteView,
    NotificationSettingsView,
    PushRegisterView,
    PushUnregisterView,
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('read-all/', NotificationReadAllView.as_view(), name='notification-read-all'),
    path('settings/', NotificationSettingsView.as_view(), name='notification-settings'),
    path('push/register/', PushRegisterView.as_view(), name='push-register'),
    path('push/unregister/', PushUnregisterView.as_view(), name='push-unregister'),
    path('<uuid:id>/read/', NotificationReadView.as_view(), name='notification-read'),
    path('<uuid:id>/', NotificationDeleteView.as_view(), name='notification-delete'),
]
