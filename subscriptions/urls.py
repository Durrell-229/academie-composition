from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('plans/', views.plan_list_view, name='plan_list'),
    path('subscribe/<uuid:plan_id>/', views.subscribe_action, name='subscribe'),
]
