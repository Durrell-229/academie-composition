"""
Backend d'authentification Laravel SSO.
Permet à un utilisateur authentifié sur Laravel de se connecter automatiquement sur Django.
"""
import requests
import logging
from django.conf import settings
from accounts.models import User

logger = logging.getLogger(__name__)


class LaravelAuthBackend:
    """
    Backend qui vérifie l'identité d'un utilisateur via l'API Laravel.
    
    Flow :
    1. L'utilisateur clique sur un lien depuis Laravel avec ?laravel_token=xxx
    2. Django appelle POST {LARAVEL_API_URL}/api/auth/check-token
    3. Si valide, Django crée/met à jour le compte et connecte l'utilisateur
    """

    def authenticate(self, request, laravel_token=None, email=None, password=None, **kwargs):
        if not laravel_token and not (email and password):
            return None

        laravel_url = getattr(settings, 'LARAVEL_API_URL', '')
        if not laravel_url:
            logger.warning("[LaravelAuth] LARAVEL_API_URL non configuré")
            return None

        try:
            # Vérifier le token via l'API Laravel
            if laravel_token:
                resp = requests.post(
                    f"{laravel_url}/api/auth/check-token",
                    json={'token': laravel_token},
                    timeout=5,
                )
            elif email and password:
                resp = requests.post(
                    f"{laravel_url}/api/auth/verify",
                    json={'email': email, 'password': password},
                    timeout=5,
                )
            else:
                return None

            if resp.status_code != 200:
                logger.warning(f"[LaravelAuth] Token invalide: {resp.status_code}")
                return None

            data = resp.json()
            email = data.get('email', '')
            if not email:
                return None

            # Chercher ou créer le user Django
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': data.get('first_name', data.get('name', '').split()[0] if data.get('name') else ''),
                    'last_name': ' '.join(data.get('last_name', data.get('name', '')).split()[1:]) if data.get('last_name') or data.get('name') else '',
                    'role': self._map_role(data.get('role', 'eleve')),
                }
            )

            # Mettre à jour les infos Laravel
            user.laravel_id = data.get('id', user.laravel_id)
            user.laravel_token = laravel_token or user.laravel_token
            user.first_name = data.get('first_name', data.get('name', user.first_name))
            if data.get('last_name'):
                user.last_name = data['last_name']
            user.save()

            logger.info(f"[LaravelAuth] User {'créé' if created else 'connecté'}: {email}")
            return user

        except requests.RequestException as e:
            logger.error(f"[LaravelAuth] Erreur API Laravel: {e}")
            return None
        except Exception as e:
            logger.error(f"[LaravelAuth] Erreur inattendue: {e}")
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def _map_role(self, laravel_role):
        """Mappe un rôle Laravel vers un rôle Django."""
        role_map = {
            'admin': 'admin',
            'administrator': 'admin',
            'teacher': 'professeur',
            'prof': 'professeur',
            'professor': 'professeur',
            'student': 'eleve',
            'eleve': 'eleve',
            'counselor': 'conseiller',
        }
        return role_map.get(laravel_role.lower() if laravel_role else '', 'eleve')
