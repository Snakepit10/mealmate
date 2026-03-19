from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class MealCalendar(TimeStampedModel):
    family = models.ForeignKey(
        'families.Family',
        on_delete=models.CASCADE,
        related_name='calendars',
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#4CAF50')  # hex
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_calendars',
    )

    class Meta:
        verbose_name = 'calendario pasti'
        verbose_name_plural = 'calendari pasti'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} — {self.family.name}'


class MealSlot(TimeStampedModel):
    BREAKFAST = 'breakfast'
    LUNCH = 'lunch'
    DINNER = 'dinner'
    SNACK = 'snack'
    MEAL_TYPE_CHOICES = [
        (BREAKFAST, 'Colazione'),
        (LUNCH, 'Pranzo'),
        (DINNER, 'Cena'),
        (SNACK, 'Spuntino'),
    ]

    calendar = models.ForeignKey(MealCalendar, on_delete=models.CASCADE, related_name='slots')
    date = models.DateField()
    meal_type = models.CharField(max_length=10, choices=MEAL_TYPE_CHOICES)

    class Meta:
        verbose_name = 'slot pasto'
        verbose_name_plural = 'slot pasto'
        unique_together = [('calendar', 'date', 'meal_type')]
        ordering = ('date', 'meal_type')

    def __str__(self):
        return f'{self.calendar.name} — {self.date} {self.get_meal_type_display()}'


class MealEntry(TimeStampedModel):
    slot = models.ForeignKey(MealSlot, on_delete=models.CASCADE, related_name='entries')
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='meal_entries',
    )
    note = models.CharField(max_length=500, blank=True)
    assigned_members = models.ManyToManyField(
        'families.FamilyMember',
        blank=True,
        related_name='meal_entries',
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='meal_additions',
    )

    class Meta:
        verbose_name = 'voce pasto'
        verbose_name_plural = 'voci pasto'
        ordering = ('created_at',)

    def __str__(self):
        if self.recipe:
            return f'{self.recipe.title} — {self.slot}'
        return f'{self.note} — {self.slot}'


class MealCalendarShare(TimeStampedModel):
    PERMISSION_READ = 'read'
    PERMISSION_WRITE = 'write'
    PERMISSION_CHOICES = [
        (PERMISSION_READ, 'Lettura'),
        (PERMISSION_WRITE, 'Scrittura'),
    ]

    calendar = models.ForeignKey(MealCalendar, on_delete=models.CASCADE, related_name='shares')
    shared_with_family = models.ForeignKey(
        'families.Family',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='calendar_shares',
    )
    shared_with_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='calendar_shares',
    )
    permission = models.CharField(max_length=5, choices=PERMISSION_CHOICES, default=PERMISSION_READ)

    class Meta:
        verbose_name = 'condivisione calendario'
        verbose_name_plural = 'condivisioni calendario'
