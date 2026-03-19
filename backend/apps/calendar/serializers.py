from rest_framework import serializers

from .models import MealCalendar, MealSlot, MealEntry


class MealCalendarSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)

    class Meta:
        model = MealCalendar
        fields = ('id', 'name', 'color', 'created_by', 'created_by_name', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')


class CreateMealCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealCalendar
        fields = ('name', 'color')


class MealEntrySerializer(serializers.ModelSerializer):
    recipe_title = serializers.CharField(source='recipe.title', read_only=True)
    recipe_cover = serializers.ImageField(source='recipe.cover_image', read_only=True)
    added_by_name = serializers.CharField(source='added_by.name', read_only=True)
    assigned_member_ids = serializers.PrimaryKeyRelatedField(
        source='assigned_members',
        many=True,
        read_only=True,
    )

    class Meta:
        model = MealEntry
        fields = (
            'id', 'slot', 'recipe', 'recipe_title', 'recipe_cover',
            'note', 'assigned_member_ids', 'added_by', 'added_by_name',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'slot', 'added_by', 'created_at', 'updated_at')


class CreateMealEntrySerializer(serializers.ModelSerializer):
    assigned_members = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )

    class Meta:
        model = MealEntry
        fields = ('recipe', 'note', 'assigned_members')

    def validate(self, attrs):
        if not attrs.get('recipe') and not attrs.get('note', '').strip():
            raise serializers.ValidationError('Specifica una ricetta oppure una nota.')
        return attrs


class UpdateMealEntrySerializer(serializers.ModelSerializer):
    assigned_members = serializers.ListField(
        child=serializers.UUIDField(), required=False
    )

    class Meta:
        model = MealEntry
        fields = ('recipe', 'note', 'assigned_members')


class MealSlotSerializer(serializers.ModelSerializer):
    entries = MealEntrySerializer(many=True, read_only=True)

    class Meta:
        model = MealSlot
        fields = ('id', 'date', 'meal_type', 'entries')
        read_only_fields = ('id',)


class CreateMealSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealSlot
        fields = ('date', 'meal_type')


class PlanWeekSerializer(serializers.Serializer):
    """Pianifica una settimana: lista di {date, meal_type, recipe_id?, note?}"""
    entries = serializers.ListField(
        child=serializers.DictField(), min_length=1
    )


class MissingIngredientSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=8, decimal_places=2, allow_null=True)
    unit = serializers.CharField(allow_null=True)
    shopping_item_created = serializers.BooleanField()
