"""
Analytics et rapports avancés
Tableaux de bord et statistiques
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from schools.models import Etablissement, Classe


class TableauBord(models.Model):
    """Configuration des tableaux de bord personnalisés"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tableaux_de_bord')
    nom = models.CharField(_('nom'), max_length=100)
    
    configuration = models.JSONField(_('configuration des widgets'), default=dict)
    is_defaut = models.BooleanField(_('tableau de bord par défaut'), default=False)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Tableau de bord')
        verbose_name_plural = _('Tableaux de bord')
    
    def __str__(self):
        return f"{self.nom} - {self.utilisateur.get_full_name()}"


class IndicateurPerformance(models.Model):
    """Indicateurs clés de performance (KPI)"""
    
    class TypeIndicateur(models.TextChoices):
        TAUX_REUSSITE = 'taux_reussite', _('Taux de réussite')
        MOYENNE_GENERALE = 'moyenne_generale', _('Moyenne générale')
        TAUX_PRESENCE = 'taux_presence', _('Taux de présence')
        TAUX_PAIEMENT = 'taux_paiement', _('Taux de paiement')
        TAUX_ABANDON = 'taux_abandon', _('Taux d\'abandon')
        TAUX_REDDBLEMENT = 'taux_redoublement', _('Taux de redoublement')
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='indicateurs')
    
    nom = models.CharField(_('nom'), max_length=100)
    type_indicateur = models.CharField(_('type'), max_length=30, choices=TypeIndicateur.choices)
    valeur_actuelle = models.DecimalField(_('valeur actuelle'), max_digits=10, decimal_places=2)
    valeur_cible = models.DecimalField(_('valeur cible'), max_digits=10, decimal_places=2)
    
    periode = models.CharField(_('période'), max_length=20)  # 2024-2025-T1
    date_calcul = models.DateTimeField(_('date de calcul'), auto_now=True)
    
    class Meta:
        verbose_name = _('Indicateur')
        verbose_name_plural = _('Indicateurs')
    
    def __str__(self):
        return f"{self.nom} - {self.valeur_actuelle}"


class RapportStatistique(models.Model):
    """Rapports statistiques générés"""
    
    class TypeRapport(models.TextChoices):
        PERFORMANCE_ELEVES = 'performance_eleves', _('Performance des élèves')
        RESULTATS_EXAMENS = 'resultats_examens', _('Résultats des examens')
        ASSIDUITE = 'assiduite', _('Assiduité')
        FINANCIER = 'financier', _('Rapport financier')
        PEDAGOGIQUE = 'pedagogique', _('Rapport pédagogique')
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='rapports_stats')
    
    type_rapport = models.CharField(_('type'), max_length=30, choices=TypeRapport.choices)
    titre = models.CharField(_('titre'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    periode_debut = models.DateField(_('début'))
    periode_fin = models.DateField(_('fin'))
    
    # Données
    donnees = models.JSONField(_('données du rapport'))
    fichier_pdf = models.FileField(_('rapport PDF'), upload_to='analytics/rapports/', blank=True, null=True)
    
    # Génération
    genere_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='rapports_stats_generes')
    date_generation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Rapport statistique')
        verbose_name_plural = _('Rapports statistiques')
        ordering = ['-date_generation']
