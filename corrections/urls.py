from django.urls import path
from . import views as correction_views

app_name = 'corrections'

urlpatterns = [
    path('dashboard/', correction_views.correction_dashboard, name='dashboard'),
    path('corrige-types/', correction_views.corrige_types_list, name='corrige_types_list'),
    path('corrige-types/<uuid:id>/', correction_views.corrige_type_detail, name='corrige_type_detail'),
    path('corrige-types/upload/', correction_views.upload_corrige_type, name='upload_corrige_type'),
    path('baremes/', correction_views.baremes_list, name='baremes_list'),
    path('ai/<uuid:session_id>/trigger/', correction_views.trigger_ai_correction, name='trigger_ai_correction'),
    path('humain/<uuid:session_id>/assigner/', correction_views.assign_human_correction, name='assign_human_correction'),
    path('humain/<uuid:session_id>/corriger/', correction_views.human_correction_form, name='human_correction_form'),
]
