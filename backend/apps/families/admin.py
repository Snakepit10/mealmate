from django.contrib import admin

from .models import Family, FamilyMember


class FamilyMemberInline(admin.TabularInline):
    model = FamilyMember
    extra = 0
    readonly_fields = ('id', 'joined_at')
    fields = ('user', 'name', 'role', 'is_registered', 'birth_date', 'joined_at')


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'invite_code', 'created_by', 'created_at')
    search_fields = ('name', 'invite_code')
    readonly_fields = ('id', 'invite_code', 'created_at', 'updated_at')
    inlines = (FamilyMemberInline,)


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('get_display_name', 'family', 'role', 'is_registered', 'joined_at')
    list_filter = ('role', 'is_registered', 'family')
    search_fields = ('user__email', 'user__name', 'name')
    readonly_fields = ('id', 'joined_at')
