from django.urls import path
from . import views

urlpatterns = [
    # Admin
    path('', views.devoir_list_view, name='devoir_list'),
    path('create/', views.devoir_create_view, name='devoir_create'),
    path('<uuid:pk>/', views.devoir_detail_view, name='devoir_detail'),
    path('<uuid:pk>/publish/', views.devoir_publish_view, name='devoir_publish'),
    path('<uuid:pk>/start/', views.devoir_start_view, name='devoir_start'),
    path('<uuid:pk>/end/', views.devoir_end_view, name='devoir_end'),
    path('<uuid:pk>/certificates/', views.devoir_certificates_view, name='devoir_certificates'),
    path('<uuid:pk>/generate-certificates/', views.devoir_generate_certificates_view, name='devoir_generate_certificates'),

    # Prof: submit exam
    path('<uuid:devoir_id>/submit/<uuid:matiere_id>/', views.devoir_submit_epreuve_view, name='devoir_submit_epreuve'),

    # Admin: validate/reject
    path('matiere/<uuid:pk>/validate/', views.devoir_matiere_validate_view, name='devoir_matiere_validate'),
    path('matiere/<uuid:pk>/reject/', views.devoir_matiere_reject_view, name='devoir_matiere_reject'),

    # Eleve: programme + compose
    path('programme/', views.eleve_programme_view, name='eleve_programme'),
    path('programme/<uuid:devoir_id>/', views.eleve_compose_view, name='eleve_compose'),
    path('programme/<uuid:devoir_id>/submit/', views.eleve_submit_reponse_view, name='eleve_submit_reponse'),
    path('resultats/', views.eleve_resultats_view, name='eleve_resultats'),

    # Certificate download
    path('certificat/<uuid:pk>/download/', views.certificat_download_view, name='certificat_download'),
]
