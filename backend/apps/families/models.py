from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from core.utils import generate_invite_code


class Family(TimeStampedModel):
    name = models.CharField(max_length=150)
    invite_code = models.CharField(max_length=8, unique=True, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_families',
    )

    class Meta:
        verbose_name = 'famiglia'
        verbose_name_plural = 'famiglie'

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = self._unique_invite_code()
        super().save(*args, **kwargs)

    def _unique_invite_code(self):
        code = generate_invite_code()
        while Family.objects.filter(invite_code=code).exists():
            code = generate_invite_code()
        return code

    def __str__(self):
        return self.name


class FamilyMember(TimeStampedModel):
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_MEMBER, 'Membro'),
    ]

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='family_memberships',
    )
    # Usato quando user è null (es. figlio senza account)
    name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to='member_avatars/', blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    is_registered = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'membro famiglia'
        verbose_name_plural = 'membri famiglia'
        unique_together = [('family', 'user')]

    def get_display_name(self):
        if self.user:
            return self.user.name
        return self.name

    def __str__(self):
        return f'{self.get_display_name()} — {self.family.name}'
