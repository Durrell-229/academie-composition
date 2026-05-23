import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')

# WebSocket (realtime) supprimé — ASGI HTTP simple
application = get_asgi_application()
