from django.urls import path
from . import views

app_name = 'certificats'

urlpatterns = [
    # Types de certificats
    path('types/', views.type_certificat_list, name='type_certificat_list'),
    path('types/create/', views.type_certificat_create, name='type_certificat_create'),
    
    # Certificats
    path('', views.certificat_list, name='certificat_list'),
    path('create/', views.certificat_create, name='certificat_create'),
    path('<uuid:certificat_id>/', views.certificat_detail, name='certificat_detail'),
    path('<uuid:certificat_id>/pdf/', views.certificat_pdf, name='certificat_pdf'),
    path('<uuid:certificat_id>/deliver/', views.certificat_deliver, name='certificat_deliver'),
    
    # Vérification
    path('verify/', views.certificat_verify, name='certificat_verify'),
    
    # Examens
    path('examens/', views.examen_list, name='examen_list'),
    path('examens/create/', views.examen_create, name='examen_create'),
    path('examens/<uuid:examen_id>/', views.examen_detail, name='examen_detail'),
    path('examens/<uuid:examen_id>/inscriptions/', views.inscription_list, name='inscription_list'),
    path('examens/<uuid:examen_id>/publish-results/', views.examen_publish_results, name='examen_publish_results'),
    
    # Inscriptions
    path('inscriptions/create/', views.inscription_create, name='inscription_create'),
    path('inscriptions/<uuid:inscription_id>/', views.inscription_detail, name='inscription_detail'),
    
    # Copies physiques (OCR)
    path('copies/', views.copie_list, name='copie_list'),
    path('copies/upload/', views.copie_upload, name='copie_upload'),
    path('copies/<uuid:copie_id>/', views.copie_detail, name='copie_detail'),
    path('copies/<uuid:copie_id>/correct/', views.copie_correct_ia, name='copie_correct_ia'),
    path('copies/<uuid:copie_id>/verify/', views.copie_verify, name='copie_verify'),
]
