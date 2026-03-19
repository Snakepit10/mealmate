from django.urls import path

from .views import (
    ProductListView,
    ProductDetailView,
    ProductByBarcodeView,
    ProductScanView,
    ProductCategoryListView,
    UnitOfMeasureListView,
)

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('scan/', ProductScanView.as_view(), name='product-scan'),
    path('barcode/<str:code>/', ProductByBarcodeView.as_view(), name='product-by-barcode'),
    path('categories/', ProductCategoryListView.as_view(), name='product-category-list'),
    path('units/', UnitOfMeasureListView.as_view(), name='unit-list'),
    path('<uuid:id>/', ProductDetailView.as_view(), name='product-detail'),
]
