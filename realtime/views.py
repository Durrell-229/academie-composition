from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import RealtimeNotification
from .services import realtime_service
from .consumers import DashboardConsumer, GlobalStatsConsumer
import logging

logger = logging.getLogger(__name__)

@login_required
def realtime_dashboard(request):
    """Dashboard temps réel"""
    return render(request, 'realtime/dashboard.html')

@login_required
def exam_room_status(request, exam_id):
    """Statut de la salle d'examen"""
    return JsonResponse({
        'exam_id': exam_id,
        'status': 'active',
        'connected_users': 0,
        'time_remaining': 3600
    })

@login_required
def realtime_notifications(request):
    """Page des notifications temps réel"""
    return render(request, 'realtime/notifications.html')

@login_required
def realtime_bulletins(request):
    """Page des bulletins temps réel"""
    return render(request, 'realtime/bulletins.html')
