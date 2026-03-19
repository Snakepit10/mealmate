from rest_framework import serializers

from .models import Store, StoreAisle, StoreCategory, ProductStore


class StoreCategorySerializer(serializers.ModelSerializer):
    name_display = serializers.CharField(source='get_name_display', read_only=True)

    class Meta:
        model = StoreCategory
        fields = ('id', 'name', 'name_display', 'icon')
        read_only_fields = ('id',)


class StoreAisleSerializer(serializers.ModelSerializer):
    product_category_name = serializers.CharField(source='product_category.name', read_only=True)
    product_category_icon = serializers.CharField(source='product_category.icon', read_only=True)

    class Meta:
        model = StoreAisle
        fields = ('id', 'name', 'order', 'product_category', 'product_category_name', 'product_category_icon')
        read_only_fields = ('id',)


class StoreSerializer(serializers.ModelSerializer):
    store_category_name = serializers.CharField(source='store_category.get_name_display', read_only=True)
    aisles_count = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = (
            'id', 'name', 'store_category', 'store_category_name',
            'is_default', 'aisles_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_aisles_count(self, obj):
        return obj.aisles.count()


class CreateStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('name', 'store_category', 'is_default')


class AisleReorderSerializer(serializers.Serializer):
    """Riceve una lista ordinata di ID corsia per il drag & drop."""
    order = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
    )


class ProductStoreSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    aisle_name = serializers.CharField(source='store_aisle.name', read_only=True)

    class Meta:
        model = ProductStore
        fields = (
            'id', 'product', 'product_name',
            'store', 'store_name',
            'store_aisle', 'aisle_name',
            'preferred',
        )
        read_only_fields = ('id',)
