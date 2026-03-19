from django.contrib import admin

from .models import Store, StoreAisle, StoreCategory, ProductStore


@admin.register(StoreCategory)
class StoreCategoryAdmin(admin.ModelAdmin):
    list_display = ('get_name_display', 'icon')


class StoreAisleInline(admin.TabularInline):
    model = StoreAisle
    extra = 0
    fields = ('name', 'order')
    ordering = ('order',)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'family', 'store_category', 'is_default')
    list_filter = ('store_category', 'is_default')
    search_fields = ('name', 'family__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (StoreAisleInline,)


@admin.register(StoreAisle)
class StoreAisleAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'order')
    list_filter = ('store__family',)
    ordering = ('store', 'order')


@admin.register(ProductStore)
class ProductStoreAdmin(admin.ModelAdmin):
    list_display = ('product', 'store', 'store_aisle', 'preferred')
    list_filter = ('preferred', 'store__family')
    search_fields = ('product__name', 'store__name')
