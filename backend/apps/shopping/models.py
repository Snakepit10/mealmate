from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class ShoppingItem(TimeStampedModel):
    family = models.ForeignKey(
        'families.Family',
        on_delete=models.CASCADE,
        related_name='shopping_items',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='shopping_items',
    )
    quantity = models.CharField(max_length=50, null=True, blank=True)
    unit = models.ForeignKey(
        'products.UnitOfMeasure',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shopping_items',
    )
    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shopping_items',
    )
    store_aisle = models.ForeignKey(
        'stores.StoreAisle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shopping_items',
    )
    checked = models.BooleanField(default=False)
    unavailable = models.BooleanField(default=False)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='shopping_additions',
    )
    added_automatically = models.BooleanField(default=False)
    # Traccia da quale ricetta/data pasto è stato aggiunto automaticamente
    source_recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shopping_items',
    )
    source_meal_date = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'prodotto lista spesa'
        verbose_name_plural = 'prodotti lista spesa'
        ordering = ('store_aisle__order', 'product__name')

    def __str__(self):
        return f'{self.product.name} — {self.family.name}'


class ShoppingHistory(models.Model):
    family = models.ForeignKey(
        'families.Family',
        on_delete=models.CASCADE,
        related_name='shopping_history',
    )
    completed_at = models.DateTimeField(auto_now_add=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='completed_shoppings',
    )
    items = models.JSONField()  # snapshot degli items al momento del completamento

    class Meta:
        verbose_name = 'spesa completata'
        verbose_name_plural = 'spese completate'
        ordering = ('-completed_at',)

    def __str__(self):
        return f'Spesa {self.family.name} — {self.completed_at:%Y-%m-%d %H:%M}'
