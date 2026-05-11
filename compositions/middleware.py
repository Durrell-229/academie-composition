"""
Middleware pour protéger l'accès aux corrigés types via /media/
"""
from django.http import HttpResponseForbidden
import os


class CorrigeTypeProtectionMiddleware:
    """
    Bloque l'accès direct aux corrigés types via /media/ pour les élèves.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifier si c'est une requête vers /media/exams/
        if request.path.startswith('/media/exams/'):
            # Vérifier si l'utilisateur est un élève
            if hasattr(request, 'user') and request.user.is_authenticated:
                if request.user.role == 'eleve':
                    # Récupérer le nom du fichier
                    filename = os.path.basename(request.path).lower()
                    
                    # Bloquer si le nom contient des indices de corrigé type
                    corrige_keywords = ['corrige', 'grille', 'bareme', 'solution', 'reponse']
                    if any(keyword in filename for keyword in corrige_keywords):
                        return HttpResponseForbidden(
                            "Accès interdit. Les corrigés types ne sont pas accessibles aux élèves."
                        )
        
        return self.get_response(request)
