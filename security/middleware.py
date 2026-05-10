from django.conf import settings
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware:
    """
    Middleware pour ajouter les headers de sécurité personnalisés
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Ajouter les headers de sécurité seulement en production
        if not settings.DEBUG:
            security_headers = getattr(settings, 'SECURITY_HEADERS', {})
            
            for header, value in security_headers.items():
                response[header] = value
                
        return response
