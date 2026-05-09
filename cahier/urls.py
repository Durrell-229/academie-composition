from django.urls import path
from . import views

app_name = 'cahier'

urlpatterns = [
    # Seances de cours
    path('seances/', views.seance_list, name='seance_list'),
    path('seances/create/', views.seance_create, name='seance_create'),
    path('seances/<uuid:seance_id>/', views.seance_detail, name='seance_detail'),
    
    # Devoirs
    path('devoirs/', views.devoir_list, name='devoir_list'),
    path('devoirs/create/', views.devoir_create, name='devoir_create'),
    path('devoirs/<uuid:devoir_id>/', views.devoir_detail, name='devoir_detail'),
    path('devoirs/<uuid:devoir_id>/rendus/', views.rendu_list, name='rendu_list'),
    
    # Lecons
    path('lecons/', views.lecon_list, name='lecon_list'),
    path('lecons/create/', views.lecon_create, name='lecon_create'),
    path('lecons/<uuid:lecon_id>/', views.lecon_detail, name='lecon_detail'),
    
    # Progression
    path('progression/', views.progression_list, name='progression_list'),
    path('progression/<uuid:progression_id>/', views.progression_detail, name='progression_detail'),
]
