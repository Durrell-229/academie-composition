from django.urls import path
from . import views

app_name = 'schools'

urlpatterns = [
    # Établissements
    path('', views.etablissement_list, name='etablissement_list'),
    path('create/', views.etablissement_create, name='etablissement_create'),
    path('<uuid:etablissement_id>/', views.etablissement_detail, name='etablissement_detail'),
    path('<uuid:etablissement_id>/edit/', views.etablissement_update, name='etablissement_update'),
    path('<uuid:etablissement_id>/delete/', views.etablissement_delete, name='etablissement_delete'),
    
    # Campus
    path('<uuid:etablissement_id>/campus/', views.campus_list, name='campus_list'),
    path('<uuid:etablissement_id>/campus/create/', views.campus_create, name='campus_create'),
    path('<uuid:etablissement_id>/campus/<uuid:campus_id>/', views.campus_detail, name='campus_detail'),
    
    # Classes
    path('<uuid:etablissement_id>/classes/', views.classe_list, name='classe_list'),
    path('<uuid:etablissement_id>/classes/create/', views.classe_create, name='classe_create'),
    path('<uuid:etablissement_id>/classes/<uuid:classe_id>/', views.classe_detail, name='classe_detail'),
    
    # Configuration
    path('<uuid:etablissement_id>/configuration/', views.configuration_edit, name='configuration_edit'),
]
