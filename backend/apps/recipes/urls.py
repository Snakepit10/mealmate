from django.urls import path

from .views import (
    RecipeListView,
    RecipeDetailView,
    RecipePublishView,
    RecipeUnpublishView,
    RecipeForkView,
    RecipeReportView,
    RecipeImportView,
    RecipeIngredientListView,
    RecipeIngredientDetailView,
    RecipeInstructionListView,
    RecipeInstructionDetailView,
    RecipeInstructionReorderView,
    RecipeRatingListView,
    RecipeRatingDetailView,
    RecipeCategoryListView,
    RecipeSuggestionView,
)

urlpatterns = [
    # List & create
    path('', RecipeListView.as_view(), name='recipe-list'),
    # Special actions (before <uuid:id>/ to avoid conflicts)
    path('import/', RecipeImportView.as_view(), name='recipe-import'),
    path('categories/', RecipeCategoryListView.as_view(), name='recipe-category-list'),
    path('suggestions/', RecipeSuggestionView.as_view(), name='recipe-suggestions'),
    # Detail
    path('<uuid:id>/', RecipeDetailView.as_view(), name='recipe-detail'),
    path('<uuid:id>/publish/', RecipePublishView.as_view(), name='recipe-publish'),
    path('<uuid:id>/unpublish/', RecipeUnpublishView.as_view(), name='recipe-unpublish'),
    path('<uuid:id>/fork/', RecipeForkView.as_view(), name='recipe-fork'),
    path('<uuid:id>/report/', RecipeReportView.as_view(), name='recipe-report'),
    # Ingredients
    path('<uuid:id>/ingredients/', RecipeIngredientListView.as_view(), name='recipe-ingredient-list'),
    path('<uuid:id>/ingredients/<uuid:iid>/', RecipeIngredientDetailView.as_view(), name='recipe-ingredient-detail'),
    # Instructions
    path('<uuid:id>/instructions/', RecipeInstructionListView.as_view(), name='recipe-instruction-list'),
    path('<uuid:id>/instructions/reorder/', RecipeInstructionReorderView.as_view(), name='recipe-instruction-reorder'),
    path('<uuid:id>/instructions/<uuid:sid>/', RecipeInstructionDetailView.as_view(), name='recipe-instruction-detail'),
    # Ratings
    path('<uuid:id>/ratings/', RecipeRatingListView.as_view(), name='recipe-rating-list'),
    path('<uuid:id>/ratings/<int:rid>/', RecipeRatingDetailView.as_view(), name='recipe-rating-detail'),
]
