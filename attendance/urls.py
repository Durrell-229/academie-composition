from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Présences
    path('presences/', views.presence_list, name='presence_list'),
    path('presences/create/', views.presence_create, name='presence_create'),
    path('presences/<uuid:presence_id>/', views.presence_detail, name='presence_detail'),
    
    # Absences
    path('absences/', views.absence_list, name='absence_list'),
    path('absences/create/', views.absence_create, name='absence_create'),
    path('absences/<uuid:absence_id>/', views.absence_detail, name='absence_detail'),
    
    # Retards
    path('retards/', views.retard_list, name='retard_list'),
    path('retards/create/', views.retard_create, name='retard_create'),
    
    # Rapports
    path('rapports/', views.rapport_list, name='rapport_list'),
    path('rapports/generate/', views.rapport_generate, name='rapport_generate'),
    
    # Calendrier présence
    path('calendrier/', views.calendrier_presence, name='calendrier_presence'),
]
