from django.urls import path
from . import views

app_name = 'schedule'

urlpatterns = [
    # Emplois du temps
    path('emplois-temps/', views.emploi_du_temps_list, name='emploi_du_temps_list'),
    path('emplois-temps/create/', views.emploi_du_temps_create, name='emploi_du_temps_create'),
    path('emplois-temps/<uuid:emploi_id>/', views.emploi_du_temps_detail, name='emploi_du_temps_detail'),
    path('emplois-temps/<uuid:emploi_id>/edit/', views.emploi_du_temps_edit, name='emploi_du_temps_edit'),
    path('emplois-temps/<uuid:emploi_id>/creneaux/', views.creneau_list, name='creneau_list'),
    
    # Événements
    path('evenements/', views.evenement_list, name='evenement_list'),
    path('evenements/create/', views.evenement_create, name='evenement_create'),
    path('evenements/<uuid:evenement_id>/', views.evenement_detail, name='evenement_detail'),
    
    # Calendrier
    path('calendrier/', views.calendrier_view, name='calendrier'),
    
    # Salles
    path('salles/', views.salle_list, name='salle_list'),
    path('salles/create/', views.salle_create, name='salle_create'),
    
    # Disponibilités
    path('disponibilites/', views.disponibilite_list, name='disponibilite_list'),
]
