from django.urls import path

from .views import (
    StoreListView,
    StoreDetailView,
    StoreDuplicateView,
    AisleListView,
    AisleDetailView,
    AisleReorderView,
)

# Montato su /families/{id}/stores/ tramite api_urls.py
# ma poiché le URL stores sono nested sotto families,
# queste vengono incluse direttamente in families/urls.py
urlpatterns = [
    path('stores/', StoreListView.as_view(), name='store-list'),
    path('stores/<uuid:sid>/', StoreDetailView.as_view(), name='store-detail'),
    path('stores/<uuid:sid>/duplicate/', StoreDuplicateView.as_view(), name='store-duplicate'),
    path('stores/<uuid:sid>/aisles/', AisleListView.as_view(), name='aisle-list'),
    path('stores/<uuid:sid>/aisles/reorder/', AisleReorderView.as_view(), name='aisle-reorder'),
    path('stores/<uuid:sid>/aisles/<uuid:aid>/', AisleDetailView.as_view(), name='aisle-detail'),
]
