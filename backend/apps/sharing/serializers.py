from rest_framework import serializers

from .models import SharedResource


class SharedResourceSerializer(serializers.ModelSerializer):
    shared_by_name = serializers.CharField(source='shared_by.name', read_only=True)
    shared_with_user_name = serializers.CharField(source='shared_with_user.name', read_only=True)
    shared_with_family_name = serializers.CharField(source='shared_with_family.name', read_only=True)
    resource_type_display = serializers.CharField(source='get_resource_type_display', read_only=True)

    class Meta:
        model = SharedResource
        fields = (
            'id', 'resource_type', 'resource_type_display', 'resource_id',
            'shared_by', 'shared_by_name',
            'shared_with_user', 'shared_with_user_name',
            'shared_with_family', 'shared_with_family_name',
            'permission', 'status',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'shared_by', 'status', 'created_at', 'updated_at')


class CreateSharedResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedResource
        fields = (
            'resource_type', 'resource_id',
            'shared_with_user', 'shared_with_family',
            'permission',
        )

    def validate(self, attrs):
        user = self.context['request'].user
        has_user = bool(attrs.get('shared_with_user'))
        has_family = bool(attrs.get('shared_with_family'))

        if not has_user and not has_family:
            raise serializers.ValidationError(
                'Specifica shared_with_user oppure shared_with_family.'
            )
        if has_user and has_family:
            raise serializers.ValidationError(
                'Specifica solo shared_with_user o shared_with_family, non entrambi.'
            )
        # Non condividere con se stesso
        if has_user and attrs['shared_with_user'] == user:
            raise serializers.ValidationError('Non puoi condividere con te stesso.')

        # Verifica duplicato pending
        qs = SharedResource.objects.filter(
            resource_type=attrs['resource_type'],
            resource_id=attrs['resource_id'],
            shared_by=user,
            status=SharedResource.STATUS_PENDING,
        )
        if has_user:
            qs = qs.filter(shared_with_user=attrs['shared_with_user'])
        else:
            qs = qs.filter(shared_with_family=attrs['shared_with_family'])
        if qs.exists():
            raise serializers.ValidationError('Esiste già una condivisione in attesa per questa risorsa.')

        return attrs


class UpdateSharedResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedResource
        fields = ('permission',)
