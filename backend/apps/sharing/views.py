from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SharedResource
from .serializers import (
    SharedResourceSerializer,
    CreateSharedResourceSerializer,
    UpdateSharedResourceSerializer,
)


def _user_shares(user):
    """Tutte le condivisioni che riguardano l'utente (inviate + ricevute)."""
    family_ids = user.family_memberships.values_list('family_id', flat=True)
    return SharedResource.objects.filter(
        Q(shared_by=user)
        | Q(shared_with_user=user)
        | Q(shared_with_family_id__in=family_ids)
    ).select_related('shared_by', 'shared_with_user', 'shared_with_family')


def _get_as_recipient(share_id, user):
    """Recupera una condivisione di cui l'utente è destinatario."""
    family_ids = user.family_memberships.values_list('family_id', flat=True)
    try:
        share = SharedResource.objects.get(id=share_id)
    except SharedResource.DoesNotExist:
        return None, 'not_found'

    is_recipient = (
        share.shared_with_user == user
        or (share.shared_with_family_id and share.shared_with_family_id in list(family_ids))
    )
    if not is_recipient:
        return None, 'forbidden'
    return share, None


class ShareListView(APIView):
    """GET /shares/   POST /shares/"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        qs = _user_shares(request.user)
        status_filter = request.query_params.get('status')
        if status_filter in (SharedResource.STATUS_PENDING, SharedResource.STATUS_ACCEPTED, SharedResource.STATUS_REJECTED):
            qs = qs.filter(status=status_filter)
        direction = request.query_params.get('direction')
        if direction == 'sent':
            qs = qs.filter(shared_by=request.user)
        elif direction == 'received':
            family_ids = request.user.family_memberships.values_list('family_id', flat=True)
            qs = qs.filter(
                Q(shared_with_user=request.user) | Q(shared_with_family_id__in=family_ids)
            ).exclude(shared_by=request.user)
        return Response(SharedResourceSerializer(qs, many=True).data)

    def post(self, request):
        serializer = CreateSharedResourceSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        share = serializer.save(shared_by=request.user)
        return Response(SharedResourceSerializer(share).data, status=status.HTTP_201_CREATED)


class ShareDetailView(APIView):
    """GET/PATCH/DELETE /shares/{id}/"""
    permission_classes = (IsAuthenticated,)

    def _get_share(self, share_id, user):
        try:
            return _user_shares(user).get(id=share_id)
        except SharedResource.DoesNotExist:
            return None

    def get(self, request, id):
        share = self._get_share(id, request.user)
        if not share:
            return Response({'detail': 'Condivisione non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SharedResourceSerializer(share).data)

    def patch(self, request, id):
        share = self._get_share(id, request.user)
        if not share:
            return Response({'detail': 'Condivisione non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if share.shared_by != request.user:
            return Response(
                {'detail': 'Solo chi ha condiviso può modificare i permessi.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = UpdateSharedResourceSerializer(share, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SharedResourceSerializer(share).data)

    def delete(self, request, id):
        share = self._get_share(id, request.user)
        if not share:
            return Response({'detail': 'Condivisione non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if share.shared_by != request.user:
            return Response(
                {'detail': 'Solo chi ha condiviso può revocare la condivisione.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        share.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShareAcceptView(APIView):
    """POST /shares/{id}/accept/"""
    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        share, error = _get_as_recipient(id, request.user)
        if error == 'not_found':
            return Response({'detail': 'Condivisione non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if error == 'forbidden':
            return Response({'detail': 'Non sei il destinatario di questa condivisione.'}, status=status.HTTP_403_FORBIDDEN)
        if share.status != SharedResource.STATUS_PENDING:
            return Response(
                {'detail': f'La condivisione è già in stato "{share.status}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        share.status = SharedResource.STATUS_ACCEPTED
        share.save(update_fields=['status', 'updated_at'])
        return Response(SharedResourceSerializer(share).data)


class ShareRejectView(APIView):
    """POST /shares/{id}/reject/"""
    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        share, error = _get_as_recipient(id, request.user)
        if error == 'not_found':
            return Response({'detail': 'Condivisione non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if error == 'forbidden':
            return Response({'detail': 'Non sei il destinatario di questa condivisione.'}, status=status.HTTP_403_FORBIDDEN)
        if share.status != SharedResource.STATUS_PENDING:
            return Response(
                {'detail': f'La condivisione è già in stato "{share.status}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        share.status = SharedResource.STATUS_REJECTED
        share.save(update_fields=['status', 'updated_at'])
        return Response(SharedResourceSerializer(share).data)
