"""
Vues pour la messagerie
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Conversation, ParticipantConversation, Message, NotificationMessage, InvitationConversation


@login_required
def conversation_list(request):
    """Liste des conversations de l'utilisateur"""
    query = request.GET.get('q', '')
    
    # Récupérer les conversations où l'utilisateur est participant
    participant = ParticipantConversation.objects.filter(
        utilisateur=request.user,
        conversation__is_actif=True
    ).select_related('conversation')
    
    conversations = [p.conversation for p in participant]
    
    if query:
        conversations = [c for c in conversations if query.lower() in c.titre.lower()]
    
    context = {
        'conversations': conversations,
        'query': query,
    }
    return render(request, 'messaging/conversation_list.html', context)


@login_required
def conversation_create(request):
    """Création d'une nouvelle conversation"""
    if request.method == 'POST':
        # Logique de création
        messages.success(request, "La conversation a été créée.")
        return redirect('messaging:conversation_list')
    
    return render(request, 'messaging/conversation_form.html', {'title': 'Nouvelle conversation'})


@login_required
def conversation_detail(request, conversation_id):
    """Détail d'une conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id, is_actif=True)
    
    # Vérifier que l'utilisateur est participant
    try:
        participant = ParticipantConversation.objects.get(
            conversation=conversation,
            utilisateur=request.user
        )
        # Réinitialiser les notifications
        participant.nombre_non_lus = 0
        participant.save()
    except ParticipantConversation.DoesNotExist:
        messages.error(request, "Vous n'êtes pas autorisé à accéder à cette conversation.")
        return redirect('messaging:conversation_list')
    
    context = {
        'conversation': conversation,
        'participant': participant,
    }
    return render(request, 'messaging/conversation_detail.html', context)


@login_required
def message_list(request, conversation_id):
    """Liste des messages d'une conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id, is_actif=True)
    
    messages_list = Message.objects.filter(
        conversation=conversation,
        is_supprime=False
    ).select_related('expediteur').order_by('date_envoi')
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
    }
    return render(request, 'messaging/message_list.html', context)


@login_required
def message_send(request, conversation_id):
    """Envoi d'un message"""
    conversation = get_object_or_404(Conversation, id=conversation_id, is_actif=True)
    
    if request.method == 'POST':
        # Logique d'envoi
        messages.success(request, "Message envoyé.")
        return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    
    return render(request, 'messaging/message_form.html', {'conversation': conversation})


@login_required
def notification_list(request):
    """Liste des notifications de l'utilisateur"""
    notifications = NotificationMessage.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'messaging/notification_list.html', context)


@login_required
def notification_read(request, notification_id):
    """Marquer une notification comme lue"""
    notification = get_object_or_404(NotificationMessage, id=notification_id, utilisateur=request.user)
    notification.is_lue = True
    notification.save()
    
    return redirect('messaging:notification_list')


@login_required
def invitation_list(request):
    """Liste des invitations de l'utilisateur"""
    invitations = InvitationConversation.objects.filter(
        utilisateur=request.user,
        statut='en_attente'
    ).select_related('conversation', 'invite_par')
    
    context = {
        'invitations': invitations,
    }
    return render(request, 'messaging/invitation_list.html', context)


@login_required
def invitation_accept(request, invitation_id):
    """Accepter une invitation"""
    invitation = get_object_or_404(InvitationConversation, id=invitation_id, utilisateur=request.user)
    invitation.statut = 'acceptee'
    invitation.save()
    
    # Ajouter l'utilisateur à la conversation
    ParticipantConversation.objects.create(
        conversation=invitation.conversation,
        utilisateur=request.user
    )
    
    messages.success(request, "Invitation acceptée.")
    return redirect('messaging:conversation_detail', conversation_id=invitation.conversation.id)


@login_required
def invitation_decline(request, invitation_id):
    """Refuser une invitation"""
    invitation = get_object_or_404(InvitationConversation, id=invitation_id, utilisateur=request.user)
    invitation.statut = 'refusee'
    invitation.save()
    
    messages.success(request, "Invitation refusée.")
    return redirect('messaging:invitation_list')
