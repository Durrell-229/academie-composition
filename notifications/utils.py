from .models import Notification


def send_notification(user, title, message, link=None, type='INSCRIPTION'):
    """Crée une notification en base de données pour un utilisateur."""
    notif = Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        type=type
    )
    # Envoi email asynchrone via Redis si l'utilisateur a un email
    if user.email:
        try:
            from .tasks import send_notification_email
            send_notification_email.delay(str(notif.id))
        except Exception:
            pass  # Email optionnel, ne pas bloquer la notification
    return notif
