from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Notification, EmailQueue
from accounts.models import User
import requests
import logging

logger = logging.getLogger(__name__)


def _send_resend_email(to_email: str, subject: str, body: str) -> bool:
    """Envoie un email via l'API HTTP Resend (pas de SMTP, pas de timeout)."""
    api_key = getattr(settings, 'RESEND_API_KEY', '') or ''
    if not api_key:
        logger.error("[Resend] API key non configurée")
        return False

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    data = {
        'from': 'Académie Numérique <onboarding@resend.dev>',
        'to': [to_email],
        'subject': subject,
        'html': body.replace('\n', '<br>'),
    }

    try:
        resp = requests.post('https://api.resend.com/emails', headers=headers, json=data, timeout=10)
        if resp.status_code == 200:
            logger.info(f"[Resend] Email envoyé à {to_email}")
            return True
        else:
            logger.error(f"[Resend] Erreur {resp.status_code} pour {to_email}: {resp.text}")
            return False
    except requests.RequestException as e:
        logger.error(f"[Resend] Erreur réseau pour {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"[Resend] Erreur inattendue pour {to_email}: {e}")
        return False


@login_required
def notification_list_view(request):
    """Affiche les notifications de l'utilisateur et permet de tout marquer comme lu."""
    if request.method == 'POST' and request.POST.get('mark_all_read'):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, "Toutes les notifications ont été marquées comme lues.")
        return redirect('notification_list')

    # Récupérer les notifications de l'utilisateur
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:50]
    
    # Compter les non lues
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    return render(request, 'notifications/list.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
def create_notification_view(request):
    """Permet à un admin de créer une notification pour un ou plusieurs utilisateurs."""
    if request.user.role != 'admin':
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        notif_type = request.POST.get('type', 'INSCRIPTION')
        recipient_role = request.POST.get('recipient_role', 'all')

        if not title or not message:
            messages.error(request, "Le titre et le message sont requis.")
            return redirect('dashboard')

        # Déterminer les destinataires
        if recipient_role == 'all':
            recipients = User.objects.filter(is_active=True)
        else:
            recipients = User.objects.filter(role=recipient_role, is_active=True)

        count = 0
        for recipient in recipients:
            Notification.objects.create(
                recipient=recipient,
                title=title,
                message=message,
                type=notif_type,
            )
            count += 1

        messages.success(request, f"Notification envoyée à {count} utilisateur(s).")
        return redirect('dashboard')

    return redirect('dashboard')


@login_required
def email_compose_view(request):
    """Permet à un admin de composer et envoyer un email."""
    if request.user.role != 'admin':
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        body_text = request.POST.get('body_text', '').strip()
        recipient_role = request.POST.get('recipient_role', 'all')

        if not subject or not body_text:
            messages.error(request, "Le sujet et le corps du message sont requis.")
            return redirect('dashboard')

        # Déterminer les destinataires
        if recipient_role == 'all':
            recipients = User.objects.filter(is_active=True).values_list('email', flat=True)
        elif recipient_role == 'custom':
            custom_email = request.POST.get('custom_email', '').strip()
            recipients = [custom_email] if custom_email else []
        else:
            recipients = User.objects.filter(role=recipient_role, is_active=True).values_list('email', flat=True)

        recipient_list = list(recipients)
        if not recipient_list:
            messages.error(request, "Aucun destinataire trouvé.")
            return redirect('dashboard')

        # Vérifier que la clé API Resend est configurée
        resend_api_key = getattr(settings, 'RESEND_API_KEY', '') or ''
        if not resend_api_key:
            messages.error(
                request,
                "Email non configuré : RESEND_API_KEY est requis. "
                "Configurez-le dans les variables d'environnement Render."
            )
            return redirect('dashboard')

        # Limiter à 50 emails par requête pour éviter timeout
        if len(recipient_list) > 50:
            messages.warning(request, f"Envoi limité aux 50 premiers destinataires sur {len(recipient_list)} (limite anti-timeout).")
            recipient_list = recipient_list[:50]

        # Envoyer individuellement via l'API Resend (HTTP, pas SMTP)
        sent_count = 0
        error_count = 0
        for email_addr in recipient_list:
            success = _send_resend_email(email_addr, subject, body_text)
            if success:
                EmailQueue.objects.create(
                    destinataire=email_addr,
                    sujet=subject,
                    corps_texte=body_text,
                    statut='sent',
                )
                sent_count += 1
            else:
                error_count += 1
                EmailQueue.objects.create(
                    destinataire=email_addr,
                    sujet=subject,
                    corps_texte=body_text,
                    statut='error',
                    erreur="Erreur API Resend",
                )

        if sent_count > 0:
            messages.success(request, f"{sent_count} email(s) envoyé(s). {error_count} erreur(s)." if error_count else f"{sent_count} email(s) envoyé(s) avec succès.")
        else:
            messages.error(request, f"Aucun email envoyé. {error_count} erreur(s).")

        return redirect('dashboard')

    return redirect('dashboard')
