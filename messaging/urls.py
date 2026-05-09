from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Conversations
    path('conversations/', views.conversation_list, name='conversation_list'),
    path('conversations/create/', views.conversation_create, name='conversation_create'),
    path('conversations/<uuid:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    
    # Messages
    path('conversations/<uuid:conversation_id>/messages/', views.message_list, name='message_list'),
    path('conversations/<uuid:conversation_id>/messages/send/', views.message_send, name='message_send'),
    
    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<uuid:notification_id>/read/', views.notification_read, name='notification_read'),
    
    # Invitations
    path('invitations/', views.invitation_list, name='invitation_list'),
    path('invitations/<uuid:invitation_id>/accept/', views.invitation_accept, name='invitation_accept'),
    path('invitations/<uuid:invitation_id>/decline/', views.invitation_decline, name='invitation_decline'),
]
