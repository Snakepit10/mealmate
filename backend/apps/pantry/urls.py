from django.urls import path

from .views import (
    PantryListView,
    PantryDetailView,
    PantryFinishView,
    PantryRestoreView,
    PantryExpiringView,
    PantryHistoryView,
)

urlpatterns = [
    path('pantry/', PantryListView.as_view(), name='pantry-list'),
    path('pantry/expiring/', PantryExpiringView.as_view(), name='pantry-expiring'),
    path('pantry/history/', PantryHistoryView.as_view(), name='pantry-history'),
    path('pantry/<uuid:pid>/', PantryDetailView.as_view(), name='pantry-detail'),
    path('pantry/<uuid:pid>/finish/', PantryFinishView.as_view(), name='pantry-finish'),
    path('pantry/<uuid:pid>/restore/', PantryRestoreView.as_view(), name='pantry-restore'),
]
