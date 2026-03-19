import uuid
from django.conf import settings
from django.db import models


class SharedResource(models.Model):
    RESOURCE_RECIPE = 'recipe'
    RESOURCE_CALENDAR = 'calendar'
    RESOURCE_SHOPPING = 'shopping'
    RESOURCE_PANTRY = 'pantry'
    RESOURCE_TYPE_CHOICES = [
        (RESOURCE_RECIPE, 'Ricetta'),
        (RESOURCE_CALENDAR, 'Calendario'),
        (RESOURCE_SHOPPING, 'Lista spesa'),
        (RESOURCE_PANTRY, 'Dispensa'),
    ]

    PERMISSION_READ = 'read'
    PERMISSION_WRITE = 'write'
    PERMISSION_CHOICES = [
        (PERMISSION_READ, 'Lettura'),
        (PERMISSION_WRITE, 'Scrittura'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'In attesa'),
        (STATUS_ACCEPTED, 'Accettato'),
        (STATUS_REJECTED, 'Rifiutato'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPE_CHOICES)
    resource_id = models.UUIDField()
    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shares_sent',
    )
    shared_with_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shares_received',
    )
    shared_with_family = models.ForeignKey(
        'families.Family',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shares_received',
    )
    permission = models.CharField(max_length=5, choices=PERMISSION_CHOICES, default=PERMISSION_READ)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'risorsa condivisa'
        verbose_name_plural = 'risorse condivise'
        ordering = ('-created_at',)

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.shared_with_user and not self.shared_with_family:
            raise ValidationError('Specifica un utente o una famiglia destinataria.')
        if self.shared_with_user and self.shared_with_family:
            raise ValidationError('Specifica solo un utente o una famiglia, non entrambi.')

    def __str__(self):
        target = self.shared_with_user or self.shared_with_family
        return f'{self.resource_type}:{self.resource_id} → {target} [{self.status}]'
