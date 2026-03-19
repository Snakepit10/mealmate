from django.urls import path

from .views import StoreCategoryListView

urlpatterns = [
    path('', StoreCategoryListView.as_view(), name='store-category-list'),
]
