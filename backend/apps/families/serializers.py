from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Family, FamilyMember

User = get_user_model()


class FamilyMemberSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = FamilyMember
        fields = (
            'id', 'user', 'display_name', 'user_email', 'user_avatar',
            'name', 'avatar', 'birth_date', 'role', 'is_registered', 'joined_at',
        )
        read_only_fields = ('id', 'joined_at', 'is_registered')

    def get_display_name(self, obj):
        return obj.get_display_name()

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    def get_user_avatar(self, obj):
        request = self.context.get('request')
        if obj.user and obj.user.avatar:
            return request.build_absolute_uri(obj.user.avatar.url) if request else obj.user.avatar.url
        return None


class AddMemberSerializer(serializers.ModelSerializer):
    """Aggiunge un membro senza account (es. figlio)."""

    class Meta:
        model = FamilyMember
        fields = ('name', 'avatar', 'birth_date', 'role')

    def validate_role(self, value):
        request = self.context.get('request')
        family_id = self.context.get('family_id')
        # Solo un admin può aggiungere altri admin
        if value == FamilyMember.ROLE_ADMIN:
            is_admin = FamilyMember.objects.filter(
                family_id=family_id,
                user=request.user,
                role=FamilyMember.ROLE_ADMIN,
            ).exists()
            if not is_admin:
                raise serializers.ValidationError('Solo un admin può assegnare il ruolo admin.')
        return value


class UpdateMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMember
        fields = ('name', 'avatar', 'birth_date', 'role')


class FamilySerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Family
        fields = (
            'id', 'name', 'invite_code', 'created_by', 'created_by_name',
            'members_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'invite_code', 'created_by', 'created_at', 'updated_at')

    def get_members_count(self, obj):
        return obj.members.count()

    def get_created_by_name(self, obj):
        return obj.created_by.name if obj.created_by else None


class CreateFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ('name',)


class JoinFamilySerializer(serializers.Serializer):
    invite_code = serializers.CharField(max_length=8)

    def validate_invite_code(self, value):
        try:
            family = Family.objects.get(invite_code=value.upper())
        except Family.DoesNotExist:
            raise serializers.ValidationError('Codice invito non valido.')
        self.context['family'] = family
        return value.upper()


class TransferAdminSerializer(serializers.Serializer):
    member_id = serializers.UUIDField()

    def validate_member_id(self, value):
        family_id = self.context.get('family_id')
        try:
            member = FamilyMember.objects.get(id=value, family_id=family_id)
        except FamilyMember.DoesNotExist:
            raise serializers.ValidationError('Membro non trovato in questa famiglia.')
        if not member.user:
            raise serializers.ValidationError('Non puoi rendere admin un membro senza account.')
        self.context['target_member'] = member
        return value
