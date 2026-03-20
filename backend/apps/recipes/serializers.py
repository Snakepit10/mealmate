from rest_framework import serializers

from .models import Recipe, RecipeCategory, RecipeIngredient, RecipeInstruction, RecipeRating, RecipeReport


class RecipeCategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = RecipeCategory
        fields = ('id', 'name', 'level', 'parent', 'order', 'children')
        read_only_fields = ('id',)

    def get_children(self, obj):
        if obj.level == 1:
            return RecipeCategorySerializer(obj.children.all(), many=True).data
        return []


class RecipeIngredientSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    unit_abbr = serializers.CharField(source='unit.abbreviation', read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'product', 'product_name', 'quantity', 'unit', 'unit_abbr', 'is_optional', 'note', 'order')
        read_only_fields = ('id',)


class RecipeInstructionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeInstruction
        fields = ('id', 'step_number', 'text', 'image')
        read_only_fields = ('id',)


class RecipeRatingSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = RecipeRating
        fields = ('id', 'user', 'user_name', 'score', 'comment', 'image', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def validate_score(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Il voto deve essere tra 1 e 5.')
        return value


class RecipeListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    ingredients_count = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'cover_image', 'cover_image_url', 'difficulty', 'servings',
            'prep_time', 'cook_time', 'category', 'category_name',
            'is_public', 'is_draft', 'average_rating', 'ratings_count',
            'created_by', 'created_by_name', 'ingredients_count',
            'created_at',
        )
        read_only_fields = ('id', 'average_rating', 'ratings_count', 'created_by', 'created_at')

    def get_ingredients_count(self, obj):
        return obj.ingredients.count()


class RecipeDetailSerializer(RecipeListSerializer):
    ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    instructions = RecipeInstructionSerializer(many=True, read_only=True)
    forked_from_title = serializers.CharField(source='forked_from.title', read_only=True)

    class Meta(RecipeListSerializer.Meta):
        fields = RecipeListSerializer.Meta.fields + (
            'description', 'external_link', 'family',
            'forked_from', 'forked_from_title',
            'ingredients', 'instructions', 'updated_at',
        )


class CreateRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'title', 'description', 'cover_image', 'cover_image_url', 'external_link',
            'servings', 'prep_time', 'cook_time', 'difficulty',
            'category', 'is_public', 'is_draft',
        )


class RecipeReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeReport
        fields = ('id', 'reason', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate(self, attrs):
        request = self.context.get('request')
        recipe = self.context.get('recipe')
        if RecipeReport.objects.filter(recipe=recipe, reported_by=request.user).exists():
            raise serializers.ValidationError('Hai già segnalato questa ricetta.')
        return attrs


class InstructionReorderSerializer(serializers.Serializer):
    order = serializers.ListField(child=serializers.UUIDField(), min_length=1)


class RecipeSuggestionSerializer(serializers.ModelSerializer):
    feasibility_pct = serializers.FloatField(read_only=True)
    missing_count = serializers.IntegerField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'cover_image', 'difficulty',
            'category_name', 'average_rating',
            'feasibility_pct', 'missing_count',
        )
