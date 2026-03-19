from datetime import date, timedelta

from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsFamilyMember
from core.ws import send_family_event

from apps.shopping.models import ShoppingItem
from apps.stores.models import StoreAisle

from .models import PantryItem, PantryHistory
from .serializers import (
    PantryItemSerializer,
    CreatePantryItemSerializer,
    UpdatePantryItemSerializer,
    PantryHistorySerializer,
)


def _ws_payload(item: PantryItem, user_name: str) -> dict:
    return {
        'item_id': str(item.id),
        'product_name': item.product.name,
        'status': item.status,
        'updated_by': user_name,
    }


class PantryListView(APIView):
    """GET /families/{id}/pantry/   POST /families/{id}/pantry/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def get(self, request, id):
        qs = (
            PantryItem.objects
            .filter(family_id=id)
            .select_related('product', 'product__category', 'product__default_store', 'updated_by')
        )
        status_filter = request.query_params.get('status')
        if status_filter in (PantryItem.STATUS_PRESENT, PantryItem.STATUS_FINISHED):
            qs = qs.filter(status=status_filter)
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(product__name__icontains=search)
        return Response(PantryItemSerializer(qs, many=True).data)

    @transaction.atomic
    def post(self, request, id):
        serializer = CreatePantryItemSerializer(
            data=request.data,
            context={'family_id': id},
        )
        serializer.is_valid(raise_exception=True)
        item = serializer.save(
            family_id=id,
            status=PantryItem.STATUS_PRESENT,
            updated_by=request.user,
        )
        PantryHistory.objects.create(
            pantry_item=item,
            action=PantryHistory.ACTION_ADDED,
            performed_by=request.user,
        )
        send_family_event('pantry', str(id), 'pantry.item_added', _ws_payload(item, request.user.name))
        return Response(PantryItemSerializer(item).data, status=status.HTTP_201_CREATED)


class PantryDetailView(APIView):
    """GET/PATCH/DELETE /families/{id}/pantry/{pid}/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def _get_item(self, family_id, pid):
        try:
            return PantryItem.objects.select_related(
                'product', 'product__category', 'product__default_store', 'updated_by'
            ).get(id=pid, family_id=family_id)
        except PantryItem.DoesNotExist:
            return None

    def get(self, request, id, pid):
        item = self._get_item(id, pid)
        if not item:
            return Response({'detail': 'Prodotto non trovato in dispensa.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(PantryItemSerializer(item).data)

    @transaction.atomic
    def patch(self, request, id, pid):
        item = self._get_item(id, pid)
        if not item:
            return Response({'detail': 'Prodotto non trovato in dispensa.'}, status=status.HTTP_404_NOT_FOUND)
        old_status = item.status
        serializer = UpdatePantryItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        item = serializer.save(updated_by=request.user)

        PantryHistory.objects.create(
            pantry_item=item,
            action=PantryHistory.ACTION_UPDATED,
            performed_by=request.user,
        )
        send_family_event('pantry', str(id), 'pantry.item_updated', _ws_payload(item, request.user.name))
        return Response(PantryItemSerializer(item).data)

    @transaction.atomic
    def delete(self, request, id, pid):
        item = self._get_item(id, pid)
        if not item:
            return Response({'detail': 'Prodotto non trovato in dispensa.'}, status=status.HTTP_404_NOT_FOUND)
        payload = _ws_payload(item, request.user.name)
        item.delete()
        send_family_event('pantry', str(id), 'pantry.item_removed', payload)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PantryFinishView(APIView):
    """POST /families/{id}/pantry/{pid}/finish/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    @transaction.atomic
    def post(self, request, id, pid):
        try:
            item = PantryItem.objects.select_related(
                'product', 'product__category', 'product__default_store'
            ).get(id=pid, family_id=id)
        except PantryItem.DoesNotExist:
            return Response({'detail': 'Prodotto non trovato in dispensa.'}, status=status.HTTP_404_NOT_FOUND)

        item.status = PantryItem.STATUS_FINISHED
        item.expiry_date = None          # azzerare la scadenza al termine del prodotto
        item.updated_by = request.user
        item.save(update_fields=['status', 'expiry_date', 'updated_by', 'updated_at'])

        PantryHistory.objects.create(
            pantry_item=item,
            action=PantryHistory.ACTION_FINISHED,
            performed_by=request.user,
        )
        send_family_event('pantry', str(id), 'pantry.item_finished', _ws_payload(item, request.user.name))

        # Se il prodotto ha un negozio predefinito → aggiunge automaticamente alla lista spesa
        if item.product.default_store_id:
            store = item.product.default_store
            already_in_list = ShoppingItem.objects.filter(
                family_id=id, product=item.product, checked=False
            ).exists()
            if not already_in_list:
                # Auto-assegna la corsia in base alla categoria del prodotto
                aisle = None
                if item.product.category_id:
                    aisle = StoreAisle.objects.filter(
                        store=store, product_category_id=item.product.category_id
                    ).first()
                shopping_item = ShoppingItem.objects.create(
                    family_id=id,
                    product=item.product,
                    store=store,
                    store_aisle=aisle,
                    added_by=request.user,
                    added_automatically=True,
                )
                send_family_event('shopping', str(id), 'shopping.item_added', {
                    'item_id': str(shopping_item.id),
                    'product_name': item.product.name,
                    'checked': False,
                    'updated_by': request.user.name,
                })
            return Response({
                **PantryItemSerializer(item).data,
                'auto_added_store': store.name,
            })

        # Nessun negozio predefinito → il frontend chiede se aggiungere
        return Response({
            **PantryItemSerializer(item).data,
            'suggest_shopping': True,
        })


class PantryRestoreView(APIView):
    """POST /families/{id}/pantry/{pid}/restore/
    Riporta un prodotto terminato allo stato presente.
    """

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    @transaction.atomic
    def post(self, request, id, pid):
        try:
            item = PantryItem.objects.select_related(
                'product', 'product__category', 'product__default_store'
            ).get(id=pid, family_id=id)
        except PantryItem.DoesNotExist:
            return Response({'detail': 'Prodotto non trovato in dispensa.'}, status=status.HTTP_404_NOT_FOUND)

        if item.status == PantryItem.STATUS_PRESENT:
            return Response({'detail': 'Il prodotto è già presente in dispensa.'}, status=status.HTTP_400_BAD_REQUEST)

        item.status = PantryItem.STATUS_PRESENT
        item.updated_by = request.user
        item.save(update_fields=['status', 'updated_by', 'updated_at'])

        PantryHistory.objects.create(
            pantry_item=item,
            action=PantryHistory.ACTION_ADDED,
            performed_by=request.user,
        )
        send_family_event('pantry', str(id), 'pantry.item_added', _ws_payload(item, request.user.name))
        return Response(PantryItemSerializer(item).data)


class PantryExpiringView(APIView):
    """GET /families/{id}/pantry/expiring/  — prodotti in scadenza entro N giorni"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def get(self, request, id):
        days = int(request.query_params.get('days', 3))
        threshold = date.today() + timedelta(days=days)
        qs = (
            PantryItem.objects
            .filter(
                family_id=id,
                status=PantryItem.STATUS_PRESENT,
                expiry_date__isnull=False,
                expiry_date__lte=threshold,
            )
            .select_related('product', 'product__category', 'product__default_store', 'updated_by')
            .order_by('expiry_date')
        )
        return Response(PantryItemSerializer(qs, many=True).data)


class PantryHistoryView(APIView):
    """GET /families/{id}/pantry/history/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def get(self, request, id):
        qs = (
            PantryHistory.objects
            .filter(pantry_item__family_id=id)
            .select_related('pantry_item__product', 'performed_by')
            .order_by('-timestamp')[:100]
        )
        return Response(PantryHistorySerializer(qs, many=True).data)
