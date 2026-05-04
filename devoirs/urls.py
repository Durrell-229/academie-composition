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
    path('<uuid:pk>/coefficients/', views.devoir_set_coefficients_view, name='devoir_set_coefficients'),
    path('<uuid:pk>/bulletins/', views.devoir_bulletins_view, name='devoir_bulletins'),
    path('<uuid:pk>/bulletins/approve-all/', views.devoir_approuver_tous_view, name='devoir_approuver_tous'),
    path('<uuid:pk>/certificates/', views.devoir_certificates_view, name='devoir_certificates'),
    path('<uuid:pk>/generate-certificates/', views.devoir_generate_certificates_view, name='devoir_generate_certificates'),

    # Admin: validate/reject epreuves
    path('validate/', views.admin_validate_all_view, name='admin_validate_all'),
    path('epreuve/<uuid:pk>/download/', views.download_epreuve_file, name='download_epreuve'),
    path('matiere/<uuid:pk>/validate/', views.devoir_matiere_validate_view, name='devoir_matiere_validate'),
    path('matiere/<uuid:pk>/reject/', views.devoir_matiere_reject_view, name='devoir_matiere_reject'),
    path('<uuid:pk>/upload-epreuve/', views.admin_upload_epreuve_view, name='admin_upload_epreuve'),

    # Admin: approve/reject bulletins
    path('bulletin/<uuid:pk>/approve/', views.devoir_approuver_bulletin_view, name='devoir_approuver_bulletin'),
    path('bulletin/<uuid:pk>/reject/', views.devoir_rejeter_bulletin_view, name='devoir_rejeter_bulletin'),

    # Prof: submit exam
    path('prof/', views.prof_dashboard_view, name='prof_dashboard'),
    path('<uuid:devoir_id>/submit/<uuid:matiere_id>/', views.devoir_submit_epreuve_view, name='devoir_submit_epreuve'),

    # Eleve: programme + compose
    path('programme/', views.eleve_programme_view, name='eleve_programme'),
    path('programme/<uuid:devoir_id>/calendar/', views.eleve_devoir_calendar_view, name='eleve_devoir_calendar'),
    path('programme/<uuid:devoir_id>/', views.eleve_compose_view, name='eleve_compose'),
    path('programme/<uuid:devoir_id>/submit/', views.eleve_submit_reponse_view, name='eleve_submit_reponse'),
    path('copie/<uuid:devoir_matiere_id>/', views.eleve_upload_copie_view, name='eleve_upload_copie'),
    path('resultats/', views.eleve_resultats_view, name='eleve_resultats'),
    path('bulletin/<uuid:pk>/download/', views.eleve_download_bulletin_view, name='eleve_download_bulletin'),

    # Certificate download
    path('certificat/<uuid:pk>/download/', views.certificat_download_view, name='certificat_download'),
    
    # Class & Serie Management
    path('classes/', views.classe_list_view, name='classe_list'),
    path('classes/create/', views.classe_create_view, name='classe_create'),
    path('classes/<uuid:pk>/edit/', views.classe_edit_view, name='classe_edit'),
    path('classes/<uuid:pk>/delete/', views.classe_delete_view, name='classe_delete'),
    
    # Schedule Management
    path('<uuid:pk>/schedule/', views.schedule_builder_view, name='schedule_builder'),
    path('<uuid:pk>/schedule/delete/<str:matiere_nom>/', views.schedule_delete_view, name='schedule_delete'),
    
    # Workflow Dashboard
    path('workflow/', views.workflow_dashboard_view, name='workflow_dashboard'),
    
    # IA Lab
    path('ia-lab/', views.ia_lab_dashboard_view, name='ia_lab_dashboard'),
    path('ia-lab/verify/', views.ia_verify_copy_view, name='ia_verify_copy'),
]
