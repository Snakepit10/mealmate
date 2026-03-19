from django.contrib import admin

from .models import Product, ProductCategory, UnitOfMeasure


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'order')
    ordering = ('order', 'name')


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'is_custom')
    list_filter = ('is_custom',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'barcode', 'category', 'type', 'source', 'nutriscore')
    list_filter = ('type', 'source', 'category', 'nutriscore')
    search_fields = ('name', 'brand', 'barcode', 'off_id')
    readonly_fields = ('id', 'off_id', 'created_at', 'updated_at')
    raw_id_fields = ('created_by',)
