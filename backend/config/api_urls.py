from django.urls import path, include

urlpatterns = [
    # Auth
    path('auth/', include('apps.accounts.urls')),
    # Families
    path('families/', include('apps.families.urls')),
    # Products
    path('products/', include('apps.products.urls')),
    # Stores
    path('store-categories/', include('apps.stores.urls_categories')),
    # Recipes
    path('recipes/', include('apps.recipes.urls')),
    # Sharing
    path('shares/', include('apps.sharing.urls')),
    # Notifications
    path('notifications/', include('apps.notifications.urls')),
]
