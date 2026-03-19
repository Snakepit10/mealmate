from rest_framework import serializers

from .models import Notification, NotificationSettings, PushSubscription


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = (
            'id', 'type', 'type_display', 'title', 'message',
            'read', 'related_type', 'related_id', 'created_at',
        )
        read_only_fields = fields


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = (
            'expiry_enabled', 'expiry_days_before',
            'missing_ingredient_enabled',
            'shopping_updated_enabled',
            'menu_today_enabled', 'menu_today_time',
            'recipe_rated_enabled',
            'recipe_shared_enabled',
        )


class PushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushSubscription
        fields = ('endpoint', 'p256dh', 'auth', 'user_agent')

    def validate_endpoint(self, value):
        if not value.startswith('https://'):
            raise serializers.ValidationError("L'endpoint deve essere HTTPS.")
        return value
