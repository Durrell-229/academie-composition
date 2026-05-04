from django.urls import path
from . import views

urlpatterns = [
    path('', views.exam_list_view, name='exam_list'),
    path('create/', views.exam_create_view, name='exam_create'),
    path('file/<uuid:file_id>/download/', views.download_exam_file, name='download_exam_file'),
    path('<str:exam_id>/', views.exam_detail_view, name='exam_detail'),
]
