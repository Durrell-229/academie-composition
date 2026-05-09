from django.urls import path
from . import views

app_name = 'realtime'

websocket_urlpatterns = [
    path('ws/dashboard/', views.DashboardConsumer.as_asgi(), name='dashboard_ws'),
    path('ws/global-stats/', views.GlobalStatsConsumer.as_asgi(), name='global_stats_ws'),
]

urlpatterns = [
    path('dashboard/', views.realtime_dashboard, name='dashboard'),
    path('exam/<int:exam_id>/status/', views.exam_room_status, name='exam_status'),
    path('notifications/', views.realtime_notifications, name='notifications'),
    path('bulletins/', views.realtime_bulletins, name='bulletins'),
]
