from django.urls import path

from .views import (
    ShoppingListView,
    ShoppingItemDetailView,
    ShoppingCheckView,
    ShoppingUncheckView,
    ShoppingUnavailableView,
    ShoppingQuickAddView,
    ShoppingCompleteView,
    ShoppingHistoryListView,
    ShoppingHistoryDetailView,
    ShoppingHistoryReuseView,
)

urlpatterns = [
    path('shopping/', ShoppingListView.as_view(), name='shopping-list'),
    path('shopping/quick-add/', ShoppingQuickAddView.as_view(), name='shopping-quick-add'),
    path('shopping/complete/', ShoppingCompleteView.as_view(), name='shopping-complete'),
    path('shopping/history/', ShoppingHistoryListView.as_view(), name='shopping-history-list'),
    path('shopping/history/<int:hid>/', ShoppingHistoryDetailView.as_view(), name='shopping-history-detail'),
    path('shopping/history/<int:hid>/reuse/', ShoppingHistoryReuseView.as_view(), name='shopping-history-reuse'),
    path('shopping/<uuid:iid>/', ShoppingItemDetailView.as_view(), name='shopping-item-detail'),
    path('shopping/<uuid:iid>/check/', ShoppingCheckView.as_view(), name='shopping-check'),
    path('shopping/<uuid:iid>/uncheck/', ShoppingUncheckView.as_view(), name='shopping-uncheck'),
    path('shopping/<uuid:iid>/unavailable/', ShoppingUnavailableView.as_view(), name='shopping-unavailable'),
]
