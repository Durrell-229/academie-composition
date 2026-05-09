"""
Administration pour la messagerie
"""

from django.contrib import admin
from .models import Conversation, ParticipantConversation, Message, NotificationMessage, InvitationConversation, MessageFavori


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_conversation', 'nombre_messages', 'is_actif', 'date_creation']
    list_filter = ['type_conversation', 'is_actif', 'is_archive']
    search_fields = ['titre', 'description']
    readonly_fields = ['id', 'date_creation', 'date_modification']


@admin.register(ParticipantConversation)
class ParticipantConversationAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'conversation', 'is_admin', 'nombre_non_lus', 'date_rejoint']
    list_filter = ['is_admin', 'notifications_actives']
    search_fields = ['utilisateur__last_name', 'conversation__titre']
    readonly_fields = ['id', 'date_rejoint']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['expediteur', 'conversation', 'type_message', 'contenu', 'is_supprime', 'date_envoi']
    list_filter = ['type_message', 'is_supprime', 'is_modifie']
    search_fields = ['contenu', 'expediteur__last_name']
    readonly_fields = ['id', 'date_envoi', 'date_modification']


@admin.register(NotificationMessage)
class NotificationMessageAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'type_notification', 'titre', 'is_lue', 'date_creation']
    list_filter = ['type_notification', 'is_lue', 'is_cliquee']
    search_fields = ['titre', 'contenu', 'utilisateur__last_name']
    readonly_fields = ['id', 'date_creation']


@admin.register(InvitationConversation)
class InvitationConversationAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'conversation', 'invite_par', 'statut', 'date_invitation']
    list_filter = ['statut']
    search_fields = ['utilisateur__last_name', 'invite_par__last_name']
    readonly_fields = ['id', 'date_invitation']


@admin.register(MessageFavori)
class MessageFavoriAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'message', 'note', 'date_ajout']
    search_fields = ['utilisateur__last_name', 'note']
    readonly_fields = ['id', 'date_ajout']
