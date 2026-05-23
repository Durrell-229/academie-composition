from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'),
    # Organisation routes kept in DB but removed from interface (plateforme cours en ligne)
    # path('organisations/create/', views.organisation_create, name='organisation_create'),
    # path('organisations/<uuid:pk>/', views.organisation_detail, name='organisation_detail'),
    # path('organisations/<uuid:pk>/membres/', views.organisation_membres, name='organisation_membres'),
]
