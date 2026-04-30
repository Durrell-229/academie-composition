from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification


@login_required
def notification_list_view(request):
    """Affiche les notifications de l'utilisateur et permet de tout marquer comme lu."""
    if request.method == 'POST' and request.POST.get('mark_all_read'):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, "Toutes les notifications ont été marquées comme lues.")
        return redirect('notification_list')

    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:50]
    return render(request, 'notifications/list.html', {'notifications': notifications})
