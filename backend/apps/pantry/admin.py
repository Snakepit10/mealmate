from django.contrib import admin

from .models import PantryItem, PantryHistory


class PantryHistoryInline(admin.TabularInline):
    model = PantryHistory
    extra = 0
    readonly_fields = ('action', 'performed_by', 'timestamp')
    can_delete = False


@admin.register(PantryItem)
class PantryItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'family', 'status', 'expiry_date', 'updated_by', 'updated_at')
    list_filter = ('status', 'family')
    search_fields = ('product__name', 'family__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('product', 'updated_by')
    inlines = (PantryHistoryInline,)


@admin.register(PantryHistory)
class PantryHistoryAdmin(admin.ModelAdmin):
    list_display = ('pantry_item', 'action', 'performed_by', 'timestamp')
    list_filter = ('action',)
    readonly_fields = ('pantry_item', 'action', 'performed_by', 'timestamp')
