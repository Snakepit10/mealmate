from django.urls import path

from .views import (
    CalendarListView,
    CalendarDetailView,
    SlotListView,
    SlotDetailView,
    EntryListView,
    EntryDetailView,
    EntryCopyView,
    EntryMoveView,
    PlanWeekView,
    CheckPantryView,
)

urlpatterns = [
    path('calendars/', CalendarListView.as_view(), name='calendar-list'),
    path('calendars/<uuid:cid>/', CalendarDetailView.as_view(), name='calendar-detail'),
    path('calendars/<uuid:cid>/slots/', SlotListView.as_view(), name='slot-list'),
    path('calendars/<uuid:cid>/slots/<uuid:sid>/', SlotDetailView.as_view(), name='slot-detail'),
    path('calendars/<uuid:cid>/slots/<uuid:sid>/entries/', EntryListView.as_view(), name='entry-list'),
    path('calendars/<uuid:cid>/slots/<uuid:sid>/entries/<uuid:eid>/', EntryDetailView.as_view(), name='entry-detail'),
    path('calendars/<uuid:cid>/slots/<uuid:sid>/entries/<uuid:eid>/copy/', EntryCopyView.as_view(), name='entry-copy'),
    path('calendars/<uuid:cid>/slots/<uuid:sid>/entries/<uuid:eid>/move/', EntryMoveView.as_view(), name='entry-move'),
    path('calendars/<uuid:cid>/plan-week/', PlanWeekView.as_view(), name='plan-week'),
    path('calendars/<uuid:cid>/check-pantry/', CheckPantryView.as_view(), name='check-pantry'),
]
