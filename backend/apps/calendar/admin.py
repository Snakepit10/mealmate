from django.contrib import admin

from .models import MealCalendar, MealSlot, MealEntry, MealCalendarShare


class MealEntryInline(admin.TabularInline):
    model = MealEntry
    extra = 0
    fields = ('recipe', 'note', 'added_by')
    raw_id_fields = ('recipe', 'added_by')


class MealSlotInline(admin.TabularInline):
    model = MealSlot
    extra = 0
    fields = ('date', 'meal_type')
    show_change_link = True


@admin.register(MealCalendar)
class MealCalendarAdmin(admin.ModelAdmin):
    list_display = ('name', 'family', 'color', 'created_by')
    list_filter = ('family',)
    search_fields = ('name', 'family__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (MealSlotInline,)


@admin.register(MealSlot)
class MealSlotAdmin(admin.ModelAdmin):
    list_display = ('calendar', 'date', 'meal_type')
    list_filter = ('meal_type', 'calendar__family')
    inlines = (MealEntryInline,)


@admin.register(MealEntry)
class MealEntryAdmin(admin.ModelAdmin):
    list_display = ('slot', 'recipe', 'note', 'added_by')
    raw_id_fields = ('recipe', 'added_by')
    filter_horizontal = ('assigned_members',)
