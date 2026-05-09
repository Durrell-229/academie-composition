"""
Modèles pour la gestion multi-établissements
Permet de gérer plusieurs écoles, campus et établissements physiques
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

class Etablissement(models.Model):
    """Modèle principal pour un établissement scolaire"""
    
    class TypeEtablissement(models.TextChoices):
        PRIMAIRE = 'primaire', _('École Primaire')
        COLLEGE = 'college', _('Collège')
        LYCEE = 'lycee', _('Lycée')
        UNIVERSITE = 'universite', _('Université')
        FORMATION_PRO = 'formation_pro', _('Formation Professionnelle')
        ECOLE_SPECIALE = 'ecole_speciale', _('École Spécialisée')
        GROUPE_SCOLAIRE = 'groupe_scolaire', _('Groupe Scolaire')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(_('nom de l\'établissement'), max_length=200)
    code = models.CharField(_('code établissement'), max_length=20, unique=True)
    type_etablissement = models.CharField(
        _('type d\'établissement'),
        max_length=30,
        choices=TypeEtablissement.choices
    )
    logo = models.ImageField(_('logo'), upload_to='schools/logos/', blank=True, null=True)
    
    # Informations de contact
    adresse = models.TextField(_('adresse'), blank=True)
    ville = models.CharField(_('ville'), max_length=100, blank=True)
    pays = models.CharField(_('pays'), max_length=100, default='Bénin')
    code_postal = models.CharField(_('code postal'), max_length=20, blank=True)
    telephone = models.CharField(_('téléphone'), max_length=20, blank=True)
    email = models.EmailField(_('email'), blank=True)
    site_web = models.URLField(_('site web'), blank=True)
    
    # Coordonnées géographiques
    latitude = models.DecimalField(_('latitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('longitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Informations administratives
    numero_agrement = models.CharField(_('numéro d\'agrément'), max_length=50, blank=True)
    uai = models.CharField(_('code UAI'), max_length=10, blank=True, unique=True, null=True)
    siret = models.CharField(_('numéro SIRET'), max_length=14, blank=True, validators=[
        RegexValidator(r'^\d{14}$', _('Le numéro SIRET doit contenir exactement 14 chiffres'))
    ])
    
    # Capacité et statistiques
    capacite_max = models.PositiveIntegerField(_('capacité maximale'), default=0)
    nombre_eleves = models.PositiveIntegerField(_('nombre d\'élèves actuels'), default=0)
    nombre_professeurs = models.PositiveIntegerField(_('nombre de professeurs'), default=0)
    
    # Configuration
    langue_principale = models.CharField(_('langue principale'), max_length=5, default='fr')
    fuseau_horaire = models.CharField(_('fuseau horaire'), max_length=50, default='Africa/Porto-Novo')
    devise = models.CharField(_('devise'), max_length=10, default='XOF')
    annee_scolaire_courante = models.CharField(_('année scolaire courante'), max_length=9, default='2024-2025')
    
    # Statut
    is_active = models.BooleanField(_('actif'), default=True)
    is_verified = models.BooleanField(_('vérifié'), default=False)
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)
    
    class Meta:
        verbose_name = _('Établissement')
        verbose_name_plural = _('Établissements')
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.code})"
    
    @property
    def nombre_campus(self):
        return self.campus.count()
    
    @property
    def taux_occupation(self):
        if self.capacite_max > 0:
            return round((self.nombre_eleves / self.capacite_max) * 100, 1)
        return 0


class Campus(models.Model):
    """Campus ou site d'un établissement"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='campus')
    nom = models.CharField(_('nom du campus'), max_length=200)
    code = models.CharField(_('code campus'), max_length=20)
    
    # Localisation
    adresse = models.TextField(_('adresse'))
    ville = models.CharField(_('ville'), max_length=100)
    pays = models.CharField(_('pays'), max_length=100, default='Bénin')
    latitude = models.DecimalField(_('latitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('longitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Infrastructure
    superficie = models.DecimalField(_('superficie (m²)'), max_digits=10, decimal_places=2, null=True, blank=True)
    nombre_salles = models.PositiveIntegerField(_('nombre de salles'), default=0)
    nombre_batiments = models.PositiveIntegerField(_('nombre de bâtiments'), default=0)
    
    # Contact campus
    telephone = models.CharField(_('téléphone'), max_length=20, blank=True)
    email = models.EmailField(_('email'), blank=True)
    directeur = models.CharField(_('directeur du campus'), max_length=200, blank=True)
    
    # Statut
    is_principal = models.BooleanField(_('campus principal'), default=False)
    is_active = models.BooleanField(_('actif'), default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Campus')
        verbose_name_plural = _('Campus')
        unique_together = ['etablissement', 'code']
        ordering = ['-is_principal', 'nom']
    
    def __str__(self):
        return f"{self.etablissement.nom} - {self.nom}"


class NiveauScolaire(models.Model):
    """Niveaux scolaires par établissement"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='niveaux')
    nom = models.CharField(_('nom du niveau'), max_length=100)
    code = models.CharField(_('code'), max_length=20)
    ordre = models.PositiveIntegerField(_('ordre'), default=0)
    description = models.TextField(_('description'), blank=True)
    
    # Configuration
    duree_annees = models.PositiveIntegerField(_('durée en années'), default=1)
    age_min = models.PositiveIntegerField(_('âge minimum'), null=True, blank=True)
    age_max = models.PositiveIntegerField(_('âge maximum'), null=True, blank=True)
    
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('Niveau scolaire')
        verbose_name_plural = _('Niveaux scolaires')
        unique_together = ['etablissement', 'code']
        ordering = ['ordre', 'nom']
    
    def __str__(self):
        return f"{self.etablissement.nom} - {self.nom}"


class Classe(models.Model):
    """Classes par niveau et établissement"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='classes')
    campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True, related_name='classes')
    niveau = models.ForeignKey(NiveauScolaire, on_delete=models.CASCADE, related_name='classes')
    
    nom = models.CharField(_('nom de la classe'), max_length=100)  # Ex: 6ème A, CM2, Terminale C
    code = models.CharField(_('code'), max_length=20)
    section = models.CharField(_('section'), max_length=10, blank=True)  # A, B, C, etc.
    
    # Effectif
    capacite_max = models.PositiveIntegerField(_('capacité maximale'), default=40)
    effectif_actuel = models.PositiveIntegerField(_('effectif actuel'), default=0)
    
    # Responsable
    professeur_principal = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes_principales',
        limit_choices_to={'role': 'professeur'}
    )
    
    # Emploi du temps
    emploi_du_temps = models.JSONField(_('emploi du temps'), blank=True, null=True)
    
    # Statut
    is_active = models.BooleanField(_('actif'), default=True)
    annee_scolaire = models.CharField(_('année scolaire'), max_length=9, default='2024-2025')
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Classe')
        verbose_name_plural = _('Classes')
        unique_together = ['etablissement', 'code', 'annee_scolaire']
        ordering = ['niveau__ordre', 'nom']
    
    def __str__(self):
        return f"{self.nom} - {self.annee_scolaire}"
    
    @property
    def places_disponibles(self):
        return max(0, self.capacite_max - self.effectif_actuel)


class AnneeScolaire(models.Model):
    """Années scolaires par établissement"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='annees_scolaires')
    nom = models.CharField(_('nom'), max_length=20)  # Ex: 2024-2025
    code = models.CharField(_('code'), max_length=10, unique=True)
    
    date_debut = models.DateField(_('date de début'))
    date_fin = models.DateField(_('date de fin'))
    
    # Trimestres/Semestres
    nombre_periodes = models.PositiveIntegerField(_('nombre de périodes'), default=3)
    periodes = models.JSONField(_('périodes'), blank=True, null=True)
    
    # Statut
    is_courante = models.BooleanField(_('année courante'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Année scolaire')
        verbose_name_plural = _('Années scolaires')
        unique_together = ['etablissement', 'nom']
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.etablissement.nom} - {self.nom}"


class ConfigurationEtablissement(models.Model):
    """Configuration personnalisée par établissement"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.OneToOneField(Etablissement, on_delete=models.CASCADE, related_name='configuration')
    
    # Configuration académique
    systeme_evaluation = models.CharField(_('système d\'évaluation'), max_length=50, default='20')  # 20, 100, etc.
    note_minimale_reussite = models.DecimalField(_('note minimale de réussite'), max_digits=5, decimal_places=2, default=10.00)
    coefficient_max = models.DecimalField(_('coefficient maximum'), max_digits=5, decimal_places=2, default=10.00)
    
    # Configuration horaire
    heure_debut_cours = models.TimeField(_('heure de début des cours'), default='08:00')
    heure_fin_cours = models.TimeField(_('heure de fin des cours'), default='17:00')
    duree_cours = models.PositiveIntegerField(_('durée d\'un cours (minutes)'), default=55)
    pause_dejeuner = models.TimeField(_('pause déjeuner'), default='12:00')
    duree_pause_dejeuner = models.PositiveIntegerField(_('durée pause déjeuner (minutes)'), default=60)
    
    # Configuration bulletins
    frequence_bulletins = models.CharField(_('fréquence des bulletins'), max_length=20, default='trimestriel')
    delai_publication_bulletins = models.PositiveIntegerField(_('délai publication bulletins (jours)'), default=15)
    
    # Configuration absences
    tolerance_retard = models.PositiveIntegerField(_('tolérance retard (minutes)'), default=15)
    max_absences = models.PositiveIntegerField(_('maximum absences autorisées'), default=10)
    
    # Configuration paiements
    devise = models.CharField(_('devise'), max_length=10, default='XOF')
    frais_inscription = models.DecimalField(_('frais d\'inscription'), max_digits=12, decimal_places=2, default=0)
    mensualites = models.JSONField(_('mensualités'), blank=True, null=True)
    
    # Configuration notifications
    notifications_parents = models.BooleanField(_('notifications aux parents'), default=True)
    notifications_professeurs = models.BooleanField(_('notifications aux professeurs'), default=True)
    notifications_eleves = models.BooleanField(_('notifications aux élèves'), default=True)
    
    # Personnalisation
    couleur_principale = models.CharField(_('couleur principale'), max_length=7, default='#007A5E')
    couleur_secondaire = models.CharField(_('couleur secondaire'), max_length=7, default='#CE1126')
    nom_personnalise_bulletin = models.CharField(_('nom personnalisé bulletin'), max_length=200, blank=True)
    
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Configuration établissement')
        verbose_name_plural = _('Configurations établissements')
    
    def __str__(self):
        return f"Configuration - {self.etablissement.nom}"
