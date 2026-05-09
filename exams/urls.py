from django.urls import path
from . import views

urlpatterns = [
    path('', views.exam_list_view, name='exam_list'),
    path('create/', views.exam_create_view, name='exam_create'),
    path('file/<uuid:file_id>/download/', views.download_exam_file, name='download_exam_file'),
    
    # Validation admin
    path('<str:exam_id>/approve/', views.exam_approve_view, name='exam_approve'),
    path('<str:exam_id>/reject/', views.exam_reject_view, name='exam_reject'),
    path('<str:exam_id>/publish/', views.exam_publish_view, name='exam_publish'),
    
    path('<str:exam_id>/', views.exam_detail_view, name='exam_detail'),
]
