from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsFamilyMember, IsFamilyAdmin

from .models import Family, FamilyMember
from .serializers import (
    FamilySerializer,
    CreateFamilySerializer,
    FamilyMemberSerializer,
    AddMemberSerializer,
    UpdateMemberSerializer,
    JoinFamilySerializer,
    TransferAdminSerializer,
)


class FamilyCreateView(APIView):
    """GET /families/ — lista famiglie dell'utente.
       POST /families/ — crea una nuova famiglia e aggiunge il creatore come admin."""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        families = Family.objects.filter(members__user=request.user)
        return Response(FamilySerializer(families, many=True).data)

    @transaction.atomic
    def post(self, request):
        serializer = CreateFamilySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        family = serializer.save(created_by=request.user)
        FamilyMember.objects.create(
            family=family,
            user=request.user,
            role=FamilyMember.ROLE_ADMIN,
            is_registered=True,
        )
        return Response(FamilySerializer(family).data, status=status.HTTP_201_CREATED)


class FamilyDetailView(APIView):
    """GET/PATCH/DELETE /families/{id}/"""

    def get_permissions(self):
        if self.request.method in ('PATCH', 'DELETE'):
            return [IsAuthenticated(), IsFamilyAdmin()]
        return [IsAuthenticated(), IsFamilyMember()]

    def _get_family(self, family_id):
        try:
            return Family.objects.get(id=family_id)
        except Family.DoesNotExist:
            return None

    def get(self, request, id):
        family = self._get_family(id)
        if not family:
            return Response({'detail': 'Famiglia non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(FamilySerializer(family).data)

    def patch(self, request, id):
        family = self._get_family(id)
        if not family:
            return Response({'detail': 'Famiglia non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CreateFamilySerializer(family, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(FamilySerializer(family).data)

    def delete(self, request, id):
        family = self._get_family(id)
        if not family:
            return Response({'detail': 'Famiglia non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        family.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FamilyMemberListView(APIView):
    """GET/POST /families/{id}/members/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def _get_family(self, family_id):
        try:
            return Family.objects.get(id=family_id)
        except Family.DoesNotExist:
            return None

    def get(self, request, id):
        family = self._get_family(id)
        if not family:
            return Response({'detail': 'Famiglia non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        members = family.members.select_related('user').all()
        return Response(FamilyMemberSerializer(members, many=True, context={'request': request}).data)

    def post(self, request, id):
        family = self._get_family(id)
        if not family:
            return Response({'detail': 'Famiglia non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AddMemberSerializer(
            data=request.data,
            context={'request': request, 'family_id': id},
        )
        serializer.is_valid(raise_exception=True)
        member = serializer.save(family=family, is_registered=False)
        return Response(
            FamilyMemberSerializer(member, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class FamilyMemberDetailView(APIView):
    """PATCH/DELETE /families/{id}/members/{mid}/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyAdmin()]

    def _get_member(self, family_id, mid):
        try:
            return FamilyMember.objects.select_related('user').get(id=mid, family_id=family_id)
        except FamilyMember.DoesNotExist:
            return None

    def patch(self, request, id, mid):
        member = self._get_member(id, mid)
        if not member:
            return Response({'detail': 'Membro non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        # Non permettere la modifica del proprio ruolo tramite questo endpoint
        if member.user == request.user:
            return Response(
                {'detail': 'Non puoi modificare il tuo stesso membro tramite questo endpoint.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = UpdateMemberSerializer(member, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(FamilyMemberSerializer(member, context={'request': request}).data)

    def delete(self, request, id, mid):
        member = self._get_member(id, mid)
        if not member:
            return Response({'detail': 'Membro non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        if member.user == request.user:
            return Response(
                {'detail': 'Usa /leave/ per abbandonare la famiglia.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Non rimuovere l'unico admin
        if member.role == FamilyMember.ROLE_ADMIN:
            admins_count = FamilyMember.objects.filter(family_id=id, role=FamilyMember.ROLE_ADMIN).count()
            if admins_count <= 1:
                return Response(
                    {'detail': 'Non puoi rimuovere l\'unico admin. Trasferisci prima il ruolo.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InviteRegenerateView(APIView):
    """POST /families/{id}/invite/ — rigenera il codice invito."""
    permission_classes = (IsAuthenticated(), IsFamilyAdmin())

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyAdmin()]

    def post(self, request, id):
        try:
            family = Family.objects.get(id=id)
        except Family.DoesNotExist:
            return Response({'detail': 'Famiglia non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        from core.utils import generate_invite_code
        code = generate_invite_code()
        while Family.objects.filter(invite_code=code).exists():
            code = generate_invite_code()
        family.invite_code = code
        family.save(update_fields=['invite_code'])
        return Response({'invite_code': family.invite_code})


class JoinFamilyView(APIView):
    """POST /families/join/ — entra in una famiglia con codice invito."""
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    def post(self, request):
        serializer = JoinFamilySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        family = serializer.context['family']

        # Verifica che non sia già membro
        if FamilyMember.objects.filter(family=family, user=request.user).exists():
            return Response(
                {'detail': 'Sei già membro di questa famiglia.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member = FamilyMember.objects.create(
            family=family,
            user=request.user,
            role=FamilyMember.ROLE_MEMBER,
            is_registered=True,
        )
        return Response(
            FamilyMemberSerializer(member, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class LeaveFamilyView(APIView):
    """POST /families/{id}/leave/"""
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    def post(self, request, id):
        try:
            member = FamilyMember.objects.get(family_id=id, user=request.user)
        except FamilyMember.DoesNotExist:
            return Response({'detail': 'Non sei membro di questa famiglia.'}, status=status.HTTP_404_NOT_FOUND)

        if member.role == FamilyMember.ROLE_ADMIN:
            admins_count = FamilyMember.objects.filter(family_id=id, role=FamilyMember.ROLE_ADMIN).count()
            if admins_count <= 1:
                return Response(
                    {'detail': 'Sei l\'unico admin. Trasferisci il ruolo prima di uscire.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TransferAdminView(APIView):
    """POST /families/{id}/transfer-admin/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyAdmin()]

    @transaction.atomic
    def post(self, request, id):
        serializer = TransferAdminSerializer(
            data=request.data,
            context={'request': request, 'family_id': id},
        )
        serializer.is_valid(raise_exception=True)

        target_member = serializer.context['target_member']

        # Declassa il richiedente a membro
        FamilyMember.objects.filter(family_id=id, user=request.user).update(role=FamilyMember.ROLE_MEMBER)
        # Promuove il target ad admin
        target_member.role = FamilyMember.ROLE_ADMIN
        target_member.save(update_fields=['role'])

        return Response({'detail': f'Ruolo admin trasferito a {target_member.get_display_name()}.'})
