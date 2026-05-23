import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class StatutCorrection(models.TextChoices):
    EN_ATTENTE = 'pending', 'En attente'
    VALIDATION_ENSEIGNANT = 'corrected', 'Corrigé'
    APPROUVE = 'approved', 'Approuvé'


class CorrectionCopie(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='submissions', null=True, blank=True)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    image = models.ImageField(upload_to='submissions/%Y/%m/', blank=True, null=True)
    corrected_text = models.TextField(blank=True, null=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    note_ia = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    json_resultat = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=StatutCorrection.choices, default=StatutCorrection.EN_ATTENTE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'correction_correctioncopie'

    def __str__(self):
        return f"{self.student.email} - {self.exam.titre if self.exam else 'QCM'}"


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


class CorrectionHumaine(models.Model):
    class Statut(models.TextChoices):
        ASSIGNEE = 'assignee', _('Assignée')
        EN_COURS = 'en_cours', _('En cours')
        TERMINEE = 'terminee', _('Terminée')
        VALIDEE = 'validee', _('Validée')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(
        'compositions.CompositionSession', on_delete=models.CASCADE,
        related_name='correction_humaine', verbose_name=_('session')
    )
    correcteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='corrections_humaines_assignees', verbose_name=_('correcteur')
    )
    assigne_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='corrections_humaines_assignees_par', verbose_name=_('assigné par')
    )
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.ASSIGNEE)
    note = models.DecimalField(_('note'), max_digits=5, decimal_places=2, null=True, blank=True)
    note_sur = models.DecimalField(_('note sur'), max_digits=5, decimal_places=2, default=20)
    commentaire = models.TextField(_('commentaire global'), blank=True)
    details_json = models.JSONField(_('détails par critère'), default=list)
    date_limite = models.DateTimeField(_('date limite'), null=True, blank=True)
    rendu_at = models.DateTimeField(_('rendu le'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('correction humaine')
        verbose_name_plural = _('corrections humaines')
        ordering = ['-created_at']

    def __str__(self):
        return f"Correction humaine — {self.session}"

    def terminer(self, note, commentaire, details=None):
        self.note = note
        self.commentaire = commentaire
        self.details_json = details or []
        self.statut = self.Statut.TERMINEE
        self.rendu_at = timezone.now()
        self.save()

        resultat = getattr(self.session, 'resultat', None)
        if resultat:
            resultat.note = note
            resultat.appreciation = commentaire
            resultat.corrige_par_humain = True
            resultat.corrigeur = self.correcteur
            resultat.corrige_at = self.rendu_at
            resultat.details_correction = {'humain': details or []}
            resultat.save()
