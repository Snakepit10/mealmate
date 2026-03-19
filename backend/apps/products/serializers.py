from rest_framework import serializers

from .models import Product, ProductCategory, UnitOfMeasure


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ('id', 'name', 'icon', 'order', 'is_food')
        read_only_fields = ('id',)


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = ('id', 'name', 'abbreviation', 'is_custom')
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    default_unit_abbr = serializers.CharField(source='default_unit.abbreviation', read_only=True)
    default_store_name = serializers.CharField(source='default_store.name', read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'brand', 'barcode',
            'category', 'category_name',
            'type', 'default_unit', 'default_unit_abbr',
            'default_store', 'default_store_name',
            'image_url', 'nutriscore', 'off_id', 'source',
            'created_by', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'off_id', 'source', 'created_by', 'created_at', 'updated_at')


class CreateProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'name', 'brand', 'barcode',
            'category', 'type', 'default_unit',
            'default_store', 'image_url', 'nutriscore',
        )
        extra_kwargs = {
            # Obbligatoria alla creazione; ignorata su PATCH (partial=True)
            'category': {'required': True, 'allow_null': False},
        }

    def validate_barcode(self, value):
        if value:
            from core.utils import normalize_barcode
            value = normalize_barcode(value)
            if Product.objects.filter(barcode=value).exclude(
                pk=self.instance.pk if self.instance else None
            ).exists():
                raise serializers.ValidationError('Prodotto con questo barcode già esistente.')
        return value or None


class BarcodeScannedProductSerializer(serializers.ModelSerializer):
    """Serializer per la risposta di /scan/ con info extra dalla fonte."""
    source = serializers.CharField(read_only=True)
    needs_confirmation = serializers.BooleanField(read_only=True, default=False)
    category_name = serializers.CharField(source='category.name', read_only=True)
    default_unit_abbr = serializers.CharField(source='default_unit.abbreviation', read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'brand', 'barcode',
            'category', 'category_name',
            'type', 'default_unit', 'default_unit_abbr',
            'image_url', 'nutriscore', 'off_id', 'source',
            'needs_confirmation',
        )
