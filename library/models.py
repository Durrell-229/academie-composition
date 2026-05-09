"""
Bibliothèque numérique
Gestion des ressources éducatives
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from schools.models import Etablissement
from core.models import Matiere


class CategorieDocument(models.Model):
    """Catégories de documents"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='categories_documents')
    
    nom = models.CharField(_('nom'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    code_couleur = models.CharField(_('couleur'), max_length=7, default='#3b82f6')
    
    is_actif = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('Catégorie')
        verbose_name_plural = _('Catégories')
    
    def __str__(self):
        return self.nom


class Document(models.Model):
    """Documents de la bibliothèque"""
    
    class TypeDocument(models.TextChoices):
        LIVRE = 'livre', _('Livre')
        ARTICLE = 'article', _('Article scientifique')
        COURS = 'cours', _('Support de cours')
        EXERCICE = 'exercice', _('Exercices corrigés')
        EXAMEN = 'examen', _('Sujet d\'examen')
        VIDEO = 'video', _('Vidéo éducative')
        AUDIO = 'audio', _('Audio / Podcast')
        PRESENTATION = 'presentation', _('Présentation')
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='documents')
    categorie = models.ForeignKey(CategorieDocument, on_delete=models.CASCADE, related_name='documents')
    matiere = models.ForeignKey(Matiere, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    
    titre = models.CharField(_('titre'), max_length=200)
    auteur = models.CharField(_('auteur'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    type_document = models.CharField(_('type'), max_length=20, choices=TypeDocument.choices)
    fichier = models.FileField(_('fichier'), upload_to='library/documents/')
    couverture = models.ImageField(_('couverture'), upload_to='library/couvertures/', blank=True, null=True)
    
    # Métadonnées
    nombre_pages = models.PositiveIntegerField(_('nombre de pages'), null=True, blank=True)
    langue = models.CharField(_('langue'), max_length=10, default='fr')
    mots_cles = models.JSONField(_('mots-clés'), blank=True, null=True)
    
    # Accès
    is_public = models.BooleanField(_('accès public'), default=True)
    classes_autorisees = models.ManyToManyField('schools.Classe', related_name='documents_autorises', blank=True)
    
    # Statistiques
    nombre_lectures = models.PositiveIntegerField(_('lectures'), default=0)
    nombre_telechargements = models.PositiveIntegerField(_('téléchargements'), default=0)
    note_moyenne = models.DecimalField(_('note moyenne'), max_digits=3, decimal_places=2, default=0)
    
    # Upload
    upload_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='documents_uploades')
    date_upload = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = ['-date_upload']
    
    def __str__(self):
        return self.titre


class Emprunt(models.Model):
    """Emprunts de documents (pour livres physiques aussi)"""
    
    class StatutEmprunt(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        EN_COURS = 'en_cours', _('En cours')
        RENDU = 'rendu', _('Rendu')
        EN_RETARD = 'en_retard', _('En retard')
        PERDU = 'perdu', _('Perdu')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='emprunts')
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emprunts', limit_choices_to={'role': 'eleve'})
    
    date_emprunt = models.DateField(_('date d\'emprunt'))
    date_retour_prevu = models.DateField(_('date de retour prévue'))
    date_retour_effectif = models.DateField(_('date de retour effectif'), null=True, blank=True)
    
    statut = models.CharField(_('statut'), max_length=20, choices=StatutEmprunt.choices, default=StatutEmprunt.EN_COURS)
    
    # Pénalités
    amende = models.DecimalField(_('amende (XOF)'), max_digits=10, decimal_places=0, default=0)
    notes = models.TextField(_('notes'), blank=True)
    
    class Meta:
        verbose_name = _('Emprunt')
        verbose_name_plural = _('Emprunts')
        ordering = ['-date_emprunt']
