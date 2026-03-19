import uuid
from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_EXPIRY = 'expiry'
    TYPE_MISSING_INGREDIENT = 'missing_ingredient'
    TYPE_SHOPPING_UPDATED = 'shopping_updated'
    TYPE_MENU_TODAY = 'menu_today'
    TYPE_MEMBER_JOINED = 'member_joined'
    TYPE_RECIPE_RATED = 'recipe_rated'
    TYPE_RECIPE_SHARED = 'recipe_shared'
    TYPE_CHOICES = [
        (TYPE_EXPIRY, 'Scadenza prodotto'),
        (TYPE_MISSING_INGREDIENT, 'Ingrediente mancante'),
        (TYPE_SHOPPING_UPDATED, 'Lista spesa aggiornata'),
        (TYPE_MENU_TODAY, 'Menu di oggi'),
        (TYPE_MEMBER_JOINED, 'Nuovo membro'),
        (TYPE_RECIPE_RATED, 'Ricetta valutata'),
        (TYPE_RECIPE_SHARED, 'Ricetta condivisa'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    type = models.CharField(max_length=25, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    read = models.BooleanField(default=False)
    related_type = models.CharField(max_length=50, blank=True)
    related_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'notifica'
        verbose_name_plural = 'notifiche'
        ordering = ('-created_at',)

    def __str__(self):
        return f'[{self.type}] {self.title} → {self.user.email}'


class PushSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.TextField()
    auth = models.TextField()
    user_agent = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'sottoscrizione push'
        verbose_name_plural = 'sottoscrizioni push'

    def __str__(self):
        return f'{self.user.email} — {self.endpoint[:60]}…'


class NotificationSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings',
    )
    expiry_enabled = models.BooleanField(default=True)
    expiry_days_before = models.PositiveSmallIntegerField(default=2)
    missing_ingredient_enabled = models.BooleanField(default=True)
    shopping_updated_enabled = models.BooleanField(default=True)
    menu_today_enabled = models.BooleanField(default=True)
    menu_today_time = models.TimeField(default='08:00')
    recipe_rated_enabled = models.BooleanField(default=True)
    recipe_shared_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'impostazioni notifiche'
        verbose_name_plural = 'impostazioni notifiche'

    def __str__(self):
        return f'Impostazioni notifiche — {self.user.email}'
