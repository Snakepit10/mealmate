from django.urls import path

from .views import ShareListView, ShareDetailView, ShareAcceptView, ShareRejectView

urlpatterns = [
    path('', ShareListView.as_view(), name='share-list'),
    path('<uuid:id>/', ShareDetailView.as_view(), name='share-detail'),
    path('<uuid:id>/accept/', ShareAcceptView.as_view(), name='share-accept'),
    path('<uuid:id>/reject/', ShareRejectView.as_view(), name='share-reject'),
]
