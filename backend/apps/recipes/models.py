from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class RecipeCategory(TimeStampedModel):
    name = models.CharField(max_length=100)
    level = models.PositiveSmallIntegerField(choices=[(1, 'Livello 1'), (2, 'Livello 2')], default=1)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'categoria ricetta'
        verbose_name_plural = 'categorie ricetta'
        ordering = ('order', 'name')

    def __str__(self):
        if self.parent:
            return f'{self.parent.name} › {self.name}'
        return self.name


class Recipe(TimeStampedModel):
    DIFFICULTY_EASY = 'easy'
    DIFFICULTY_MEDIUM = 'medium'
    DIFFICULTY_HARD = 'hard'
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_EASY, 'Facile'),
        (DIFFICULTY_MEDIUM, 'Media'),
        (DIFFICULTY_HARD, 'Difficile'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    external_link = models.URLField(blank=True)
    servings = models.PositiveSmallIntegerField(null=True, blank=True)
    prep_time = models.PositiveSmallIntegerField(null=True, blank=True, help_text='Minuti')
    cook_time = models.PositiveSmallIntegerField(null=True, blank=True, help_text='Minuti')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default=DIFFICULTY_MEDIUM)
    category = models.ForeignKey(
        RecipeCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recipes',
    )
    family = models.ForeignKey(
        'families.Family',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recipes',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_recipes',
    )
    is_public = models.BooleanField(default=False)
    forked_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='forks',
    )
    is_draft = models.BooleanField(default=True)
    average_rating = models.FloatField(default=0.0)
    ratings_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'ricetta'
        verbose_name_plural = 'ricette'
        ordering = ('-created_at',)

    def __str__(self):
        return self.title

    def update_rating(self):
        from django.db.models import Avg, Count
        result = self.ratings.aggregate(avg=Avg('score'), count=Count('id'))
        self.average_rating = round(result['avg'] or 0.0, 2)
        self.ratings_count = result['count']
        self.save(update_fields=['average_rating', 'ratings_count'])


class RecipeIngredient(TimeStampedModel):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    quantity = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    unit = models.ForeignKey(
        'products.UnitOfMeasure',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recipe_ingredients',
    )
    is_optional = models.BooleanField(default=False)
    note = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'ingrediente'
        verbose_name_plural = 'ingredienti'
        ordering = ('order',)

    def __str__(self):
        return f'{self.product.name} — {self.recipe.title}'


class RecipeInstruction(TimeStampedModel):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='instructions')
    step_number = models.PositiveSmallIntegerField()
    text = models.TextField()
    image = models.ImageField(upload_to='instructions/', blank=True, null=True)

    class Meta:
        verbose_name = 'istruzione'
        verbose_name_plural = 'istruzioni'
        ordering = ('step_number',)
        unique_together = [('recipe', 'step_number')]

    def __str__(self):
        return f'Passo {self.step_number} — {self.recipe.title}'


class RecipeRating(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipe_ratings',
    )
    score = models.PositiveSmallIntegerField()  # 1-5
    comment = models.TextField(blank=True)
    image = models.ImageField(upload_to='ratings/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'valutazione'
        verbose_name_plural = 'valutazioni'
        unique_together = [('recipe', 'user')]
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.user.name} → {self.recipe.title} ({self.score}★)'


class RecipeReport(models.Model):
    REASON_WRONG = 'wrong_content'
    REASON_SPAM = 'spam'
    REASON_INAPPROPRIATE = 'inappropriate'
    REASON_CHOICES = [
        (REASON_WRONG, 'Contenuto errato'),
        (REASON_SPAM, 'Spam'),
        (REASON_INAPPROPRIATE, 'Inappropriato'),
    ]
    STATUS_PENDING = 'pending'
    STATUS_REVIEWED = 'reviewed'
    STATUS_RESOLVED = 'resolved'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'In attesa'),
        (STATUS_REVIEWED, 'Revisionato'),
        (STATUS_RESOLVED, 'Risolto'),
    ]

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipe_reports',
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'segnalazione ricetta'
        verbose_name_plural = 'segnalazioni ricette'
        unique_together = [('recipe', 'reported_by')]
