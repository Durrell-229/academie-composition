from django.urls import path
from . import views

urlpatterns = [
    path('room/<str:exam_id>/', views.composition_room_view, name='composition_room'),
    path('submit-paper/<str:session_id>/', views.submit_paper_view, name='submit_paper'),
    path('result/<str:session_id>/', views.result_view, name='result_detail'),
    path('ia-corrections/', views.ia_corrections_list_view, name='ia_corrections_list'),
    path('api/log-cheat/', views.log_cheat_event, name='log_cheat'),
    path('api/upload-screenshot/', views.upload_screenshot, name='upload_screenshot'),
    # Endpoint public pour téléchargement bulletin via QR
    path('bulletin/<uuid:resultat_id>/download/', views.download_composition_bulletin, name='bulletin_download'),
]
