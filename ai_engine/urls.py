from django.urls import path, include
from . import ocr_views

app_name = 'ocr'

urlpatterns = [
    path('test/', ocr_views.test_ocr, name='test'),
    path('upload/', ocr_views.upload_for_ocr, name='upload'),
]
