from django.urls import path, include
from . import views, urls_benin

urlpatterns = [
    path('', include(urls_benin)),

    # Élève (protégé par abonnement pro)
    path('start/', views.start_qcm, name='qcm_start'),
    path('take/', views.take_qcm, name='qcm_take'),
    path('submit/', views.submit_qcm, name='qcm_submit'),
    path('bulletin/<uuid:resultat_id>/', views.download_qcm_bulletin, name='qcm_bulletin_download'),
    path('abonnement-requis/', views.qcm_paywall, name='qcm_paywall'),

    # Professeur — gestion des QCM
    path('prof/', views.prof_liste_qcm, name='qcm_prof_liste'),
    path('prof/creer/', views.prof_creer_qcm, name='qcm_prof_creer'),
    path('prof/upload/', views.prof_upload_qcm, name='qcm_prof_upload'),
    path('prof/<uuid:question_id>/editer/', views.prof_editer_qcm, name='qcm_prof_editer'),
    path('prof/<uuid:question_id>/supprimer/', views.prof_supprimer_qcm, name='qcm_prof_supprimer'),
]
