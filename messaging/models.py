"""
Modèles pour le système de messagerie interne
Permet la communication entre utilisateurs de la plateforme
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User


class Conversation(models.Model):
    """Conversation entre utilisateurs"""
    
    class TypeConversation(models.TextChoices):
        PRIVÉ = 'prive', _('Privé')
        GROUPE = 'groupe', _('Groupe')
        CLASSE = 'classe', _('Classe')
        ADMIN = 'admin', _('Administration')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_conversation = models.CharField(_('type'), max_length=20, choices=TypeConversation.choices, default=TypeConversation.PRIVÉ)
    
    # Informations
    titre = models.CharField(_('titre'), max_length=200, blank=True)
    description = models.TextField(_('description'), blank=True)
    
    # Participants
    participants = models.ManyToManyField(User, related_name='conversations', through='ParticipantConversation')
    administrateurs = models.ManyToManyField(User, related_name='conversations_administrees', blank=True)
    
    # Image
    image = models.ImageField(_('image'), upload_to='conversations/', blank=True, null=True)
    
    # Statistiques
    nombre_messages = models.PositiveIntegerField(_('nombre de messages'), default=0)
    dernier_message = models.ForeignKey('Message', on_delete=models.SET_NULL, null=True, blank=True, related_name='conversation_dernier')
    
    # Statut
    is_actif = models.BooleanField(_('actif'), default=True)
    is_archive = models.BooleanField(_('archivé'), default=False)
    
    # Dates
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)
    
    class Meta:
        verbose_name = _('Conversation')
        verbose_name_plural = _('Conversations')
        ordering = ['-date_modification']
    
    def __str__(self):
        return self.titre or f"Conversation {self.id}"


class ParticipantConversation(models.Model):
    """Participant à une conversation"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Statut
    is_admin = models.BooleanField(_('administrateur'), default=False)
    is_muet = models.BooleanField(_('muet'), default=False)
    
    # Notifications
    notifications_actives = models.BooleanField(_('notifications actives'), default=True)
    nombre_non_lus = models.PositiveIntegerField(_('messages non lus'), default=0)
    
    # Dates
    date_rejoint = models.DateTimeField(_('date de participation'), auto_now_add=True)
    date_dernier_message_lu = models.DateTimeField(_('dernier message lu'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Participant')
        verbose_name_plural = _('Participants')
        unique_together = ['conversation', 'utilisateur']
    
    def __str__(self):
        return f"{self.utilisateur.get_full_name()} - {self.conversation.titre}"


class Message(models.Model):
    """Message dans une conversation"""
    
    class TypeMessage(models.TextChoices):
        TEXTE = 'texte', _('Texte')
        IMAGE = 'image', _('Image')
        FICHIER = 'fichier', _('Fichier')
        AUDIO = 'audio', _('Audio')
        VIDEO = 'video', _('Vidéo')
        LIEN = 'lien', _('Lien')
        LOCALISATION = 'localisation', _('Localisation')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    expediteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_envoyes')
    
    # Contenu
    type_message = models.CharField(_('type'), max_length=20, choices=TypeMessage.choices, default=TypeMessage.TEXTE)
    contenu = models.TextField(_('contenu'))
    
    # Fichiers
    fichier = models.FileField(_('fichier'), upload_to='messages/fichiers/', blank=True, null=True)
    miniature = models.ImageField(_('miniature'), upload_to='messages/miniatures/', blank=True, null=True)
    
    # Métadonnées
    nom_fichier = models.CharField(_('nom du fichier'), max_length=255, blank=True)
    taille_fichier = models.PositiveIntegerField(_('taille du fichier (octets)'), null=True, blank=True)
    
    # Statut
    is_supprime = models.BooleanField(_('supprimé'), default=False)
    is_modifie = models.BooleanField(_('modifié'), default=False)
    
    # Réponse
    message_parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reponses')
    
    # Réactions
    reactions = models.JSONField(_('réactions'), blank=True, null=True, default=dict)
    
    # Lecture
    utilisateurs_lus = models.ManyToManyField(User, related_name='messages_lus', blank=True)
    
    # Dates
    date_envoi = models.DateTimeField(_('date d\'envoi'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)
    
    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['date_envoi']
    
    def __str__(self):
        return f"{self.expediteur.get_full_name()}: {self.contenu[:50]}"


class NotificationMessage(models.Model):
    """Notifications pour les messages"""
    
    class TypeNotification(models.TextChoices):
        NOUVEAU_MESSAGE = 'nouveau_message', _('Nouveau message')
        MENTION = 'mention', _('Mention')
        REACTION = 'reaction', _('Réaction')
        AJOUT_GROUPE = 'ajout_groupe', _('Ajout au groupe')
        INVITATION = 'invitation', _('Invitation')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_messages')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='notifications')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    type_notification = models.CharField(_('type'), max_length=20, choices=TypeNotification.choices)
    titre = models.CharField(_('titre'), max_length=200)
    contenu = models.TextField(_('contenu'))
    
    # Statut
    is_lue = models.BooleanField(_('lue'), default=False)
    is_cliquee = models.BooleanField(_('cliquée'), default=False)
    
    # Dates
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_lecture = models.DateTimeField(_('date de lecture'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Notification de message')
        verbose_name_plural = _('Notifications de messages')
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.utilisateur.get_full_name()} - {self.titre}"


class InvitationConversation(models.Model):
    """Invitation à rejoindre une conversation"""
    
    class StatutInvitation(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        ACCEPTEE = 'acceptee', _('Acceptée')
        REFUSEE = 'refusee', _('Refusée')
        EXPIREE = 'expiree', _('Expirée')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='invitations')
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations_recues')
    invite_par = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations_envoyees')
    
    message = models.TextField(_('message d\'invitation'), blank=True)
    statut = models.CharField(_('statut'), max_length=20, choices=StatutInvitation.choices, default=StatutInvitation.EN_ATTENTE)
    
    date_invitation = models.DateTimeField(_('date d\'invitation'), auto_now_add=True)
    date_reponse = models.DateTimeField(_('date de réponse'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Invitation')
        verbose_name_plural = _('Invitations')
        unique_together = ['conversation', 'utilisateur']
    
    def __str__(self):
        return f"Invitation de {self.invite_par.get_full_name()} à {self.utilisateur.get_full_name()}"


class MessageFavori(models.Model):
    """Messages favoris"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_favoris')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='favoris')
    
    note = models.TextField(_('note personnelle'), blank=True)
    
    date_ajout = models.DateTimeField(_('date d\'ajout'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Message favori')
        verbose_name_plural = _('Messages favoris')
        unique_together = ['utilisateur', 'message']
    
    def __str__(self):
        return f"Favori de {self.utilisateur.get_full_name()}"
