from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsFamilyMember, IsFamilyAdmin

from .models import Store, StoreAisle, StoreCategory
from .serializers import (
    StoreSerializer,
    CreateStoreSerializer,
    StoreAisleSerializer,
    StoreCategorySerializer,
    AisleReorderSerializer,
)


class StoreCategoryListView(APIView):
    """GET /store-categories/"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        categories = StoreCategory.objects.all()
        return Response(StoreCategorySerializer(categories, many=True).data)


# ── Stores ────────────────────────────────────────────────────────────────────

class StoreListView(APIView):
    """GET/POST /families/{id}/stores/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def _get_family_id(self, kwargs):
        return kwargs.get('id')

    def get(self, request, id):
        stores = (
            Store.objects
            .filter(family_id=id)
            .select_related('store_category')
            .prefetch_related('aisles')
        )
        return Response(StoreSerializer(stores, many=True).data)

    def post(self, request, id):
        # Verifica admin
        if not request.user.family_memberships.filter(family_id=id, role='admin').exists():
            return Response({'detail': 'Solo un admin può aggiungere negozi.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = CreateStoreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store = serializer.save(family_id=id)
        return Response(StoreSerializer(store).data, status=status.HTTP_201_CREATED)


class StoreDetailView(APIView):
    """GET/PATCH/DELETE /families/{id}/stores/{sid}/"""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsFamilyMember()]
        return [IsAuthenticated(), IsFamilyAdmin()]

    def _get_store(self, family_id, sid):
        try:
            return Store.objects.select_related('store_category').get(id=sid, family_id=family_id)
        except Store.DoesNotExist:
            return None

    def get(self, request, id, sid):
        store = self._get_store(id, sid)
        if not store:
            return Response({'detail': 'Negozio non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(StoreSerializer(store).data)

    def patch(self, request, id, sid):
        store = self._get_store(id, sid)
        if not store:
            return Response({'detail': 'Negozio non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CreateStoreSerializer(store, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StoreSerializer(store).data)

    def delete(self, request, id, sid):
        store = self._get_store(id, sid)
        if not store:
            return Response({'detail': 'Negozio non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        store.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Aisles ────────────────────────────────────────────────────────────────────

class AisleListView(APIView):
    """GET/POST /families/{id}/stores/{sid}/aisles/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def _get_store(self, family_id, sid):
        try:
            return Store.objects.get(id=sid, family_id=family_id)
        except Store.DoesNotExist:
            return None

    def get(self, request, id, sid):
        store = self._get_store(id, sid)
        if not store:
            return Response({'detail': 'Negozio non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        aisles = store.aisles.all()
        return Response(StoreAisleSerializer(aisles, many=True).data)

    def post(self, request, id, sid):
        if not request.user.family_memberships.filter(family_id=id, role='admin').exists():
            return Response({'detail': 'Solo un admin può aggiungere corsie.'}, status=status.HTTP_403_FORBIDDEN)
        store = self._get_store(id, sid)
        if not store:
            return Response({'detail': 'Negozio non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        # Assegna order = ultimo + 1
        last_order = store.aisles.order_by('-order').values_list('order', flat=True).first() or 0
        data = request.data.copy()
        # Auto-imposta il nome dalla categoria se non fornito
        if data.get('product_category') and not str(data.get('name', '')).strip():
            from apps.products.models import ProductCategory
            try:
                cat = ProductCategory.objects.get(pk=data['product_category'])
                data['name'] = f"{cat.icon} {cat.name}".strip()
            except ProductCategory.DoesNotExist:
                pass
        serializer = StoreAisleSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        aisle = serializer.save(store=store, order=last_order + 1)
        return Response(StoreAisleSerializer(aisle).data, status=status.HTTP_201_CREATED)


class AisleDetailView(APIView):
    """PATCH/DELETE /families/{id}/stores/{sid}/aisles/{aid}/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyAdmin()]

    def _get_aisle(self, family_id, sid, aid):
        try:
            return StoreAisle.objects.get(id=aid, store_id=sid, store__family_id=family_id)
        except StoreAisle.DoesNotExist:
            return None

    def patch(self, request, id, sid, aid):
        aisle = self._get_aisle(id, sid, aid)
        if not aisle:
            return Response({'detail': 'Corsia non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = StoreAisleSerializer(aisle, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StoreAisleSerializer(aisle).data)

    def delete(self, request, id, sid, aid):
        aisle = self._get_aisle(id, sid, aid)
        if not aisle:
            return Response({'detail': 'Corsia non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        aisle.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AisleReorderView(APIView):
    """POST /families/{id}/stores/{sid}/aisles/reorder/
    Body: { "order": ["uuid1", "uuid2", ...] }
    """

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    @transaction.atomic
    def post(self, request, id, sid):
        try:
            store = Store.objects.get(id=sid, family_id=id)
        except Store.DoesNotExist:
            return Response({'detail': 'Negozio non trovato.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AisleReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ordered_ids = serializer.validated_data['order']

        # Verifica che tutti gli ID appartengano a questo store
        existing_ids = set(
            store.aisles.filter(id__in=ordered_ids).values_list('id', flat=True)
        )
        if len(existing_ids) != len(ordered_ids):
            return Response(
                {'detail': 'Uno o più ID corsia non validi per questo negozio.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for position, aisle_id in enumerate(ordered_ids):
            StoreAisle.objects.filter(id=aisle_id).update(order=position)

        aisles = store.aisles.all()
        return Response(StoreAisleSerializer(aisles, many=True).data)


class StoreDuplicateView(APIView):
    """POST /families/{id}/stores/{sid}/duplicate/
    Crea una copia del negozio (stesso nome + " (copia)") con tutte le corsie.
    """

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyAdmin()]

    @transaction.atomic
    def post(self, request, id, sid):
        try:
            original = (
                Store.objects
                .prefetch_related('aisles')
                .get(id=sid, family_id=id)
            )
        except Store.DoesNotExist:
            return Response({'detail': 'Negozio non trovato.'}, status=status.HTTP_404_NOT_FOUND)

        new_store = Store.objects.create(
            family_id=id,
            name=f"{original.name} (copia)",
            store_category=original.store_category,
            is_default=False,  # mai copiare lo stato predefinito
        )

        # Copia le corsie mantenendo ordine e categoria
        for aisle in original.aisles.order_by('order'):
            StoreAisle.objects.create(
                store=new_store,
                name=aisle.name,
                order=aisle.order,
                product_category=aisle.product_category,
            )

        return Response(StoreSerializer(new_store).data, status=status.HTTP_201_CREATED)
