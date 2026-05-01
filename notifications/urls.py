from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list_view, name='notification_list'),
    path('create/', views.create_notification_view, name='create_notification'),
    path('email/', views.email_compose_view, name='email_compose'),
]
