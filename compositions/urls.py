from django.urls import path
from . import views

urlpatterns = [
    path('room/<uuid:exam_id>/', views.composition_room_view, name='composition_room'),
    path('submit-paper/<uuid:session_id>/', views.submit_paper_view, name='submit_paper'),
    path('result/<uuid:session_id>/', views.result_view, name='result_detail'),
    path('ia-corrections/', views.ia_corrections_list_view, name='ia_corrections_list'),
    path('api/log-cheat/', views.log_cheat_event, name='log_cheat'),
    path('api/upload-screenshot/', views.upload_screenshot, name='upload_screenshot'),
    path('api/nemotron-analyze/', views.nemotron_analyze_screenshot, name='nemotron_analyze'),
    path('api/submit-from-room/', views.submit_from_room, name='submit_from_room'),
    # Endpoint public pour téléchargement bulletin via QR
    path('bulletin/<uuid:resultat_id>/download/', views.download_composition_bulletin, name='bulletin_download'),
    # Vue protégée pour servir les fichiers d'examen (bloque les corrigés types aux élèves)
    path('file/<uuid:file_id>/', views.serve_exam_file, name='serve_exam_file'),
]
