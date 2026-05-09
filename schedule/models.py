"""
Modèles pour la gestion des emplois du temps interactifs
Permet de gérer les horaires, plannings et emplois du temps scolaires
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from schools.models import Etablissement, Classe


class EmploiDuTemps(models.Model):
    """Emploi du temps pour une classe ou un professeur"""
    
    class TypeCible(models.TextChoices):
        CLASSE = 'classe', _('Classe')
        PROFESSEUR = 'professeur', _('Professeur')
        SALLE = 'salle', _('Salle')
        ETABLISSEMENT = 'etablissement', _('Établissement')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='emplois_du_temps')
    
    type_cible = models.CharField(_('type de cible'), max_length=20, choices=TypeCible.choices)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, null=True, blank=True, related_name='emplois_du_temps')
    professeur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='emplois_du_temps', limit_choices_to={'role': 'professeur'})
    salle = models.CharField(_('salle'), max_length=50, blank=True)
    
    annee_scolaire = models.CharField(_('année scolaire'), max_length=9, default='2024-2025')
    semestre = models.CharField(_('semestre'), max_length=20, default='Semestre 1')
    
    nom = models.CharField(_('nom de l\'emploi du temps'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    is_actif = models.BooleanField(_('actif'), default=True)
    is_public = models.BooleanField(_('public'), default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Emploi du temps')
        verbose_name_plural = _('Emplois du temps')
        ordering = ['annee_scolaire', 'nom']
    
    def __str__(self):
        return f"{self.nom} - {self.annee_scolaire}"


class CreneauHoraire(models.Model):
    """Créneau horaire pour les cours"""
    
    class JourSemaine(models.TextChoices):
        LUNDI = 'lundi', _('Lundi')
        MARDI = 'mardi', _('Mardi')
        MERCREDI = 'mercredi', _('Mercredi')
        JEUDI = 'jeudi', _('Jeudi')
        VENDREDI = 'vendredi', _('Vendredi')
        SAMEDI = 'samedi', _('Samedi')
        DIMANCHE = 'dimanche', _('Dimanche')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emploi_du_temps = models.ForeignKey(EmploiDuTemps, on_delete=models.CASCADE, related_name='creneaux')
    
    jour = models.CharField(_('jour'), max_length=20, choices=JourSemaine.choices)
    heure_debut = models.TimeField(_('heure de début'))
    heure_fin = models.TimeField(_('heure de fin'))
    
    # Cours
    matiere = models.ForeignKey('core.Matiere', on_delete=models.CASCADE, related_name='creneaux')
    professeur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='creneaux', limit_choices_to={'role': 'professeur'})
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='creneaux', null=True, blank=True)
    salle = models.CharField(_('salle'), max_length=50, blank=True)
    
    # Couleur et style
    couleur = models.CharField(_('couleur'), max_length=7, default='#3b82f6')
    note = models.TextField(_('note'), blank=True)
    
    is_actif = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('Créneau horaire')
        verbose_name_plural = _('Créneaux horaires')
        ordering = ['jour', 'heure_debut']
    
    def __str__(self):
        return f"{self.get_jour_display()} - {self.matiere.nom} ({self.heure_debut}-{self.heure_fin})"
    
    @property
    def duree_minutes(self):
        """Calculer la durée en minutes"""
        if self.heure_debut and self.heure_fin:
            debut = self.heure_debut.hour * 60 + self.heure_debut.minute
            fin = self.heure_fin.hour * 60 + self.heure_fin.minute
            return fin - debut
        return 0


class EvenementScolaire(models.Model):
    """Événements scolaires (examens, réunions, activités)"""
    
    class TypeEvenement(models.TextChoices):
        EXAMEN = 'examen', _('Examen')
        REUNION = 'reunion', _('Réunion')
        ACTIVITE = 'activite', _('Activité')
        CONFERENCES = 'conferences', _('Conférences')
        SORTIE = 'sortie', _('Sortie')
        FETE = 'fete', _('Fête')
        AUTRE = 'autre', _('Autre')
    
    class Priorite(models.TextChoices):
        BASSE = 'basse', _('Basse')
        NORMALE = 'normale', _('Normale')
        HAUTE = 'haute', _('Haute')
        URGENTE = 'urgente', _('Urgente')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='evenements')
    
    titre = models.CharField(_('titre'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    type_evenement = models.CharField(_('type d\'événement'), max_length=20, choices=TypeEvenement.choices)
    
    # Dates et heures
    date_debut = models.DateTimeField(_('date et heure de début'))
    date_fin = models.DateTimeField(_('date et heure de fin'))
    duree = models.PositiveIntegerField(_('durée (minutes)'), null=True, blank=True)
    
    # Lieu
    lieu = models.CharField(_('lieu'), max_length=200, blank=True)
    salle = models.CharField(_('salle'), max_length=50, blank=True)
    
    # Participants
    classes_concernees = models.ManyToManyField(Classe, related_name='evenements', blank=True)
    participants = models.ManyToManyField(User, related_name='evenements_participes', blank=True)
    organisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='evenements_organises')
    
    # Priorité et rappel
    priorite = models.CharField(_('priorité'), max_length=20, choices=Priorite.choices, default=Priorite.NORMALE)
    rappel_avant = models.PositiveIntegerField(_('rappel (heures avant)'), default=24)
    
    # Statut
    is_annule = models.BooleanField(_('annulé'), default=False)
    motif_annulation = models.TextField(_('motif d\'annulation'), blank=True)
    
    # Couleur
    couleur = models.CharField(_('couleur'), max_length=7, default='#10b981')
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Événement scolaire')
        verbose_name_plural = _('Événements scolaires')
        ordering = ['date_debut']
    
    def __str__(self):
        return f"{self.titre} - {self.date_debut.strftime('%d/%m/%Y %H:%M')}"


class DisponibiliteProfesseur(models.Model):
    """Disponibilité des professeurs"""
    
    class JourSemaine(models.TextChoices):
        LUNDI = 'lundi', _('Lundi')
        MARDI = 'mardi', _('Mardi')
        MERCREDI = 'mercredi', _('Mercredi')
        JEUDI = 'jeudi', _('Jeudi')
        VENDREDI = 'vendredi', _('Vendredi')
        SAMEDI = 'samedi', _('Samedi')
        DIMANCHE = 'dimanche', _('Dimanche')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disponibilites', limit_choices_to={'role': 'professeur'})
    
    jour = models.CharField(_('jour'), max_length=20, choices=JourSemaine.choices)
    heure_debut_matin = models.TimeField(_('heure début matin'), null=True, blank=True)
    heure_fin_matin = models.TimeField(_('heure fin matin'), null=True, blank=True)
    heure_debut_apresmidi = models.TimeField(_('heure début après-midi'), null=True, blank=True)
    heure_fin_apresmidi = models.TimeField(_('heure fin après-midi'), null=True, blank=True)
    
    # Notes
    notes = models.TextField(_('notes'), blank=True)
    
    is_actif = models.BooleanField(_('actif'), default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Disponibilité professeur')
        verbose_name_plural = _('Disponibilités professeurs')
        unique_together = ['professeur', 'jour']
        ordering = ['professeur', 'jour']
    
    def __str__(self):
        return f"{self.professeur.get_full_name()} - {self.get_jour_display()}"


class Salle(models.Model):
    """Gestion des salles de classe"""
    
    class TypeSalle(models.TextChoices):
        CLASSE = 'classe', _('Salle de classe')
        LABORATOIRE = 'laboratoire', _('Laboratoire')
        INFO = 'info', _('Salle informatique')
        SPORT = 'sport', _('Salle de sport')
        REUNION = 'reunion', _('Salle de réunion')
        BIBLIOTHEQUE = 'bibliotheque', _('Bibliothèque')
        CANTINE = 'cantine', _('Cantine')
        AUTRE = 'autre', _('Autre')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='salles')
    campus = models.ForeignKey('schools.Campus', on_delete=models.SET_NULL, null=True, blank=True, related_name='salles')
    
    nom = models.CharField(_('nom de la salle'), max_length=100)
    code = models.CharField(_('code'), max_length=20, unique=True)
    type_salle = models.CharField(_('type de salle'), max_length=20, choices=TypeSalle.choices)
    
    # Capacité et équipement
    capacite = models.PositiveIntegerField(_('capacité'), default=30)
    superficie = models.DecimalField(_('superficie (m²)'), max_digits=8, decimal_places=2, null=True, blank=True)
    equipements = models.TextField(_('équipements'), blank=True, help_text=_('Liste des équipements séparés par des virgules'))
    
    # Localisation
    etage = models.CharField(_('étage'), max_length=20, blank=True)
    batiment = models.CharField(_('bâtiment'), max_length=50, blank=True)
    
    # Statut
    is_disponible = models.BooleanField(_('disponible'), default=True)
    is_accessible = models.BooleanField(_('accessible PMR'), default=False)
    
    notes = models.TextField(_('notes'), blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Salle')
        verbose_name_plural = _('Salles')
        ordering = ['batiment', 'etage', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.code})"
