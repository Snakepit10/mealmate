from django.contrib import admin

from .models import SharedResource


@admin.register(SharedResource)
class SharedResourceAdmin(admin.ModelAdmin):
    list_display = (
        'resource_type', 'resource_id', 'shared_by',
        'shared_with_user', 'shared_with_family',
        'permission', 'status', 'created_at',
    )
    list_filter = ('resource_type', 'permission', 'status')
    search_fields = ('shared_by__email', 'shared_with_user__email', 'shared_with_family__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('shared_by', 'shared_with_user', 'shared_with_family')
