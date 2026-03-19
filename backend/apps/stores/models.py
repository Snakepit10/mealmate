from django.db import models

from core.models import TimeStampedModel


class StoreCategory(TimeStampedModel):
    SUPERMARKET = 'supermarket'
    PHARMACY = 'pharmacy'
    POULTRY = 'poultry'
    FISHMONGER = 'fishmonger'
    BAKERY = 'bakery'
    BUTCHER = 'butcher'
    MARKET = 'market'
    OTHER = 'other'

    TYPE_CHOICES = [
        (SUPERMARKET, 'Supermercato'),
        (PHARMACY, 'Farmacia'),
        (POULTRY, 'Polleria'),
        (FISHMONGER, 'Pescheria'),
        (BAKERY, 'Panetteria'),
        (BUTCHER, 'Macelleria'),
        (MARKET, 'Mercato'),
        (OTHER, 'Altro'),
    ]

    name = models.CharField(max_length=20, choices=TYPE_CHOICES, unique=True)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'categoria negozio'
        verbose_name_plural = 'categorie negozio'
        ordering = ('name',)

    def __str__(self):
        return self.get_name_display()


class Store(TimeStampedModel):
    family = models.ForeignKey(
        'families.Family',
        on_delete=models.CASCADE,
        related_name='stores',
    )
    name = models.CharField(max_length=150)
    store_category = models.ForeignKey(
        StoreCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stores',
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'negozio'
        verbose_name_plural = 'negozi'
        ordering = ('-is_default', 'name')

    def save(self, *args, **kwargs):
        # Garantisce un solo negozio default per categoria per famiglia
        if self.is_default and self.store_category:
            Store.objects.filter(
                family=self.family,
                store_category=self.store_category,
                is_default=True,
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} ({self.family.name})'


class StoreAisle(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='aisles')
    name = models.CharField(max_length=100)
    order = models.PositiveSmallIntegerField(default=0)
    product_category = models.ForeignKey(
        'products.ProductCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='store_aisles',
    )

    class Meta:
        verbose_name = 'corsia'
        verbose_name_plural = 'corsie'
        ordering = ('order', 'name')
        # Una sola corsia per categoria per negozio
        constraints = [
            models.UniqueConstraint(
                fields=['store', 'product_category'],
                condition=models.Q(product_category__isnull=False),
                name='unique_store_product_category',
            )
        ]

    def __str__(self):
        return f'{self.name} — {self.store.name}'


class ProductStore(TimeStampedModel):
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='store_links',
    )
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='product_links')
    store_aisle = models.ForeignKey(
        StoreAisle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_links',
    )
    preferred = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'prodotto-negozio'
        verbose_name_plural = 'prodotti-negozio'
        unique_together = [('product', 'store')]

    def save(self, *args, **kwargs):
        # Un solo negozio preferito per prodotto
        if self.preferred:
            ProductStore.objects.filter(
                product=self.product,
                preferred=True,
            ).exclude(pk=self.pk).update(preferred=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product.name} @ {self.store.name}'
