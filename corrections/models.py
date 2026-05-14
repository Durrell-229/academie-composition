import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Bareme(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.OneToOneField(
        'exams.Exam', on_delete=models.CASCADE, related_name='bareme',
        verbose_name=_('épreuve')
    )
    titre = models.CharField(_('titre'), max_length=300, blank=True)
    total_points = models.DecimalField(_('total points'), max_digits=5, decimal_places=2, default=20)
    donnees = models.JSONField(_('données barème'), default=dict)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='baremes_crees', verbose_name=_('créé par')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('barème')
        verbose_name_plural = _('barèmes')
        ordering = ['-created_at']

    def __str__(self):
        return f"Barème — {self.exam.titre}"

    def to_dict(self):
        return {
            'titre': self.titre or str(self),
            'total_points': float(self.total_points),
            **self.donnees,
        }
