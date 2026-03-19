from django.contrib import admin

from .models import Recipe, RecipeCategory, RecipeIngredient, RecipeInstruction, RecipeRating, RecipeReport


@admin.register(RecipeCategory)
class RecipeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'parent', 'order')
    list_filter = ('level',)
    ordering = ('order', 'name')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    fields = ('product', 'quantity', 'unit', 'is_optional', 'note', 'order')
    ordering = ('order',)


class RecipeInstructionInline(admin.TabularInline):
    model = RecipeInstruction
    extra = 0
    fields = ('step_number', 'text')
    ordering = ('step_number',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'family', 'created_by', 'is_public', 'is_draft', 'average_rating', 'ratings_count')
    list_filter = ('is_public', 'is_draft', 'difficulty', 'category')
    search_fields = ('title', 'description', 'created_by__email')
    readonly_fields = ('id', 'average_rating', 'ratings_count', 'created_at', 'updated_at')
    raw_id_fields = ('created_by', 'family', 'forked_from')
    inlines = (RecipeIngredientInline, RecipeInstructionInline)


@admin.register(RecipeRating)
class RecipeRatingAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user', 'score', 'created_at')
    list_filter = ('score',)
    raw_id_fields = ('recipe', 'user')


@admin.register(RecipeReport)
class RecipeReportAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'reported_by', 'reason', 'status', 'created_at')
    list_filter = ('status', 'reason')
    raw_id_fields = ('recipe', 'reported_by')
