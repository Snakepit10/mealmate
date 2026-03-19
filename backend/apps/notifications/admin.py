from django.contrib import admin

from .models import Notification, NotificationSettings, PushSubscription


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'title', 'read', 'created_at')
    list_filter = ('type', 'read')
    search_fields = ('user__email', 'title', 'message')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('user',)


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'expiry_enabled', 'menu_today_enabled', 'menu_today_time')
    raw_id_fields = ('user',)


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('user',)
