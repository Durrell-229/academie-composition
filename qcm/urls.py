from django.urls import path, include
from . import views, urls_benin

urlpatterns = [
    path('', include(urls_benin)),

    path('start/', views.start_qcm, name='qcm_start'),
    path('take/', views.take_qcm, name='qcm_take'),
    path('submit/', views.submit_qcm, name='qcm_submit'),
    path('bulletin/<uuid:resultat_id>/', views.download_qcm_bulletin, name='qcm_bulletin_download'),
]
