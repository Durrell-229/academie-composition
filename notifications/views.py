from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification, EmailQueue
from accounts.models import User


@login_required
def notification_list_view(request):
    """Affiche les notifications de l'utilisateur et permet de tout marquer comme lu."""
    if request.method == 'POST' and request.POST.get('mark_all_read'):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, "Toutes les notifications ont été marquées comme lues.")
        return redirect('notification_list')

    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:50]
    return render(request, 'notifications/list.html', {'notifications': notifications})


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

        # Vérifier que les credentials SMTP sont configurés
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            messages.error(
                request,
                "Email non configuré : EMAIL_HOST_USER et EMAIL_HOST_PASSWORD sont requis. "
                "Configurez-les dans les variables d'environnement Render ou dans .env en local."
            )
            return redirect('dashboard')

        # Limiter à 50 emails par requête pour éviter timeout
        if len(recipient_list) > 50:
            messages.warning(request, f"Envoi limité aux 50 premiers destinataires sur {len(recipient_list)} (limite anti-timeout).")
            recipient_list = recipient_list[:50]

        # Envoyer individuellement via SMTP (un par un pour éviter OOM)
        sent_count = 0
        error_count = 0
        for email_addr in recipient_list:
            try:
                send_mail(
                    subject=subject,
                    message=body_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email_addr],
                    fail_silently=False,
                )
                EmailQueue.objects.create(
                    destinataire=email_addr,
                    sujet=subject,
                    corps_texte=body_text,
                    statut='sent',
                )
                sent_count += 1
            except Exception as e:
                error_count += 1
                EmailQueue.objects.create(
                    destinataire=email_addr,
                    sujet=subject,
                    corps_texte=body_text,
                    statut='error',
                    erreur=str(e),
                )

        if sent_count > 0:
            messages.success(request, f"{sent_count} email(s) envoyé(s). {error_count} erreur(s)." if error_count else f"{sent_count} email(s) envoyé(s) avec succès.")
        else:
            messages.error(request, f"Aucun email envoyé. {error_count} erreur(s).")

        return redirect('dashboard')

    return redirect('dashboard')
