from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .nvidia_ocr import nvidia_ocr_service
import logging

logger = logging.getLogger(__name__)

@login_required
def test_ocr(request):
    """Page de test OCR"""
    return render(request, 'ai_engine/test_ocr.html')

@login_required
def upload_for_ocr(request):
    """Upload pour OCR"""
    if request.method == 'POST':
        file = request.FILES.get('file')
        if file:
            result = nvidia_ocr_service.extract_text_from_file(file)
            return JsonResponse(result)
    return JsonResponse({'success': False, 'error': 'No file provided'})
