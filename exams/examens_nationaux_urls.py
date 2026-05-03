from django.urls import path
from . import examens_nationaux_views as views

app_name = 'examens_nationaux'

urlpatterns = [
    path('', views.examen_list_view, name='list'),
    path('<uuid:examen_id>/', views.examen_detail_view, name='detail'),
    path('<uuid:examen_id>/bulletin/', views.generate_examen_bulletin, name='bulletin'),
    path('bulletin/<uuid:composition_id>/download/', views.download_examen_bulletin, name='bulletin_download'),
]
