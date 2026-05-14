from django.urls import path
from . import views

app_name = 'bulletins'

urlpatterns = [
    path('', views.index, name='index'),
    # Creation d'un nouveau bulletin
    path('creer/', views.bulletin_creer, name='creer'),
    # Endpoint public verification QR code (avant <uuid:bulletin_id>/)
    path('verify/<uuid:token>/download/', views.verify_and_download, name='verify_download'),
    # Actions sur un bulletin existant
    path('<uuid:bulletin_id>/', views.detail, name='detail'),
    path('<uuid:bulletin_id>/modifier/', views.bulletin_editer, name='editer'),
    path('<uuid:bulletin_id>/generate/', views.generate_bulletin, name='generate'),
    path('<uuid:bulletin_id>/download/', views.download_bulletin_pdf, name='download'),
    path('<uuid:bulletin_id>/preview/', views.preview_bulletin, name='preview'),
    # Format officiel Benin — affichage HTML et PDF
    path('<uuid:bulletin_id>/scolaire/', views.bulletin_scolaire_html, name='scolaire_html'),
    path('<uuid:bulletin_id>/scolaire/pdf/', views.bulletin_scolaire_pdf, name='scolaire_pdf'),
]
