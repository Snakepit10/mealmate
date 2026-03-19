from datetime import date, timedelta

from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsFamilyMember
from core.ws import send_family_event

from apps.families.models import FamilyMember
from apps.pantry.models import PantryItem
from apps.recipes.models import Recipe
from apps.shopping.models import ShoppingItem

from .models import MealCalendar, MealSlot, MealEntry
from .serializers import (
    MealCalendarSerializer,
    CreateMealCalendarSerializer,
    MealSlotSerializer,
    CreateMealSlotSerializer,
    MealEntrySerializer,
    CreateMealEntrySerializer,
    UpdateMealEntrySerializer,
    PlanWeekSerializer,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_pantry_and_add_shopping(entry: MealEntry, family_id) -> dict:
    """
    Verifica ingredienti della ricetta in dispensa.
    Crea ShoppingItem per ingredienti mancanti con added_automatically=True.
    Restituisce dict con missing_ingredients e feasibility_pct.
    """
    recipe = entry.recipe
    if not recipe:
        return {'missing_ingredients': [], 'feasibility_pct': None}

    required = list(
        recipe.ingredients.filter(is_optional=False).select_related('product', 'unit')
    )
    if not required:
        return {'missing_ingredients': [], 'feasibility_pct': 100.0}

    present_ids = set(
        PantryItem.objects.filter(
            family_id=family_id,
            status=PantryItem.STATUS_PRESENT,
            product_id__in=[i.product_id for i in required],
        ).values_list('product_id', flat=True)
    )

    missing = []
    for ingredient in required:
        if ingredient.product_id not in present_ids:
            # Crea ShoppingItem solo se non esiste già
            shopping_item, created = ShoppingItem.objects.get_or_create(
                family_id=family_id,
                product=ingredient.product,
                checked=False,
                defaults={
                    'quantity': ingredient.quantity,
                    'unit': ingredient.unit,
                    'added_automatically': True,
                    'source_recipe': recipe,
                    'source_meal_date': entry.slot.date,
                    'added_by': entry.added_by,
                },
            )
            missing.append({
                'product_id': str(ingredient.product_id),
                'product_name': ingredient.product.name,
                'quantity': str(ingredient.quantity) if ingredient.quantity else None,
                'unit': ingredient.unit.abbreviation if ingredient.unit else None,
                'shopping_item_created': created,
            })

    present_count = len(required) - len(missing)
    feasibility_pct = round((present_count / len(required)) * 100, 1)
    return {'missing_ingredients': missing, 'feasibility_pct': feasibility_pct}


def _cleanup_auto_shopping(entry: MealEntry, family_id):
    """
    Quando si elimina un MealEntry, rimuove i ShoppingItem aggiunti automaticamente
    per quella ricetta+data che non sono ancora stati spuntati.
    """
    if not entry.recipe:
        return
    ShoppingItem.objects.filter(
        family_id=family_id,
        source_recipe=entry.recipe,
        source_meal_date=entry.slot.date,
        added_automatically=True,
        checked=False,
    ).delete()


def _set_assigned_members(entry: MealEntry, member_ids: list, family_id):
    """Aggiorna i membri assegnati al pasto, verificando che appartengano alla famiglia."""
    if not member_ids:
        entry.assigned_members.clear()
        return
    members = FamilyMember.objects.filter(id__in=member_ids, family_id=family_id)
    entry.assigned_members.set(members)


def _ws_entry_payload(entry: MealEntry, user_name: str) -> dict:
    return {
        'entry_id': str(entry.id),
        'slot_id': str(entry.slot_id),
        'recipe_title': entry.recipe.title if entry.recipe else None,
        'note': entry.note,
        'updated_by': user_name,
    }


def _get_calendar(family_id, cid):
    try:
        return MealCalendar.objects.get(id=cid, family_id=family_id)
    except MealCalendar.DoesNotExist:
        return None


def _get_slot(calendar_id, sid):
    try:
        return MealSlot.objects.get(id=sid, calendar_id=calendar_id)
    except MealSlot.DoesNotExist:
        return None


# ── Calendar CRUD ─────────────────────────────────────────────────────────────

class CalendarListView(APIView):
    """GET/POST /families/{id}/calendars/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def get(self, request, id):
        calendars = MealCalendar.objects.filter(family_id=id).select_related('created_by')
        return Response(MealCalendarSerializer(calendars, many=True).data)

    @transaction.atomic
    def post(self, request, id):
        serializer = CreateMealCalendarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        calendar = serializer.save(family_id=id, created_by=request.user)
        return Response(MealCalendarSerializer(calendar).data, status=status.HTTP_201_CREATED)


class CalendarDetailView(APIView):
    """GET/PATCH/DELETE /families/{id}/calendars/{cid}/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def get(self, request, id, cid):
        calendar = _get_calendar(id, cid)
        if not calendar:
            return Response({'detail': 'Calendario non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MealCalendarSerializer(calendar).data)

    def patch(self, request, id, cid):
        calendar = _get_calendar(id, cid)
        if not calendar:
            return Response({'detail': 'Calendario non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CreateMealCalendarSerializer(calendar, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MealCalendarSerializer(calendar).data)

    def delete(self, request, id, cid):
        calendar = _get_calendar(id, cid)
        if not calendar:
            return Response({'detail': 'Calendario non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        calendar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Slots ─────────────────────────────────────────────────────────────────────

class SlotListView(APIView):
    """GET/POST /families/{id}/calendars/{cid}/slots/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def get(self, request, id, cid):
        calendar = _get_calendar(id, cid)
        if not calendar:
            return Response({'detail': 'Calendario non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        qs = calendar.slots.prefetch_related('entries__recipe', 'entries__added_by')
        # Filtro per intervallo date
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return Response(MealSlotSerializer(qs, many=True).data)

    @transaction.atomic
    def post(self, request, id, cid):
        calendar = _get_calendar(id, cid)
        if not calendar:
            return Response({'detail': 'Calendario non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CreateMealSlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot, created = MealSlot.objects.get_or_create(
            calendar=calendar,
            date=serializer.validated_data['date'],
            meal_type=serializer.validated_data['meal_type'],
        )
        st = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(MealSlotSerializer(slot).data, status=st)


class SlotDetailView(APIView):
    """GET/DELETE /families/{id}/calendars/{cid}/slots/{sid}/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def get(self, request, id, cid, sid):
        calendar = _get_calendar(id, cid)
        if not calendar:
            return Response({'detail': 'Calendario non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        slot = _get_slot(cid, sid)
        if not slot:
            return Response({'detail': 'Slot non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MealSlotSerializer(slot).data)

    @transaction.atomic
    def delete(self, request, id, cid, sid):
        calendar = _get_calendar(id, cid)
        if not calendar:
            return Response({'detail': 'Calendario non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        slot = _get_slot(cid, sid)
        if not slot:
            return Response({'detail': 'Slot non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        # Cleanup shopping items per ogni entry con ricetta
        for entry in slot.entries.filter(recipe__isnull=False):
            _cleanup_auto_shopping(entry, id)
        slot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Entries ───────────────────────────────────────────────────────────────────

class EntryListView(APIView):
    """GET/POST /families/{id}/calendars/{cid}/slots/{sid}/entries/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def get(self, request, id, cid, sid):
        slot = _get_slot(cid, sid)
        if not slot:
            return Response({'detail': 'Slot non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        entries = slot.entries.select_related('recipe', 'added_by').prefetch_related('assigned_members')
        return Response(MealEntrySerializer(entries, many=True).data)

    @transaction.atomic
    def post(self, request, id, cid, sid):
        calendar = _get_calendar(id, cid)
        if not calendar:
            return Response({'detail': 'Calendario non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        slot = _get_slot(cid, sid)
        if not slot:
            return Response({'detail': 'Slot non trovato.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CreateMealEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        member_ids = data.pop('assigned_members', [])

        entry = MealEntry.objects.create(
            slot=slot,
            recipe=data.get('recipe'),
            note=data.get('note', ''),
            added_by=request.user,
        )
        _set_assigned_members(entry, member_ids, id)

        # Verifica dispensa e crea shopping items per ingredienti mancanti
        pantry_check = _check_pantry_and_add_shopping(entry, id)

        send_family_event('calendar', str(id), 'calendar.entry_added', _ws_entry_payload(entry, request.user.name))

        response_data = {
            **MealEntrySerializer(entry).data,
            **pantry_check,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class EntryDetailView(APIView):
    """PATCH/DELETE /families/{id}/calendars/{cid}/slots/{sid}/entries/{eid}/"""

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def _get_entry(self, sid, eid):
        try:
            return MealEntry.objects.select_related('recipe', 'added_by', 'slot').get(
                id=eid, slot_id=sid
            )
        except MealEntry.DoesNotExist:
            return None

    @transaction.atomic
    def patch(self, request, id, cid, sid, eid):
        entry = self._get_entry(sid, eid)
        if not entry:
            return Response({'detail': 'Voce non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UpdateMealEntrySerializer(entry, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        member_ids = data.pop('assigned_members', None)
        for attr, value in data.items():
            setattr(entry, attr, value)
        entry.save()
        if member_ids is not None:
            _set_assigned_members(entry, member_ids, id)
        send_family_event('calendar', str(id), 'calendar.entry_updated', _ws_entry_payload(entry, request.user.name))
        return Response(MealEntrySerializer(entry).data)

    @transaction.atomic
    def delete(self, request, id, cid, sid, eid):
        entry = self._get_entry(sid, eid)
        if not entry:
            return Response({'detail': 'Voce non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        payload = _ws_entry_payload(entry, request.user.name)
        _cleanup_auto_shopping(entry, id)
        entry.delete()
        send_family_event('calendar', str(id), 'calendar.entry_removed', payload)
        return Response(status=status.HTTP_204_NO_CONTENT)


class EntryCopyView(APIView):
    """POST /families/{id}/calendars/{cid}/slots/{sid}/entries/{eid}/copy/
    Copia una voce pasto in un altro slot.
    Body: { "target_slot_id": "uuid" }
    """

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    @transaction.atomic
    def post(self, request, id, cid, sid, eid):
        try:
            entry = MealEntry.objects.select_related('recipe', 'slot').get(id=eid, slot_id=sid)
        except MealEntry.DoesNotExist:
            return Response({'detail': 'Voce non trovata.'}, status=status.HTTP_404_NOT_FOUND)

        target_slot_id = request.data.get('target_slot_id')
        if not target_slot_id:
            return Response({'detail': 'target_slot_id obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            target_slot = MealSlot.objects.get(id=target_slot_id, calendar__family_id=id)
        except MealSlot.DoesNotExist:
            return Response({'detail': 'Slot destinazione non trovato.'}, status=status.HTTP_404_NOT_FOUND)

        new_entry = MealEntry.objects.create(
            slot=target_slot,
            recipe=entry.recipe,
            note=entry.note,
            added_by=request.user,
        )
        new_entry.assigned_members.set(entry.assigned_members.all())
        pantry_check = _check_pantry_and_add_shopping(new_entry, id)
        send_family_event('calendar', str(id), 'calendar.entry_added', _ws_entry_payload(new_entry, request.user.name))

        return Response({
            **MealEntrySerializer(new_entry).data,
            **pantry_check,
        }, status=status.HTTP_201_CREATED)


class EntryMoveView(APIView):
    """POST /families/{id}/calendars/{cid}/slots/{sid}/entries/{eid}/move/
    Sposta una voce pasto in un altro slot.
    Body: { "target_slot_id": "uuid" }
    """

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    @transaction.atomic
    def post(self, request, id, cid, sid, eid):
        try:
            entry = MealEntry.objects.select_related('recipe', 'slot').get(id=eid, slot_id=sid)
        except MealEntry.DoesNotExist:
            return Response({'detail': 'Voce non trovata.'}, status=status.HTTP_404_NOT_FOUND)

        target_slot_id = request.data.get('target_slot_id')
        if not target_slot_id:
            return Response({'detail': 'target_slot_id obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            target_slot = MealSlot.objects.get(id=target_slot_id, calendar__family_id=id)
        except MealSlot.DoesNotExist:
            return Response({'detail': 'Slot destinazione non trovato.'}, status=status.HTTP_404_NOT_FOUND)

        # Cleanup shopping auto del vecchio slot
        _cleanup_auto_shopping(entry, id)
        old_slot = entry.slot
        entry.slot = target_slot
        entry.save(update_fields=['slot', 'updated_at'])

        pantry_check = _check_pantry_and_add_shopping(entry, id)
        send_family_event('calendar', str(id), 'calendar.entry_updated', _ws_entry_payload(entry, request.user.name))

        return Response({
            **MealEntrySerializer(entry).data,
            **pantry_check,
        })


# ── Plan Week ─────────────────────────────────────────────────────────────────

class PlanWeekView(APIView):
    """POST /families/{id}/calendars/{cid}/plan-week/
    Crea in blocco slot + entry per una settimana.
    Body: { "entries": [{ "date": "...", "meal_type": "...", "recipe_id": "...", "note": "..." }, ...] }
    """

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    @transaction.atomic
    def post(self, request, id, cid):
        calendar = _get_calendar(id, cid)
        if not calendar:
            return Response({'detail': 'Calendario non trovato.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PlanWeekSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_entries = []
        errors = []

        for item in serializer.validated_data['entries']:
            try:
                slot, _ = MealSlot.objects.get_or_create(
                    calendar=calendar,
                    date=item['date'],
                    meal_type=item['meal_type'],
                )
                recipe = None
                if item.get('recipe_id'):
                    recipe = Recipe.objects.filter(id=item['recipe_id']).first()

                entry = MealEntry.objects.create(
                    slot=slot,
                    recipe=recipe,
                    note=item.get('note', ''),
                    added_by=request.user,
                )
                pantry_check = _check_pantry_and_add_shopping(entry, id)
                send_family_event('calendar', str(id), 'calendar.entry_added', _ws_entry_payload(entry, request.user.name))
                created_entries.append({
                    **MealEntrySerializer(entry).data,
                    **pantry_check,
                })
            except Exception as e:
                errors.append({'item': item, 'error': str(e)})

        return Response({'created': created_entries, 'errors': errors}, status=status.HTTP_201_CREATED)


# ── Check Pantry ──────────────────────────────────────────────────────────────

class CheckPantryView(APIView):
    """GET /families/{id}/calendars/{cid}/check-pantry/?from=YYYY-MM-DD&to=YYYY-MM-DD
    Verifica disponibilità ingredienti per tutti i pasti nell'intervallo indicato.
    """

    def get_permissions(self):
        return [IsAuthenticated(), IsFamilyMember()]

    def get(self, request, id, cid):
        calendar = _get_calendar(id, cid)
        if not calendar:
            return Response({'detail': 'Calendario non trovato.'}, status=status.HTTP_404_NOT_FOUND)

        date_from = request.query_params.get('from', str(date.today()))
        date_to = request.query_params.get('to', str(date.today() + timedelta(days=6)))

        present_ids = set(
            PantryItem.objects.filter(
                family_id=id, status=PantryItem.STATUS_PRESENT
            ).values_list('product_id', flat=True)
        )

        slots = (
            MealSlot.objects
            .filter(calendar=calendar, date__range=[date_from, date_to])
            .prefetch_related('entries__recipe__ingredients__product', 'entries__recipe__ingredients__unit')
        )

        result = []
        for slot in slots:
            slot_data = {
                'slot_id': str(slot.id),
                'date': str(slot.date),
                'meal_type': slot.meal_type,
                'entries': [],
            }
            for entry in slot.entries.all():
                if not entry.recipe:
                    continue
                required = [i for i in entry.recipe.ingredients.all() if not i.is_optional]
                missing = [
                    {'product_id': str(i.product_id), 'product_name': i.product.name}
                    for i in required if i.product_id not in present_ids
                ]
                pct = round(((len(required) - len(missing)) / len(required) * 100), 1) if required else 100.0
                slot_data['entries'].append({
                    'entry_id': str(entry.id),
                    'recipe_title': entry.recipe.title,
                    'feasibility_pct': pct,
                    'missing_ingredients': missing,
                })
            if slot_data['entries']:
                result.append(slot_data)

        return Response(result)
