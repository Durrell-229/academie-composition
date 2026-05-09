from django.urls import path, include
from . import views_benin

app_name = 'qcm_benin'

urlpatterns = [
    path('benin/start/', views_benin.start_qcm_benin, name='start_benin'),
    path('benin/take/<int:session_id>/', views_benin.take_qcm_benin, name='take_benin'),
    path('benin/submit/<int:session_id>/', views_benin.submit_qcm_benin, name='submit_benin'),
]
