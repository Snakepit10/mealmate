from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsFamilyMember
from core.ws import send_family_event

from apps.pantry.models import PantryItem, PantryHistory
from apps.products.models import Product, UnitOfMeasure
from apps.stores.models import Store, StoreAisle

from .models import ShoppingItem, ShoppingHistory
from .serializers import (
    ShoppingItemSerializer,
    CreateShoppingItemSerializer,
    UpdateShoppingItemSerializer,
    QuickAddSerializer,
    ShoppingHistorySerializer,
    ShoppingHistoryDetailSerializer,
)


def _ws_item_payload(item: ShoppingItem, user_name: str) -> dict:
    return {
        'item_id': str(item.id),
        'product_name': item.product.name,
        'checked': item.checked,
        'updated_by': user_name,
    }


class ShoppingListView(APIView):
    """GET/POST /families/{id}/shopping/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def get(self, request, id):
        qs = (
            ShoppingItem.objects
            .filter(family_id=id)
            .select_related('product', 'product__category', 'product__default_store', 'unit', 'store', 'store_aisle', 'added_by')
        )
        store_id = request.query_params.get('store')
        if store_id:
            qs = qs.filter(store_id=store_id)
        checked = request.query_params.get('checked')
        if checked == 'true':
            qs = qs.filter(checked=True)
        elif checked == 'false':
            qs = qs.filter(checked=False)
        return Response(ShoppingItemSerializer(qs, many=True).data)

    @transaction.atomic
    def post(self, request, id):
        serializer = CreateShoppingItemSerializer(
            data=request.data,
            context={'family_id': id},
        )
        serializer.is_valid(raise_exception=True)
        item = serializer.save(family_id=id, added_by=request.user)
        # Auto-assegna la corsia se store impostato ma aisle non scelto
        if item.store_id and not item.store_aisle_id and item.product.category_id:
            aisle = StoreAisle.objects.filter(
                store_id=item.store_id, product_category_id=item.product.category_id
            ).first()
            if aisle:
                item.store_aisle = aisle
                item.save(update_fields=['store_aisle'])
        send_family_event('shopping', str(id), 'shopping.item_added', _ws_item_payload(item, request.user.name))
        return Response(ShoppingItemSerializer(item).data, status=status.HTTP_201_CREATED)


class ShoppingItemDetailView(APIView):
    """GET/PATCH/DELETE /families/{id}/shopping/{iid}/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def _get_item(self, family_id, iid):
        try:
            return ShoppingItem.objects.select_related(
                'product', 'product__category', 'product__default_store', 'unit', 'store', 'store_aisle', 'added_by'
            ).get(id=iid, family_id=family_id)
        except ShoppingItem.DoesNotExist:
            return None

    def get(self, request, id, iid):
        item = self._get_item(id, iid)
        if not item:
            return Response({'detail': 'Prodotto non trovato nella lista.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ShoppingItemSerializer(item).data)

    @transaction.atomic
    def patch(self, request, id, iid):
        item = self._get_item(id, iid)
        if not item:
            return Response({'detail': 'Prodotto non trovato nella lista.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UpdateShoppingItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        # Se lo store è cambiato, ricalcola la corsia automaticamente dalla categoria
        if 'store' in request.data:
            if item.store_id and item.product.category_id:
                aisle = StoreAisle.objects.filter(
                    store_id=item.store_id, product_category_id=item.product.category_id
                ).first()
                item.store_aisle = aisle  # None se nessuna corsia corrispondente
            else:
                item.store_aisle = None
            item.save(update_fields=['store_aisle'])
        send_family_event('shopping', str(id), 'shopping.item_updated', _ws_item_payload(item, request.user.name))
        return Response(ShoppingItemSerializer(item).data)

    @transaction.atomic
    def delete(self, request, id, iid):
        item = self._get_item(id, iid)
        if not item:
            return Response({'detail': 'Prodotto non trovato nella lista.'}, status=status.HTTP_404_NOT_FOUND)
        payload = _ws_item_payload(item, request.user.name)
        item.delete()
        send_family_event('shopping', str(id), 'shopping.item_removed', payload)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCheckView(APIView):
    """POST /families/{id}/shopping/{iid}/check/
    Spunta prodotto → aggiorna/crea PantryItem come present.
    """

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    @transaction.atomic
    def post(self, request, id, iid):
        try:
            item = ShoppingItem.objects.select_related('product').get(id=iid, family_id=id)
        except ShoppingItem.DoesNotExist:
            return Response({'detail': 'Prodotto non trovato nella lista.'}, status=status.HTTP_404_NOT_FOUND)

        item.checked = True
        item.save(update_fields=['checked', 'updated_at'])

        # Aggiorna o crea PantryItem
        pantry_item, created = PantryItem.objects.update_or_create(
            family_id=id,
            product=item.product,
            defaults={
                'status': PantryItem.STATUS_PRESENT,
                'updated_by': request.user,
            },
        )
        PantryHistory.objects.create(
            pantry_item=pantry_item,
            action=PantryHistory.ACTION_ADDED,
            performed_by=request.user,
        )

        # WebSocket events
        send_family_event('shopping', str(id), 'shopping.item_checked', _ws_item_payload(item, request.user.name))
        send_family_event('pantry', str(id), 'pantry.item_added', {
            'item_id': str(pantry_item.id),
            'product_name': item.product.name,
            'status': PantryItem.STATUS_PRESENT,
            'updated_by': request.user.name,
        })

        return Response(ShoppingItemSerializer(item).data)


class ShoppingUncheckView(APIView):
    """POST /families/{id}/shopping/{iid}/uncheck/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    @transaction.atomic
    def post(self, request, id, iid):
        try:
            item = ShoppingItem.objects.select_related('product').get(id=iid, family_id=id)
        except ShoppingItem.DoesNotExist:
            return Response({'detail': 'Prodotto non trovato nella lista.'}, status=status.HTTP_404_NOT_FOUND)

        item.checked = False
        item.save(update_fields=['checked', 'updated_at'])
        send_family_event('shopping', str(id), 'shopping.item_unchecked', _ws_item_payload(item, request.user.name))
        return Response(ShoppingItemSerializer(item).data)


class ShoppingUnavailableView(APIView):
    """POST /families/{id}/shopping/{iid}/unavailable/ — segna non disponibile oggi"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def post(self, request, id, iid):
        try:
            item = ShoppingItem.objects.select_related('product').get(id=iid, family_id=id)
        except ShoppingItem.DoesNotExist:
            return Response({'detail': 'Prodotto non trovato nella lista.'}, status=status.HTTP_404_NOT_FOUND)

        item.unavailable = not item.unavailable  # toggle
        item.save(update_fields=['unavailable', 'updated_at'])
        send_family_event('shopping', str(id), 'shopping.item_updated', _ws_item_payload(item, request.user.name))
        return Response(ShoppingItemSerializer(item).data)


class ShoppingQuickAddView(APIView):
    """POST /families/{id}/shopping/quick-add/
    Cerca prodotto per nome esatto (case-insensitive); se non esiste, lo crea.
    """

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    @transaction.atomic
    def post(self, request, id):
        serializer = QuickAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product_defaults = {
            'name': data['name'],
            'source': Product.SOURCE_MANUAL,
            'created_by': request.user,
        }
        if data.get('category'):
            from apps.products.models import ProductCategory as PC
            try:
                product_defaults['category'] = PC.objects.get(pk=data['category'])
            except PC.DoesNotExist:
                pass

        product, _ = Product.objects.get_or_create(
            name__iexact=data['name'],
            defaults=product_defaults,
        )

        # Verifica duplicato
        if ShoppingItem.objects.filter(family_id=id, product=product, checked=False).exists():
            return Response(
                {'detail': 'Prodotto già presente nella lista della spesa.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unit = None
        if data.get('unit'):
            unit = UnitOfMeasure.objects.filter(id=data['unit']).first()

        store = None
        if data.get('store'):
            store = Store.objects.filter(id=data['store'], family_id=id).first()

        # Auto-assegna la corsia in base alla categoria del prodotto
        store_aisle = None
        if store and product.category_id:
            store_aisle = StoreAisle.objects.filter(
                store=store, product_category_id=product.category_id
            ).first()

        item = ShoppingItem.objects.create(
            family_id=id,
            product=product,
            quantity=data.get('quantity'),
            unit=unit,
            store=store,
            store_aisle=store_aisle,
            note=data.get('note', ''),
            added_by=request.user,
        )
        send_family_event('shopping', str(id), 'shopping.item_added', _ws_item_payload(item, request.user.name))
        return Response(ShoppingItemSerializer(item).data, status=status.HTTP_201_CREATED)


class ShoppingCompleteView(APIView):
    """POST /families/{id}/shopping/complete/
    Completa la spesa: crea snapshot storico, rimuove tutti gli items.
    """

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    @transaction.atomic
    def post(self, request, id):
        # Solo i prodotti spuntati vengono archiviati e rimossi
        checked_items = list(
            ShoppingItem.objects.filter(family_id=id, checked=True)
            .select_related('product', 'unit', 'store')
        )
        if not checked_items:
            return Response(
                {'detail': 'Nessun prodotto spuntato da completare.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        snapshot = [
            {
                'product_id': str(item.product_id),
                'product_name': item.product.name,
                'quantity': str(item.quantity) if item.quantity else None,
                'unit': item.unit.abbreviation if item.unit else None,
                'store': item.store.name if item.store else None,
                'checked': True,
                'note': item.note,
            }
            for item in checked_items
        ]

        history = ShoppingHistory.objects.create(
            family_id=id,
            completed_by=request.user,
            items=snapshot,
        )

        # Elimina solo i prodotti spuntati, lascia quelli non ancora presi
        ShoppingItem.objects.filter(family_id=id, checked=True).delete()

        send_family_event('shopping', str(id), 'shopping.list_completed', {
            'completed_by': request.user.name,
            'items_count': len(snapshot),
        })

        return Response(ShoppingHistoryDetailSerializer(history).data, status=status.HTTP_201_CREATED)


class ShoppingHistoryListView(APIView):
    """GET /families/{id}/shopping/history/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def get(self, request, id):
        qs = ShoppingHistory.objects.filter(family_id=id).select_related('completed_by')
        return Response(ShoppingHistorySerializer(qs, many=True).data)


class ShoppingHistoryDetailView(APIView):
    """GET /families/{id}/shopping/history/{hid}/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def _get_history(self, family_id, hid):
        try:
            return ShoppingHistory.objects.select_related('completed_by').get(id=hid, family_id=family_id)
        except ShoppingHistory.DoesNotExist:
            return None

    def get(self, request, id, hid):
        history = self._get_history(id, hid)
        if not history:
            return Response({'detail': 'Spesa non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ShoppingHistoryDetailSerializer(history).data)


class ShoppingHistoryReuseView(APIView):
    """POST /families/{id}/shopping/history/{hid}/reuse/
    Riaggiunge alla lista attiva tutti i prodotti di una spesa passata.
    """

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    @transaction.atomic
    def post(self, request, id, hid):
        try:
            history = ShoppingHistory.objects.get(id=hid, family_id=id)
        except ShoppingHistory.DoesNotExist:
            return Response({'detail': 'Spesa non trovata.'}, status=status.HTTP_404_NOT_FOUND)

        added = []
        skipped = []

        for entry in history.items:
            product_id = entry.get('product_id')
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                skipped.append(entry.get('product_name', product_id))
                continue

            if ShoppingItem.objects.filter(family_id=id, product=product, checked=False).exists():
                skipped.append(product.name)
                continue

            item = ShoppingItem.objects.create(
                family_id=id,
                product=product,
                added_by=request.user,
                note=entry.get('note', ''),
            )
            added.append(product.name)
            send_family_event('shopping', str(id), 'shopping.item_added', _ws_item_payload(item, request.user.name))

        return Response({'added': added, 'skipped': skipped})
