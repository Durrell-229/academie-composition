from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    # Promotions
    path('promotions/', views.promotion_list, name='promotion_list'),
    path('promotions/create/', views.promotion_create, name='promotion_create'),
    path('promotions/<uuid:promotion_id>/', views.promotion_detail, name='promotion_detail'),
    
    # Inscriptions
    path('inscriptions/', views.inscription_list, name='inscription_list'),
    path('inscriptions/create/', views.inscription_create, name='inscription_create'),
    path('inscriptions/<uuid:inscription_id>/', views.inscription_detail, name='inscription_detail'),
    path('inscriptions/<uuid:inscription_id>/edit/', views.inscription_update, name='inscription_update'),
    
    # Matières par classe
    path('classes/<uuid:classe_id>/matieres/', views.matiere_classe_list, name='matiere_classe_list'),
    path('classes/<uuid:classe_id>/matieres/create/', views.matiere_classe_create, name='matiere_classe_create'),
    
    # Évaluations
    path('evaluations/', views.evaluation_list, name='evaluation_list'),
    path('evaluations/create/', views.evaluation_create, name='evaluation_create'),
    path('evaluations/<uuid:evaluation_id>/', views.evaluation_detail, name='evaluation_detail'),
    path('evaluations/<uuid:evaluation_id>/notes/', views.evaluation_notes, name='evaluation_notes'),
    
    # Bulletins
    path('bulletins/', views.bulletin_list, name='bulletin_list'),
    path('bulletins/<uuid:bulletin_id>/', views.bulletin_detail, name='bulletin_detail'),
    path('bulletins/generate/', views.bulletin_generate, name='bulletin_generate'),
    
    # Discipline
    path('discipline/', views.discipline_list, name='discipline_list'),
    path('discipline/create/', views.discipline_create, name='discipline_create'),
]
