from django.urls import path, include

from .views import (
    FamilyCreateView,
    FamilyDetailView,
    FamilyMemberListView,
    FamilyMemberDetailView,
    InviteRegenerateView,
    JoinFamilyView,
    LeaveFamilyView,
    TransferAdminView,
)

urlpatterns = [
    path('', FamilyCreateView.as_view(), name='family-create'),
    path('join/', JoinFamilyView.as_view(), name='family-join'),
    path('<uuid:id>/', FamilyDetailView.as_view(), name='family-detail'),
    path('<uuid:id>/members/', FamilyMemberListView.as_view(), name='family-member-list'),
    path('<uuid:id>/members/<uuid:mid>/', FamilyMemberDetailView.as_view(), name='family-member-detail'),
    path('<uuid:id>/invite/', InviteRegenerateView.as_view(), name='family-invite'),
    path('<uuid:id>/leave/', LeaveFamilyView.as_view(), name='family-leave'),
    path('<uuid:id>/transfer-admin/', TransferAdminView.as_view(), name='family-transfer-admin'),
    # Stores nested sotto families
    path('<uuid:id>/', include('apps.stores.urls')),
    # Pantry nested sotto families (aggiunto al punto 7)
    path('<uuid:id>/', include('apps.pantry.urls')),
    # Shopping nested sotto families (aggiunto al punto 8)
    path('<uuid:id>/', include('apps.shopping.urls')),
    # Calendar nested sotto families (aggiunto al punto 10)
    path('<uuid:id>/', include('apps.calendar.urls')),
]
