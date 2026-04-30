from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.start_qcm, name='qcm_start'),
    path('take/', views.take_qcm, name='qcm_take'),
    path('submit/', views.submit_qcm, name='qcm_submit'),
]
