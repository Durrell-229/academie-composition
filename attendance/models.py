"""
Modèles pour la gestion des absences et retards
Permet de gérer la présence, les absences et les retards des élèves
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from schools.models import Etablissement, Classe


class Presence(models.Model):
    """Enregistrement de présence d'un élève"""
    
    class StatutPresence(models.TextChoices):
        PRESENT = 'present', _('Présent')
        ABSENT = 'absent', _('Absent')
        RETARD = 'retard', _('Retard')
        EXCUSE = 'excuse', _('Excusé')
        MALADE = 'malade', _('Malade')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='presences', limit_choices_to={'role': 'eleve'})
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='presences')
    professeur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='presences_signees', limit_choices_to={'role': 'professeur'})
    
    date = models.DateField(_('date'), db_index=True)
    heure_arrivee = models.TimeField(_('heure d\'arrivée'), null=True, blank=True)
    statut = models.CharField(_('statut'), max_length=20, choices=StatutPresence.choices, default=StatutPresence.PRESENT, db_index=True)

    # Détails d'absence/retard
    motif_absence = models.TextField(_('motif d\'absence'), blank=True)
    duree_absence = models.PositiveIntegerField(_('durée d\'absence (heures)'), null=True, blank=True)
    minutes_retard = models.PositiveIntegerField(_('minutes de retard'), default=0)
    
    # Justification
    est_justifie = models.BooleanField(_('justifié'), default=False)
    justificatif = models.FileField(_('justificatif'), upload_to='attendance/justificatifs/', blank=True, null=True)
    date_justification = models.DateField(_('date de justification'), null=True, blank=True)
    
    # Observations
    observations = models.TextField(_('observations'), blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Présence')
        verbose_name_plural = _('Présences')
        unique_together = ['eleve', 'classe', 'date']
        ordering = ['-date', 'eleve__last_name']
    
    def __str__(self):
        return f"{self.eleve.get_full_name()} - {self.date} ({self.get_statut_display()})"


class Retard(models.Model):
    """Enregistrement des retards"""
    
    class TypeRetard(models.TextChoices):
        MATIN = 'matin', _('Retard matin')
        APRES_MIDI = 'apres_midi', _('Retard après-midi')
        COURS = 'cours', _('Retard en cours')
        REUNION = 'reunion', _('Retard réunion')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='retards', limit_choices_to={'role': 'eleve'})
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='retards')
    
    date = models.DateField(_('date'))
    heure_prevue = models.TimeField(_('heure prévue'))
    heure_arrivee = models.TimeField(_('heure d\'arrivée'))
    minutes_retard = models.PositiveIntegerField(_('minutes de retard'))
    
    type_retard = models.CharField(_('type de retard'), max_length=20, choices=TypeRetard.choices)
    motif = models.TextField(_('motif'), blank=True)
    
    # Conséquences
    sanction = models.TextField(_('sanction'), blank=True)
    est_pardonne = models.BooleanField(_('pardonné'), default=False)
    
    # Validation
    signale_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='retards_signales')
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='retards_validees')
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Retard')
        verbose_name_plural = _('Retards')
        ordering = ['-date', '-minutes_retard']
    
    def __str__(self):
        return f"{self.eleve.get_full_name()} - {self.date} ({self.minutes_retard} min)"


class Absence(models.Model):
    """Gestion des absences prolongées"""
    
    class TypeAbsence(models.TextChoices):
        MALADIE = 'maladie', _('Maladie')
        FAMILIALE = 'familiale', _('Raison familiale')
        ACADEMIQUE = 'academique', _('Motif académique')
        DISCIPLINAIRE = 'disciplinaire', _('Motif disciplinaire')
        AUTRE = 'autre', _('Autre')
    
    class StatutAbsence(models.TextChoices):
        EN_COURS = 'en_cours', _('En cours')
        JUSTIFIEE = 'justifiee', _('Justifiée')
        NON_JUSTIFIEE = 'non_justifiee', _('Non justifiée')
        ANNULLEE = 'annulee', _('Annulée')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='absences', limit_choices_to={'role': 'eleve'})
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='absences')
    
    # Période d'absence
    date_debut = models.DateField(_('date de début'))
    date_fin = models.DateField(_('date de fin'), null=True, blank=True)
    duree_jours = models.PositiveIntegerField(_('durée (jours)'), null=True, blank=True)
    
    type_absence = models.CharField(_('type d\'absence'), max_length=20, choices=TypeAbsence.choices)
    statut = models.CharField(_('statut'), max_length=20, choices=StatutAbsence.choices, default=StatutAbsence.EN_COURS)
    
    # Justification
    motif = models.TextField(_('motif'))
    justificatif = models.FileField(_('justificatif'), upload_to='attendance/absences/', blank=True, null=True)
    date_justification = models.DateField(_('date de justification'), null=True, blank=True)
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='absences_validees')
    
    # Impact académique
    cours_manques = models.PositiveIntegerField(_('cours manqués'), default=0)
    evaluations_manquees = models.PositiveIntegerField(_('évaluations manquées'), default=0)
    
    # Observations
    observations = models.TextField(_('observations'), blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Absence')
        verbose_name_plural = _('Absences')
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.eleve.get_full_name()} - {self.date_debut} ({self.get_type_absence_display()})"
    
    def save(self, *args, **kwargs):
        if self.date_fin and self.date_debut:
            self.duree_jours = (self.date_fin - self.date_debut).days + 1
        super().save(*args, **kwargs)


class PresenceProfesseur(models.Model):
    """Présence des professeurs"""
    
    class StatutPresence(models.TextChoices):
        PRESENT = 'present', _('Présent')
        ABSENT = 'absent', _('Absent')
        RETARD = 'retard', _('Retard')
        MISSION = 'mission', _('En mission')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='presences_prof', limit_choices_to={'role': 'professeur'})
    
    date = models.DateField(_('date'))
    heure_arrivee = models.TimeField(_('heure d\'arrivée'), null=True, blank=True)
    heure_depart = models.TimeField(_('heure de départ'), null=True, blank=True)
    statut = models.CharField(_('statut'), max_length=20, choices=StatutPresence.choices, default=StatutPresence.PRESENT)
    
    # Détails
    motif_absence = models.TextField(_('motif d\'absence'), blank=True)
    minutes_retard = models.PositiveIntegerField(_('minutes de retard'), default=0)
    
    # Validation
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='presences_validees')
    
    observations = models.TextField(_('observations'), blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Présence professeur')
        verbose_name_plural = _('Présences professeurs')
        unique_together = ['professeur', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.professeur.get_full_name()} - {self.date} ({self.get_statut_display()})"


class RapportPresence(models.Model):
    """Rapports de présence mensuels/périodiques"""
    
    class TypeRapport(models.TextChoices):
        MENSUEL = 'mensuel', _('Mensuel')
        TRIMESTRIEL = 'trimestriel', _('Trimestriel')
        ANNUEL = 'annuel', _('Annuel')
        PERSONNALISE = 'personnalise', _('Personnalisé')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rapports_presence', limit_choices_to={'role': 'eleve'})
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='rapports_presence')
    
    type_rapport = models.CharField(_('type de rapport'), max_length=20, choices=TypeRapport.choices)
    periode_debut = models.DateField(_('début de période'))
    periode_fin = models.DateField(_('fin de période'))
    
    # Statistiques
    total_jours = models.PositiveIntegerField(_('total jours'))
    jours_presents = models.PositiveIntegerField(_('jours présents'))
    jours_absents = models.PositiveIntegerField(_('jours absents'))
    jours_retards = models.PositiveIntegerField(_('jours retards'))
    taux_presence = models.DecimalField(_('taux de présence (%)'), max_digits=5, decimal_places=2)
    
    # Détail absences
    absences_justifiees = models.PositiveIntegerField(_('absences justifiées'), default=0)
    absences_non_justifiees = models.PositiveIntegerField(_('absences non justifiées'), default=0)
    
    # Commentaires
    commentaire = models.TextField(_('commentaire'), blank=True)
    recommandation = models.TextField(_('recommandation'), blank=True)
    
    # Validation
    genere_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='rapports_presence_generes')
    date_generation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Rapport de présence')
        verbose_name_plural = _('Rapports de présence')
        ordering = ['-periode_fin']
    
    def __str__(self):
        return f"Rapport {self.eleve.get_full_name()} - {self.periode_fin}"
