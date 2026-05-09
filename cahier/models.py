"""
Modèles pour le cahier de texte numérique
Permet aux professeurs de gérer leurs cours, devoirs et leçons
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from schools.models import Etablissement, Classe
from core.models import Matiere


class SeanceCours(models.Model):
    """Séance de cours dans le cahier de texte"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='seances_cours')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='seances_cours')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='seances_cours')
    professeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seances_cours', limit_choices_to={'role': 'professeur'})
    
    # Informations de la séance
    date = models.DateField(_('date'))
    heure_debut = models.TimeField(_('heure de début'))
    heure_fin = models.TimeField(_('heure de fin'))
    salle = models.CharField(_('salle'), max_length=50, blank=True)
    
    # Contenu du cours
    titre = models.CharField(_('titre'), max_length=200)
    contenu = models.TextField(_('contenu du cours'))
    competences = models.TextField(_('compétences visées'), blank=True)
    objectifs = models.TextField(_('objectifs pédagogiques'), blank=True)
    
    # Déroulement
    activites = models.TextField(_('activités réalisées'), blank=True)
    materiel_utilise = models.TextField(_('matériel utilisé'), blank=True)
    observations = models.TextField(_('observations'), blank=True)
    
    # Pièces jointes
    documents = models.FileField(_('documents'), upload_to='cahier/documents/', blank=True, null=True)
    
    # Statut
    is_effectue = models.BooleanField(_('séance effectuée'), default=False)
    date_saisie = models.DateTimeField(_('date de saisie'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)
    
    class Meta:
        verbose_name = _('Séance de cours')
        verbose_name_plural = _('Séances de cours')
        ordering = ['-date', '-heure_debut']
    
    def __str__(self):
        return f"{self.titre} - {self.classe.nom} ({self.date})"


class Devoir(models.Model):
    """Devoir ou exercice à faire"""
    
    class TypeDevoir(models.TextChoices):
        EXERCICE = 'exercice', _('Exercice')
        TD = 'td', _('Travail dirigé')
        TP = 'tp', _('Travail pratique')
        PROJET = 'projet', _('Projet')
        REDACTION = 'redaction', _('Rédaction')
        MEMOIRE = 'memoire', _('Mémoire')
        REVISION = 'revision', _('Révision')
        AUTRE = 'autre', _('Autre')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='devoirs')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='devoirs')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='devoirs_cahier')
    professeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devoirs', limit_choices_to={'role': 'professeur'})
    
    # Informations du devoir
    titre = models.CharField(_('titre'), max_length=200)
    type_devoir = models.CharField(_('type de devoir'), max_length=20, choices=TypeDevoir.choices)
    description = models.TextField(_('description'))
    consignes = models.TextField(_('consignes'), blank=True)
    
    # Dates
    date_attribution = models.DateField(_('date d\'attribution'))
    date_rendu = models.DateField(_('date de rendu'))
    heure_rendu = models.TimeField(_('heure de rendu'), null=True, blank=True)
    
    # Barème et évaluation
    note_maximale = models.DecimalField(_('note maximale'), max_digits=5, decimal_places=2, default=20.00)
    coefficient = models.DecimalField(_('coefficient'), max_digits=5, decimal_places=2, default=1.00)
    
    # Pièces jointes
    documents = models.FileField(_('documents'), upload_to='cahier/devoirs/', blank=True, null=True)
    
    # Options
    est_notifie = models.BooleanField(_('notifié aux élèves'), default=False)
    est_evaluable = models.BooleanField(_('évaluable'), default=True)
    est_visible = models.BooleanField(_('visible'), default=True)
    
    # Statistiques
    nombre_rendus = models.PositiveIntegerField(_('nombre de rendus'), default=0)
    nombre_non_rendus = models.PositiveIntegerField(_('nombre de non-rendus'), default=0)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Devoir')
        verbose_name_plural = _('Devoirs')
        ordering = ['-date_attribution', 'titre']
    
    def __str__(self):
        return f"{self.titre} - {self.classe.nom} ({self.date_rendu})"


class Lecon(models.Model):
    """Leçon ou chapitre du programme"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='lecons')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='lecons')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='lecons')
    professeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lecons', limit_choices_to={'role': 'professeur'})
    
    # Organisation
    numero = models.PositiveIntegerField(_('numéro de leçon'))
    titre = models.CharField(_('titre'), max_length=200)
    chapitre = models.CharField(_('chapitre'), max_length=200, blank=True)
    
    # Contenu
    contenu = models.TextField(_('contenu'))
    resume = models.TextField(_('résumé'), blank=True)
    points_cles = models.TextField(_('points clés'), blank=True)
    questions_importantes = models.TextField(_('questions importantes'), blank=True)
    
    # Durée
    duree_estimee = models.PositiveIntegerField(_('durée estimée (heures)'), default=2)
    
    # Documents
    support_cours = models.FileField(_('support de cours'), upload_to='cahier/lecons/', blank=True, null=True)
    documents_complementaires = models.JSONField(_('documents complémentaires'), blank=True, null=True)
    
    # Statut
    is_realise = models.BooleanField(_('réalisé'), default=False)
    date_realisation = models.DateField(_('date de réalisation'), null=True, blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Leçon')
        verbose_name_plural = _('Leçons')
        ordering = ['classe', 'matiere', 'numero']
    
    def __str__(self):
        return f"Leçon {self.numero}: {self.titre} - {self.classe.nom}"


class RenduDevoir(models.Model):
    """Rendu d'un devoir par un élève"""
    
    class StatutRendu(models.TextChoices):
        RENDU = 'rendu', _('Rendu')
        NON_RENDU = 'non_rendu', _('Non rendu')
        EN_RETARD = 'en_retard', _('En retard')
        EXCUSE = 'excuse', _('Excusé')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='rendus')
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rendus_devoirs', limit_choices_to={'role': 'eleve'})
    
    # Rendu
    date_rendu = models.DateTimeField(_('date de rendu'), null=True, blank=True)
    statut = models.CharField(_('statut'), max_length=20, choices=StatutRendu.choices, default=StatutRendu.NON_RENDU)
    
    # Contenu
    contenu = models.TextField(_('contenu'), blank=True)
    documents = models.FileField(_('documents rendus'), upload_to='cahier/rendus/', blank=True, null=True)
    commentaire_eleve = models.TextField(_('commentaire de l\'élève'), blank=True)
    
    # Évaluation
    note = models.DecimalField(_('note'), max_digits=5, decimal_places=2, null=True, blank=True)
    appreciation = models.TextField(_('appréciation'), blank=True)
    commentaire_professeur = models.TextField(_('commentaire du professeur'), blank=True)
    date_correction = models.DateTimeField(_('date de correction'), null=True, blank=True)
    
    # Validations
    est_corrige = models.BooleanField(_('corrigé'), default=False)
    est_visible_eleve = models.BooleanField(_('visible à l\'élève'), default=False)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Rendu de devoir')
        verbose_name_plural = _('Rendus de devoirs')
        unique_together = ['devoir', 'eleve']
        ordering = ['-date_rendu']
    
    def __str__(self):
        return f"{self.eleve.get_full_name()} - {self.devoir.titre}"


class Progression(models.Model):
    """Progression du programme par classe/matière"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='progressions')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='progressions')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='progressions')
    professeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progressions', limit_choices_to={'role': 'professeur'})
    
    # Informations
    annee_scolaire = models.CharField(_('année scolaire'), max_length=9, default='2024-2025')
    trimestre = models.CharField(_('trimestre/semestre'), max_length=20, default='Trimestre 1')
    
    # Progression
    nombre_lecons_totales = models.PositiveIntegerField(_('nombre total de leçons'), default=0)
    nombre_lecons_realisees = models.PositiveIntegerField(_('nombre de leçons réalisées'), default=0)
    pourcentage_avancement = models.DecimalField(_('pourcentage d\'avancement'), max_digits=5, decimal_places=2, default=0.00)
    
    # Observations
    observations = models.TextField(_('observations'), blank=True)
    difficultes_rencontrees = models.TextField(_('difficultés rencontrées'), blank=True)
    actions_correctives = models.TextField(_('actions correctives'), blank=True)
    
    # Validation
    date_validation = models.DateField(_('date de validation'), null=True, blank=True)
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='progressions_validees')
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Progression')
        verbose_name_plural = _('Progressions')
        unique_together = ['classe', 'matiere', 'trimestre', 'annee_scolaire']
        ordering = ['-annee_scolaire', 'trimestre']
    
    def __str__(self):
        return f"Progression {self.matiere.nom} - {self.classe.nom} ({self.trimestre})"
    
    def save(self, *args, **kwargs):
        if self.nombre_lecons_totales > 0:
            self.pourcentage_avancement = (self.nombre_lecons_realisees / self.nombre_lecons_totales) * 100
        super().save(*args, **kwargs)
