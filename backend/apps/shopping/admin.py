from django.contrib import admin

from .models import ShoppingItem, ShoppingHistory


@admin.register(ShoppingItem)
class ShoppingItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'family', 'quantity', 'unit', 'store', 'checked', 'unavailable', 'added_automatically')
    list_filter = ('checked', 'unavailable', 'added_automatically', 'family')
    search_fields = ('product__name', 'family__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('product', 'added_by', 'source_recipe')


@admin.register(ShoppingHistory)
class ShoppingHistoryAdmin(admin.ModelAdmin):
    list_display = ('family', 'completed_at', 'completed_by')
    list_filter = ('family',)
    readonly_fields = ('family', 'completed_at', 'completed_by', 'items')
