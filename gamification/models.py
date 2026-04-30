import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Badge(models.Model):
    class Categorie(models.TextChoices):
        ACADEMIQUE = 'academique', _('Académique')
        PARTICIPATION = 'participation', _('Participation')
        EXCELLENCE = 'excellence', _('Excellence')
        PROGRESSION = 'progression', _('Progression')
        SOCIAL = 'social', _('Social')
        SPECIAL = 'special', _('Spécial')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(_('nom'), max_length=100)
    description = models.TextField(_('description'))
    icone = models.CharField(_('icône'), max_length=50, default='🏆')
    categorie = models.CharField(_('catégorie'), max_length=20, choices=Categorie.choices, default=Categorie.ACADEMIQUE)
    points = models.PositiveIntegerField(_('points'), default=10)
    condition_obtention = models.JSONField(_('conditions'), default=dict)
    est_actif = models.BooleanField(_('actif'), default=True)
    rarete = models.CharField(_('rareté'), max_length=20, default='commun',
                              choices=[('commun', 'Commun'), ('rare', 'Rare'), ('epique', 'Épique'), ('legendaire', 'Légendaire')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('badge')
        verbose_name_plural = _('badges')
        ordering = ['categorie', '-points']

    def __str__(self):
        return f"{self.icone} {self.nom}"


class UserBadge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='attributions')
    obtenu_at = models.DateTimeField(_('obtenu le'), default=timezone.now)
    est_nouveau = models.BooleanField(_('nouveau'), default=True)

    class Meta:
        verbose_name = _('badge utilisateur')
        verbose_name_plural = _('badges utilisateur')
        unique_together = ['user', 'badge']
        ordering = ['-obtenu_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.badge.nom}"


class GlobalLeaderboard(models.Model):
    class Periode(models.TextChoices):
        JOUR = 'jour', _('Journalier')
        SEMAINE = 'semaine', _('Hebdomadaire')
        MOIS = 'mois', _('Mensuel')
        ANNEE = 'annee', _('Annuel')
        ALL_TIME = 'all_time', _('Tous les temps')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leaderboard_entries')
    periode = models.CharField(_('période'), max_length=20, choices=Periode.choices, default=Periode.ALL_TIME)
    date_periode = models.DateField(_('date de la période'))
    rang_mondial = models.PositiveIntegerField(_('rang mondial'), default=0)
    rang_national = models.PositiveIntegerField(_('rang national'), default=0)
    score_total = models.DecimalField(_('score total'), max_digits=10, decimal_places=2, default=0)
    nb_compositions = models.PositiveIntegerField(_('compositions'), default=0)
    nb_excellentes = models.PositiveIntegerField(_('notes excellentes'), default=0)
    moyenne = models.DecimalField(_('moyenne'), max_digits=5, decimal_places=2, default=0)
    points_xp = models.PositiveIntegerField(_('points XP'), default=0)
    niveau = models.PositiveIntegerField(_('niveau'), default=1)
    streak_jours = models.PositiveIntegerField(_('série de jours'), default=0)
    pays = models.CharField(_('pays'), max_length=100, default='France')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('classement')
        verbose_name_plural = _('classements')
        unique_together = ['user', 'periode', 'date_periode']
        ordering = ['rang_mondial']

    def __str__(self):
        return f"#{self.rang_mondial} {self.user.full_name} ({self.get_periode_display()})"


class XPAction(models.Model):
    """Journal des actions donnant des points XP."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='xp_actions')
    action = models.CharField(_('action'), max_length=100)
    points_gagnes = models.PositiveIntegerField(_('points gagnés'), default=0)
    description = models.TextField(_('description'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('action XP')
        verbose_name_plural = _('actions XP')
        ordering = ['-created_at']


class StreakRecord(models.Model):
    """Série de jours consécutifs d'activité."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.PositiveIntegerField(_('série actuelle'), default=0)
    longest_streak = models.PositiveIntegerField(_('plus longue série'), default=0)
    last_activity_date = models.DateField(_('dernière activité'), null=True, blank=True)

    class Meta:
        verbose_name = _('série d\'activité')
        verbose_name_plural = _('séries d\'activité')

    def update_streak(self):
        from datetime import date, timedelta
        today = date.today()
        if self.last_activity_date == today:
            return
        if self.last_activity_date == today - timedelta(days=1):
            self.current_streak += 1
        else:
            self.current_streak = 1
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        self.last_activity_date = today
        self.save()
