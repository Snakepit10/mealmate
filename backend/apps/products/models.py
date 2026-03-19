from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class ProductCategory(TimeStampedModel):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)  # es. emoji o nome icona
    order = models.PositiveSmallIntegerField(default=0)
    is_food = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'categoria prodotto'
        verbose_name_plural = 'categorie prodotto'
        ordering = ('order', 'name')

    def __str__(self):
        return self.name


class UnitOfMeasure(TimeStampedModel):
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=10)
    is_custom = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'unità di misura'
        verbose_name_plural = 'unità di misura'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} ({self.abbreviation})'


class Product(TimeStampedModel):
    TYPE_FOOD = 'food'
    TYPE_MEDICINE = 'medicine'
    TYPE_CLEANING = 'cleaning'
    TYPE_BATHROOM = 'bathroom'
    TYPE_OTHER = 'other'
    TYPE_CHOICES = [
        (TYPE_FOOD, 'Alimentare'),
        (TYPE_MEDICINE, 'Farmaco'),
        (TYPE_CLEANING, 'Pulizia'),
        (TYPE_BATHROOM, 'Bagno'),
        (TYPE_OTHER, 'Altro'),
    ]

    SOURCE_MANUAL = 'manual'
    SOURCE_OFF = 'open_food_facts'
    SOURCE_IMPORT = 'import'
    SOURCE_CHOICES = [
        (SOURCE_MANUAL, 'Manuale'),
        (SOURCE_OFF, 'Open Food Facts'),
        (SOURCE_IMPORT, 'Importazione'),
    ]

    NUTRISCORE_CHOICES = [
        ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'),
    ]

    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    barcode = models.CharField(max_length=30, unique=True, null=True, blank=True)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_FOOD)
    default_unit = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
    )
    default_store = models.ForeignKey(
        'stores.Store',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_products',
    )
    image_url = models.URLField(blank=True)
    nutriscore = models.CharField(
        max_length=1, choices=NUTRISCORE_CHOICES, null=True, blank=True
    )
    off_id = models.CharField(max_length=50, blank=True)  # ID su Open Food Facts
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_MANUAL)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products',
    )

    class Meta:
        verbose_name = 'prodotto'
        verbose_name_plural = 'prodotti'
        ordering = ('name',)

    def __str__(self):
        if self.brand:
            return f'{self.name} — {self.brand}'
        return self.name
