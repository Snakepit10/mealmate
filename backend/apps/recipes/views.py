from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import logging

from apps.pantry.models import PantryItem
from apps.products.models import Product, ProductCategory
from integrations.recipe_importer import import_from_url, parse_ingredient_text

logger = logging.getLogger(__name__)

from .models import Recipe, RecipeCategory, RecipeIngredient, RecipeInstruction, RecipeRating, RecipeReport
from .serializers import (
    RecipeCategorySerializer,
    RecipeListSerializer,
    RecipeDetailSerializer,
    CreateRecipeSerializer,
    RecipeIngredientSerializer,
    RecipeInstructionSerializer,
    RecipeRatingSerializer,
    RecipeReportSerializer,
    InstructionReorderSerializer,
    RecipeSuggestionSerializer,
)


def _can_edit_recipe(user, recipe: Recipe) -> bool:
    """L'utente può modificare la ricetta se ne è il creatore o è admin della famiglia."""
    if recipe.created_by == user:
        return True
    if recipe.family:
        return user.family_memberships.filter(family=recipe.family, role='admin').exists()
    return False


def _visible_recipes(user, family_id=None):
    """Ricette visibili: pubbliche + della propria famiglia."""
    family_ids = user.family_memberships.values_list('family_id', flat=True)
    qs = Recipe.objects.filter(is_draft=False).filter(
        Q(is_public=True) | Q(family_id__in=family_ids)
    )
    if family_id:
        qs = qs.filter(Q(is_public=True) | Q(family_id=family_id))
    return qs.select_related('category', 'created_by')


# ── Recipe CRUD ───────────────────────────────────────────────────────────────

class RecipeListView(APIView):
    """GET /recipes/   POST /recipes/"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        qs = _visible_recipes(request.user)
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
        difficulty = request.query_params.get('difficulty')
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category_id=category)
        family_id = request.query_params.get('family_id')
        if family_id:
            qs = qs.filter(family_id=family_id)
        # Mostra anche le draft personali
        include_drafts = request.query_params.get('drafts') == 'true'
        if include_drafts:
            drafts = Recipe.objects.filter(is_draft=True, created_by=request.user)
            qs = (qs | drafts).distinct()
        return Response(RecipeListSerializer(qs[:50], many=True).data)

    @transaction.atomic
    def post(self, request):
        serializer = CreateRecipeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        family_id = request.data.get('family_id')
        recipe = serializer.save(created_by=request.user, family_id=family_id)
        return Response(RecipeDetailSerializer(recipe).data, status=status.HTTP_201_CREATED)


class RecipeDetailView(APIView):
    """GET/PATCH/DELETE /recipes/{id}/"""
    permission_classes = (IsAuthenticated,)

    def _get_recipe(self, recipe_id, user):
        try:
            return Recipe.objects.select_related('category', 'created_by', 'forked_from').get(id=recipe_id)
        except Recipe.DoesNotExist:
            return None

    def _check_visibility(self, recipe, user):
        if recipe.is_public or recipe.created_by == user:
            return True
        if recipe.family:
            return user.family_memberships.filter(family=recipe.family).exists()
        return False

    def get(self, request, id):
        recipe = self._get_recipe(id, request.user)
        if not recipe or not self._check_visibility(recipe, request.user):
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(RecipeDetailSerializer(recipe).data)

    @transaction.atomic
    def patch(self, request, id):
        recipe = self._get_recipe(id, request.user)
        if not recipe:
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_edit_recipe(request.user, recipe):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = CreateRecipeSerializer(recipe, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RecipeDetailSerializer(recipe).data)

    @transaction.atomic
    def delete(self, request, id):
        recipe = self._get_recipe(id, request.user)
        if not recipe:
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_edit_recipe(request.user, recipe):
            return Response(status=status.HTTP_403_FORBIDDEN)
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Publish / Fork / Report ───────────────────────────────────────────────────

class RecipePublishView(APIView):
    """POST /recipes/{id}/publish/"""
    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        try:
            recipe = Recipe.objects.get(id=id)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_edit_recipe(request.user, recipe):
            return Response(status=status.HTTP_403_FORBIDDEN)
        recipe.is_public = True
        recipe.is_draft = False
        recipe.save(update_fields=['is_public', 'is_draft'])
        return Response(RecipeDetailSerializer(recipe).data)


class RecipeUnpublishView(APIView):
    """POST /recipes/{id}/unpublish/"""
    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        try:
            recipe = Recipe.objects.get(id=id)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_edit_recipe(request.user, recipe):
            return Response(status=status.HTTP_403_FORBIDDEN)
        recipe.is_public = False
        recipe.save(update_fields=['is_public'])
        return Response(RecipeDetailSerializer(recipe).data)


class RecipeForkView(APIView):
    """POST /recipes/{id}/fork/ — crea una copia privata della ricetta nella famiglia."""
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    def post(self, request, id):
        try:
            original = Recipe.objects.prefetch_related('ingredients', 'instructions').get(id=id)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)

        family_id = request.data.get('family_id')

        fork = Recipe.objects.create(
            title=f'{original.title} (copia)',
            description=original.description,
            servings=original.servings,
            prep_time=original.prep_time,
            cook_time=original.cook_time,
            difficulty=original.difficulty,
            category=original.category,
            family_id=family_id,
            created_by=request.user,
            is_public=False,
            is_draft=True,
            forked_from=original,
        )
        # Copia ingredienti
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=fork,
                product=ing.product,
                quantity=ing.quantity,
                unit=ing.unit,
                is_optional=ing.is_optional,
                note=ing.note,
                order=ing.order,
            )
            for ing in original.ingredients.all()
        ])
        # Copia istruzioni
        RecipeInstruction.objects.bulk_create([
            RecipeInstruction(
                recipe=fork,
                step_number=inst.step_number,
                text=inst.text,
            )
            for inst in original.instructions.all()
        ])
        return Response(RecipeDetailSerializer(fork).data, status=status.HTTP_201_CREATED)


class RecipeReportView(APIView):
    """POST /recipes/{id}/report/"""
    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        try:
            recipe = Recipe.objects.get(id=id)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = RecipeReportSerializer(
            data=request.data,
            context={'request': request, 'recipe': recipe},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(recipe=recipe, reported_by=request.user)
        return Response({'detail': 'Segnalazione inviata.'}, status=status.HTTP_201_CREATED)


class RecipeImportView(APIView):
    """POST /recipes/import/  Body: { "url": "..." }"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        url = request.data.get('url', '').strip()
        if not url:
            return Response({'detail': 'URL obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = import_from_url(url)
        except NotImplementedError:
            return Response(
                {'detail': 'Il modulo di importazione non è ancora configurato.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception:
            return Response({'success': False, 'url': url}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Parse + auto-crea prodotti per ogni ingrediente grezzo
        try:
            data['ingredients'] = self._resolve_ingredients(data.get('ingredients', []), request.user)
        except Exception as exc:
            logger.error('RecipeImportView: _resolve_ingredients failed: %s', exc)
            # In caso di errore grave, mantieni le stringhe originali
        return Response(data)

    @staticmethod
    def _resolve_ingredients(raw_list, user):
        """
        Per ogni stringa ingrediente:
        1. Separa nome e quantità con parse_ingredient_text()
        2. Cerca un prodotto esistente per nome (case-insensitive)
        3. Se non esiste, ne crea uno nuovo nella categoria "Altro"
           (get_or_create garantisce che la categoria esista sempre)
        Restituisce una lista di dict pronti per il frontend.
        """
        # get_or_create: non dipende dall'ordine delle migration/fixtures
        altro_cat, _ = ProductCategory.objects.get_or_create(
            name='Altro',
            defaults={'icon': '📦', 'order': 99, 'is_food': True},
        )
        resolved = []
        for raw in raw_list:
            parsed = parse_ingredient_text(raw)
            name = parsed['name']
            quantity = parsed['quantity']
            if not name:
                continue
            # Cerca prodotto esistente (nome esatto, case-insensitive)
            product = Product.objects.filter(name__iexact=name).first()
            if not product:
                try:
                    product = Product.objects.create(
                        name=name,
                        category=altro_cat,
                        source='manual',
                        created_by=user,
                        type='food',
                    )
                except Exception as exc:
                    logger.warning('RecipeImportView: could not create product "%s": %s', name, exc)
            resolved.append({
                'raw': raw,
                'product_id': str(product.id) if product else None,
                # Se la creazione del prodotto fallisce, restituiamo comunque il nome parsato
                'product_name': product.name if product else name,
                'quantity': quantity,
            })
        return resolved


# ── Ingredients ───────────────────────────────────────────────────────────────

class RecipeIngredientListView(APIView):
    """GET/POST /recipes/{id}/ingredients/"""
    permission_classes = (IsAuthenticated,)

    def _get_recipe(self, recipe_id):
        try:
            return Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return None

    def get(self, request, id):
        recipe = self._get_recipe(id)
        if not recipe:
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(RecipeIngredientSerializer(
            recipe.ingredients.select_related('product', 'unit').all(), many=True
        ).data)

    @transaction.atomic
    def post(self, request, id):
        recipe = self._get_recipe(id)
        if not recipe:
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_edit_recipe(request.user, recipe):
            return Response(status=status.HTTP_403_FORBIDDEN)
        last_order = recipe.ingredients.order_by('-order').values_list('order', flat=True).first() or 0
        serializer = RecipeIngredientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ingredient = serializer.save(recipe=recipe, order=last_order + 1)
        return Response(RecipeIngredientSerializer(ingredient).data, status=status.HTTP_201_CREATED)


class RecipeIngredientDetailView(APIView):
    """PATCH/DELETE /recipes/{id}/ingredients/{iid}/"""
    permission_classes = (IsAuthenticated,)

    def _get_ingredient(self, recipe_id, iid):
        try:
            return RecipeIngredient.objects.select_related('recipe').get(id=iid, recipe_id=recipe_id)
        except RecipeIngredient.DoesNotExist:
            return None

    def patch(self, request, id, iid):
        ingredient = self._get_ingredient(id, iid)
        if not ingredient:
            return Response({'detail': 'Ingrediente non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_edit_recipe(request.user, ingredient.recipe):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = RecipeIngredientSerializer(ingredient, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RecipeIngredientSerializer(ingredient).data)

    def delete(self, request, id, iid):
        ingredient = self._get_ingredient(id, iid)
        if not ingredient:
            return Response({'detail': 'Ingrediente non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_edit_recipe(request.user, ingredient.recipe):
            return Response(status=status.HTTP_403_FORBIDDEN)
        ingredient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Instructions ──────────────────────────────────────────────────────────────

class RecipeInstructionListView(APIView):
    """GET/POST /recipes/{id}/instructions/"""
    permission_classes = (IsAuthenticated,)

    def _get_recipe(self, recipe_id):
        try:
            return Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return None

    def get(self, request, id):
        recipe = self._get_recipe(id)
        if not recipe:
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(RecipeInstructionSerializer(recipe.instructions.all(), many=True).data)

    @transaction.atomic
    def post(self, request, id):
        recipe = self._get_recipe(id)
        if not recipe:
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_edit_recipe(request.user, recipe):
            return Response(status=status.HTTP_403_FORBIDDEN)
        next_step = (recipe.instructions.order_by('-step_number').values_list('step_number', flat=True).first() or 0) + 1
        serializer = RecipeInstructionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instruction = serializer.save(recipe=recipe, step_number=next_step)
        return Response(RecipeInstructionSerializer(instruction).data, status=status.HTTP_201_CREATED)


class RecipeInstructionDetailView(APIView):
    """PATCH/DELETE /recipes/{id}/instructions/{sid}/"""
    permission_classes = (IsAuthenticated,)

    def _get_instruction(self, recipe_id, sid):
        try:
            return RecipeInstruction.objects.select_related('recipe').get(id=sid, recipe_id=recipe_id)
        except RecipeInstruction.DoesNotExist:
            return None

    def patch(self, request, id, sid):
        instruction = self._get_instruction(id, sid)
        if not instruction:
            return Response({'detail': 'Istruzione non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_edit_recipe(request.user, instruction.recipe):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = RecipeInstructionSerializer(instruction, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RecipeInstructionSerializer(instruction).data)

    def delete(self, request, id, sid):
        instruction = self._get_instruction(id, sid)
        if not instruction:
            return Response({'detail': 'Istruzione non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_edit_recipe(request.user, instruction.recipe):
            return Response(status=status.HTTP_403_FORBIDDEN)
        instruction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeInstructionReorderView(APIView):
    """POST /recipes/{id}/instructions/reorder/"""
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    def post(self, request, id):
        try:
            recipe = Recipe.objects.get(id=id)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_edit_recipe(request.user, recipe):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = InstructionReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ordered_ids = serializer.validated_data['order']
        for step_number, inst_id in enumerate(ordered_ids, start=1):
            RecipeInstruction.objects.filter(id=inst_id, recipe=recipe).update(step_number=step_number)
        return Response(RecipeInstructionSerializer(recipe.instructions.all(), many=True).data)


# ── Ratings ───────────────────────────────────────────────────────────────────

class RecipeRatingListView(APIView):
    """GET/POST /recipes/{id}/ratings/"""
    permission_classes = (IsAuthenticated,)

    def get(self, request, id):
        try:
            recipe = Recipe.objects.get(id=id)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(RecipeRatingSerializer(
            recipe.ratings.select_related('user').all(), many=True
        ).data)

    @transaction.atomic
    def post(self, request, id):
        try:
            recipe = Recipe.objects.get(id=id)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Ricetta non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if RecipeRating.objects.filter(recipe=recipe, user=request.user).exists():
            return Response({'detail': 'Hai già valutato questa ricetta.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = RecipeRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rating = serializer.save(recipe=recipe, user=request.user)
        recipe.update_rating()
        return Response(RecipeRatingSerializer(rating).data, status=status.HTTP_201_CREATED)


class RecipeRatingDetailView(APIView):
    """PATCH/DELETE /recipes/{id}/ratings/{rid}/"""
    permission_classes = (IsAuthenticated,)

    def _get_rating(self, recipe_id, rid):
        try:
            return RecipeRating.objects.select_related('recipe').get(id=rid, recipe_id=recipe_id)
        except RecipeRating.DoesNotExist:
            return None

    def patch(self, request, id, rid):
        rating = self._get_rating(id, rid)
        if not rating:
            return Response({'detail': 'Valutazione non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if rating.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = RecipeRatingSerializer(rating, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        rating.recipe.update_rating()
        return Response(RecipeRatingSerializer(rating).data)

    @transaction.atomic
    def delete(self, request, id, rid):
        rating = self._get_rating(id, rid)
        if not rating:
            return Response({'detail': 'Valutazione non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        if rating.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        recipe = rating.recipe
        rating.delete()
        recipe.update_rating()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Categories & Suggestions ──────────────────────────────────────────────────

class RecipeCategoryListView(APIView):
    """GET /recipes/categories/"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        top_level = RecipeCategory.objects.filter(level=1).prefetch_related('children')
        return Response(RecipeCategorySerializer(top_level, many=True).data)


class RecipeSuggestionView(APIView):
    """GET /recipes/suggestions/?family_id={id}
    Suggerisce ricette in base a ciò che è presente in dispensa.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        family_id = request.query_params.get('family_id')
        if not family_id:
            return Response({'detail': 'family_id obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica appartenenza alla famiglia
        if not request.user.family_memberships.filter(family_id=family_id).exists():
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Prodotti presenti in dispensa
        present_product_ids = set(
            PantryItem.objects.filter(family_id=family_id, status=PantryItem.STATUS_PRESENT)
            .values_list('product_id', flat=True)
        )

        # Ricette visibili
        recipes = _visible_recipes(request.user, family_id=family_id).prefetch_related('ingredients')

        results = []
        for recipe in recipes:
            required = [i for i in recipe.ingredients.all() if not i.is_optional]
            if not required:
                continue
            present = sum(1 for i in required if i.product_id in present_product_ids)
            pct = round((present / len(required)) * 100, 1)
            recipe.feasibility_pct = pct
            recipe.missing_count = len(required) - present
            results.append(recipe)

        results.sort(key=lambda r: r.feasibility_pct, reverse=True)

        # Raggruppa per percentuale
        groups = {
            'perfect': [],    # 100%
            'almost': [],     # 75-99%
            'partial': [],    # 50-74%
            'low': [],        # <50%
        }
        for r in results:
            if r.feasibility_pct == 100:
                groups['perfect'].append(r)
            elif r.feasibility_pct >= 75:
                groups['almost'].append(r)
            elif r.feasibility_pct >= 50:
                groups['partial'].append(r)
            else:
                groups['low'].append(r)

        return Response({
            key: RecipeSuggestionSerializer(recipes, many=True).data
            for key, recipes in groups.items()
        })
