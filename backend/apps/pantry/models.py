from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class PantryItem(TimeStampedModel):
    STATUS_PRESENT = 'present'
    STATUS_FINISHED = 'finished'
    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Presente'),
        (STATUS_FINISHED, 'Terminato'),
    ]

    family = models.ForeignKey(
        'families.Family',
        on_delete=models.CASCADE,
        related_name='pantry_items',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='pantry_items',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PRESENT)
    expiry_date = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=500, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pantry_updates',
    )

    class Meta:
        verbose_name = 'prodotto dispensa'
        verbose_name_plural = 'prodotti dispensa'
        unique_together = [('family', 'product')]
        ordering = ('product__name',)

    def __str__(self):
        return f'{self.product.name} [{self.status}] — {self.family.name}'


class PantryHistory(models.Model):
    ACTION_ADDED = 'added'
    ACTION_FINISHED = 'finished'
    ACTION_UPDATED = 'updated'
    ACTION_CHOICES = [
        (ACTION_ADDED, 'Aggiunto'),
        (ACTION_FINISHED, 'Terminato'),
        (ACTION_UPDATED, 'Aggiornato'),
    ]

    pantry_item = models.ForeignKey(
        PantryItem,
        on_delete=models.CASCADE,
        related_name='history',
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pantry_history',
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'storico dispensa'
        verbose_name_plural = 'storico dispensa'
        ordering = ('-timestamp',)

    def __str__(self):
        return f'{self.action} — {self.pantry_item.product.name} ({self.timestamp:%Y-%m-%d})'
