from django.urls import path, include
from . import views as correction_views

app_name = 'corrections'

urlpatterns = [
    path('dashboard/', correction_views.correction_dashboard, name='dashboard'),
    path('corrige-types/', correction_views.corrige_types_list, name='corrige_types_list'),
    path('corrige-types/<int:id>/', correction_views.corrige_type_detail, name='corrige_type_detail'),
    path('corrige-types/upload/', correction_views.upload_corrige_type, name='upload_corrige_type'),
    path('baremes/', correction_views.baremes_list, name='baremes_list'),
]
