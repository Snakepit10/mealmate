from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationSettings, PushSubscription
from .serializers import (
    NotificationSerializer,
    NotificationSettingsSerializer,
    PushSubscriptionSerializer,
)


class NotificationListView(APIView):
    """GET /notifications/"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        qs = Notification.objects.filter(user=request.user)
        unread_only = request.query_params.get('unread') == 'true'
        if unread_only:
            qs = qs.filter(read=False)
        notif_type = request.query_params.get('type')
        if notif_type:
            qs = qs.filter(type=notif_type)
        return Response(NotificationSerializer(qs[:50], many=True).data)


class NotificationReadView(APIView):
    """PATCH /notifications/{id}/read/"""
    permission_classes = (IsAuthenticated,)

    def patch(self, request, id):
        try:
            notif = Notification.objects.get(id=id, user=request.user)
        except Notification.DoesNotExist:
            return Response({'detail': 'Notifica non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        notif.read = True
        notif.save(update_fields=['read'])
        return Response(NotificationSerializer(notif).data)


class NotificationReadAllView(APIView):
    """POST /notifications/read-all/"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        count = Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({'marked_read': count})


class NotificationDeleteView(APIView):
    """DELETE /notifications/{id}/"""
    permission_classes = (IsAuthenticated,)

    def delete(self, request, id):
        try:
            notif = Notification.objects.get(id=id, user=request.user)
        except Notification.DoesNotExist:
            return Response({'detail': 'Notifica non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        notif.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationSettingsView(APIView):
    """GET/PATCH /notifications/settings/"""
    permission_classes = (IsAuthenticated,)

    def _get_or_create_settings(self, user):
        settings_obj, _ = NotificationSettings.objects.get_or_create(user=user)
        return settings_obj

    def get(self, request):
        settings_obj = self._get_or_create_settings(request.user)
        return Response(NotificationSettingsSerializer(settings_obj).data)

    def patch(self, request):
        settings_obj = self._get_or_create_settings(request.user)
        serializer = NotificationSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(NotificationSettingsSerializer(settings_obj).data)


class PushRegisterView(APIView):
    """POST /notifications/push/register/"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = PushSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sub, created = PushSubscription.objects.update_or_create(
            endpoint=serializer.validated_data['endpoint'],
            defaults={
                'user': request.user,
                'p256dh': serializer.validated_data['p256dh'],
                'auth': serializer.validated_data['auth'],
                'user_agent': serializer.validated_data.get('user_agent', ''),
            },
        )
        st = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({'registered': True}, status=st)


class PushUnregisterView(APIView):
    """DELETE /notifications/push/unregister/  Body: { "endpoint": "..." }"""
    permission_classes = (IsAuthenticated,)

    def delete(self, request):
        endpoint = request.data.get('endpoint', '').strip()
        if not endpoint:
            return Response({'detail': 'endpoint obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)
        deleted, _ = PushSubscription.objects.filter(
            user=request.user, endpoint=endpoint
        ).delete()
        if not deleted:
            return Response({'detail': 'Sottoscrizione non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
