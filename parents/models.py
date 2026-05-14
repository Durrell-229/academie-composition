"""
Module Parents et Tuteurs
Portail dédié pour les parents d'élèves
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from schools.models import Etablissement, Classe


class Parent(models.Model):
    """Profil parent/tuteur"""
    
    class LienParente(models.TextChoices):
        PERE = 'pere', _('Père')
        MERE = 'mere', _('Mère')
        TUTEUR = 'tuteur', _('Tuteur légal')
        ONCLE = 'oncle', _('Oncle')
        TANTE = 'tante', _('Tante')
        GRAND_PARENT = 'grand_parent', _('Grand-parent')
        AUTRE = 'autre', _('Autre')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_parent', limit_choices_to={'role': 'parent'})
    
    # Informations personnelles
    lien_parente = models.CharField(_('lien de parenté'), max_length=20, choices=LienParente.choices, default=LienParente.PERE)
    profession = models.CharField(_('profession'), max_length=100, blank=True)
    lieu_travail = models.CharField(_('lieu de travail'), max_length=200, blank=True)
    
    # Contact
    telephone_2 = models.CharField(_('téléphone 2'), max_length=20, blank=True)
    email_2 = models.EmailField(_('email 2'), blank=True)
    adresse = models.TextField(_('adresse'), blank=True)
    
    is_actif = models.BooleanField(_('compte actif'), default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Parent')
        verbose_name_plural = _('Parents')
    
    def __str__(self):
        # Utiliser select_related('user') dans les querysets pour éviter le N+1
        return f"{self.user.get_full_name()} ({self.get_lien_parente_display()})"


class Enfant(models.Model):
    """Lien entre parent et élève"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='enfants')
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parents', limit_choices_to={'role': 'eleve'})
    
    is_principal = models.BooleanField(_('tuteur principal'), default=False)
    autorisation_sortie = models.BooleanField(_('autorisation de sortie'), default=True)
    autorisation_medical = models.BooleanField(_('autorisation médicale'), default=True)
    
    class Meta:
        verbose_name = _('Enfant')
        verbose_name_plural = _('Enfants')
        unique_together = ['parent', 'eleve']
    
    def __str__(self):
        # Utiliser select_related('parent__user', 'eleve') dans les querysets pour éviter le N+1
        return f"{self.parent} - {self.eleve.get_full_name()}"


class NotificationParent(models.Model):
    """Notifications pour les parents"""
    
    class TypeNotification(models.TextChoices):
        ABSENCE = 'absence', _('Absence enregistrée')
        RETARD = 'retard', _('Retard signalé')
        NOTE = 'note', _('Nouvelle note')
        BULLETIN = 'bulletin', _('Bulletin disponible')
        PAIMENT = 'paiement', _('Paiement requis')
        EVENEMENT = 'evenement', _('Événement scolaire')
        DISCIPLINE = 'discipline', _('Incident disciplinaire')
        GENERALE = 'generale', _('Information générale')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='notifications')
    eleve = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_parent', limit_choices_to={'role': 'eleve'})
    
    type_notification = models.CharField(_('type'), max_length=20, choices=TypeNotification.choices)
    titre = models.CharField(_('titre'), max_length=200)
    contenu = models.TextField(_('contenu'))
    
    is_lue = models.BooleanField(_('lue'), default=False, db_index=True)
    date_notification = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Notification parent')
        verbose_name_plural = _('Notifications parents')
        ordering = ['-date_notification']
