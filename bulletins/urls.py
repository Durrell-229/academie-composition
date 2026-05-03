from django.urls import path
from . import views

app_name = 'bulletins'

urlpatterns = [
    path('', views.index, name='index'),
    # Endpoint public pour verification QR code (MUST be before <uuid:bulletin_id>/)
    path('verify/<uuid:token>/download/', views.verify_and_download, name='verify_download'),
    path('<uuid:bulletin_id>/', views.detail, name='detail'),
    path('<uuid:bulletin_id>/generate/', views.generate_bulletin, name='generate'),
    path('<uuid:bulletin_id>/download/', views.download_bulletin_pdf, name='download'),
    path('<uuid:bulletin_id>/preview/', views.preview_bulletin, name='preview'),
]
