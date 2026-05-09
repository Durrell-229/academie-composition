"""
Formulaires pour la messagerie
"""

from django import forms
from .models import Conversation, Message, ParticipantConversation


class ConversationForm(forms.ModelForm):
    """Formulaire pour créer/modifier une conversation"""
    
    class Meta:
        model = Conversation
        fields = ['type_conversation', 'titre', 'description', 'image', 'is_actif']
        widgets = {
            'type_conversation': forms.Select(attrs={'class': 'form-control'}),
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MessageForm(forms.ModelForm):
    """Formulaire pour envoyer un message"""
    
    class Meta:
        model = Message
        fields = ['type_message', 'contenu', 'fichier', 'message_parent']
        widgets = {
            'type_message': forms.Select(attrs={'class': 'form-control'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
            'message_parent': forms.HiddenInput(),
        }


class ParticipantForm(forms.ModelForm):
    """Formulaire pour ajouter un participant"""
    
    class Meta:
        model = ParticipantConversation
        fields = ['utilisateur', 'is_admin', 'notifications_actives']
        widgets = {
            'utilisateur': forms.Select(attrs={'class': 'form-control'}),
            'is_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notifications_actives': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
