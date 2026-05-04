from django.urls import path
from . import views
from .views_sse import notification_stream, unread_count_view

urlpatterns = [
    path('', views.notification_list_view, name='notification_list'),
    path('create/', views.create_notification_view, name='create_notification'),
    path('email/', views.email_compose_view, name='email_compose'),
    # Real-time endpoints
    path('stream/', notification_stream, name='notification_stream'),
    path('unread-count/', unread_count_view, name='notification_unread_count'),
    path('mark-read/<int:notification_id>/', views.mark_notification_read, name='notification_mark_read'),
]
