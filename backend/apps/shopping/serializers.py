from rest_framework import serializers

from .models import ShoppingItem, ShoppingHistory


class ShoppingItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_brand = serializers.CharField(source='product.brand', read_only=True)
    product_image = serializers.CharField(source='product.image_url', read_only=True)
    product_category = serializers.UUIDField(source='product.category_id', read_only=True)
    product_category_name = serializers.CharField(source='product.category.name', read_only=True)
    product_category_icon = serializers.CharField(source='product.category.icon', read_only=True)
    product_default_store = serializers.UUIDField(source='product.default_store_id', read_only=True)
    product_default_store_name = serializers.CharField(source='product.default_store.name', read_only=True)
    unit_abbr = serializers.CharField(source='unit.abbreviation', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    aisle_name = serializers.CharField(source='store_aisle.name', read_only=True)
    aisle_order = serializers.IntegerField(source='store_aisle.order', read_only=True)
    added_by_name = serializers.CharField(source='added_by.name', read_only=True)

    class Meta:
        model = ShoppingItem
        fields = (
            'id', 'product', 'product_name', 'product_brand', 'product_image',
            'product_category', 'product_category_name', 'product_category_icon',
            'product_default_store', 'product_default_store_name',
            'quantity', 'unit', 'unit_abbr',
            'store', 'store_name', 'store_aisle', 'aisle_name', 'aisle_order',
            'checked', 'unavailable',
            'added_by', 'added_by_name',
            'added_automatically', 'source_recipe', 'source_meal_date',
            'note', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'added_by', 'added_automatically',
            'source_recipe', 'source_meal_date',
            'checked', 'unavailable',
            'created_at', 'updated_at',
        )


class CreateShoppingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingItem
        fields = ('product', 'quantity', 'unit', 'store', 'store_aisle', 'note')

    def validate(self, attrs):
        family_id = self.context.get('family_id')
        product = attrs.get('product')
        if ShoppingItem.objects.filter(
            family_id=family_id,
            product=product,
            checked=False,
        ).exists():
            raise serializers.ValidationError(
                {'product': 'Prodotto già presente nella lista della spesa.'}
            )
        return attrs


class UpdateShoppingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingItem
        fields = ('quantity', 'unit', 'store', 'store_aisle', 'note')


class QuickAddSerializer(serializers.Serializer):
    """Aggiunta rapida: cerca o crea un prodotto per nome."""
    name = serializers.CharField(max_length=200)
    category = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.CharField(max_length=50, required=False, allow_null=True, allow_blank=True)
    unit = serializers.UUIDField(required=False, allow_null=True)
    store = serializers.UUIDField(required=False, allow_null=True)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)


class ShoppingHistorySerializer(serializers.ModelSerializer):
    completed_by_name = serializers.CharField(source='completed_by.name', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = ShoppingHistory
        fields = ('id', 'family', 'completed_at', 'completed_by', 'completed_by_name', 'items_count')
        read_only_fields = fields

    def get_items_count(self, obj):
        return len(obj.items) if obj.items else 0


class ShoppingHistoryDetailSerializer(serializers.ModelSerializer):
    completed_by_name = serializers.CharField(source='completed_by.name', read_only=True)

    class Meta:
        model = ShoppingHistory
        fields = ('id', 'family', 'completed_at', 'completed_by', 'completed_by_name', 'items')
        read_only_fields = fields
