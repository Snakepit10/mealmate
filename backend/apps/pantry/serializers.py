from rest_framework import serializers

from .models import PantryItem, PantryHistory


class PantryItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_brand = serializers.CharField(source='product.brand', read_only=True)
    product_image = serializers.CharField(source='product.image_url', read_only=True)
    product_category = serializers.UUIDField(source='product.category_id', read_only=True)
    product_category_name = serializers.CharField(source='product.category.name', read_only=True)
    product_category_icon = serializers.CharField(source='product.category.icon', read_only=True)
    product_default_store = serializers.UUIDField(source='product.default_store_id', read_only=True)
    product_default_store_name = serializers.CharField(source='product.default_store.name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.name', read_only=True)

    class Meta:
        model = PantryItem
        fields = (
            'id', 'product', 'product_name', 'product_brand', 'product_image',
            'product_category', 'product_category_name', 'product_category_icon',
            'product_default_store', 'product_default_store_name',
            'status', 'expiry_date', 'note',
            'updated_by', 'updated_by_name',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'updated_by', 'created_at', 'updated_at')


class CreatePantryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PantryItem
        fields = ('product', 'expiry_date', 'note')

    def validate_product(self, value):
        family_id = self.context.get('family_id')
        if PantryItem.objects.filter(family_id=family_id, product=value).exists():
            raise serializers.ValidationError('Prodotto già presente in dispensa.')
        return value


class UpdatePantryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PantryItem
        fields = ('expiry_date', 'note', 'status')


class PantryHistorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='pantry_item.product.name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.name', read_only=True)

    class Meta:
        model = PantryHistory
        fields = ('id', 'pantry_item', 'product_name', 'action', 'performed_by', 'performed_by_name', 'timestamp')
        read_only_fields = fields
