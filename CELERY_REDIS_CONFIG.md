# ⚙️ Configuration Celery & Redis pour Render

Configuration optionnelle si vous utilisez des tâches asynchrones avec Celery.

## 🔍 Vérifier si Celery est utilisé

```bash
# Chercher les imports Celery dans le code
grep -r "from celery" --include="*.py" .

# Chercher les tâches Celery
grep -r "@shared_task\|@app.task" --include="*.py" .

# Vérifier requirements.txt
grep celery requirements.txt
```

## 📝 Configuration Django (settings.py)

Si Celery est utilisé, ajouter à `academie_numerique/settings.py` :

```python
# ════════════════════════════════════════════════════════
# CELERY CONFIGURATION
# ════════════════════════════════════════════════════════

import os
from celery.schedules import crontab

# Redis as message broker
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Celery settings
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes timeout
CELERY_RESULT_EXPIRES = 3600  # 1 hour

# Celery Beat Schedule (si utilisé)
CELERY_BEAT_SCHEDULE = {
    'clean-sessions': {
        'task': 'django.core.management.call_command',
        'args': ('clearsessions',),
        'schedule': crontab(hour=2, minute=0),  # 2h du matin
    },
    # Ajouter d'autres tâches planifiées ici
}

# CHANNEL LAYERS — Redis pour WebSocket
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1')],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}
```

## 📄 Fichier celery.py

Créer `academie_numerique/celery.py` :

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')

app = Celery('academie_numerique')

# Load configuration from Django settings, all configuration keys should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django app configs.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

## 📄 Fichier __init__.py

Ajouter à `academie_numerique/__init__.py` :

```python
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ('celery_app',)
```

## 🚀 Render Configuration

render.yaml déjà configuré avec :

```yaml
services:
  # Worker — Celery
  - type: worker
    name: academie-celery-worker
    env: python
    startCommand: celery -A academie_numerique worker -l info --concurrency=4
    
  # Beat — Planification
  - type: worker
    name: academie-celery-beat
    env: python
    startCommand: celery -A academie_numerique beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## 📦 Requirements.txt

Vérifier que ces packages sont présents :

```
celery>=5.3.0
django-celery-beat>=2.5.0  # Pour persistence DB des schedules
django-celery-results>=2.5.0  # Pour stocker les résultats
redis>=5.0.0  # Redis client
channels-redis>=4.2.0  # Pour WebSocket
```

Ajouter si manquant :

```bash
pip install celery django-celery-beat django-celery-results redis channels-redis
```

## 🧪 Tests locaux

### 1. Démarrer Redis

```bash
# Via Docker (recommandé)
docker run -d -p 6379:6379 redis:latest

# Ou installer Redis localement
# Windows : https://github.com/microsoftarchive/redis/releases
# Mac : brew install redis
# Linux : apt-get install redis-server
```

### 2. Démarrer Celery Worker

```bash
celery -A academie_numerique worker -l info
```

### 3. Démarrer Celery Beat (séparé)

```bash
celery -A academie_numerique beat -l info
```

### 4. Tester une tâche

```python
# Shell Django
python manage.py shell

from django.core.mail import send_mail
from celery import shared_task

@shared_task
def send_test_email(email):
    send_mail(
        'Test Celery',
        'Message test',
        'from@example.com',
        [email],
    )
    return f'Email sent to {email}'

# Déclencher la tâche
result = send_test_email.delay('user@example.com')
print(result.get())  # Attendre le résultat
```

## 📊 Monitoring Celery

### Via Flower (interface web)

```bash
# Installer
pip install flower

# Démarrer
celery -A academie_numerique flower

# Accéder
# http://localhost:5555
```

### Via Django Shell

```bash
python manage.py shell

from celery.app.control import Inspect

i = Inspect()
print(i.active())          # Tâches en cours
print(i.registered())      # Tâches enregistrées
print(i.stats())           # Stats workers
```

### Via Render Shell

```bash
# Dashboard → Service → Shell
celery -A academie_numerique inspect active
celery -A academie_numerique inspect stats
celery -A academie_numerique purge  # Nettoyer queue
```

## 🔗 Variables d'environnement Render

Vérifier que ces variables sont définies :

```
REDIS_URL=<auto-linked from Redis service>
CELERY_BROKER_URL=<same as REDIS_URL>
CELERY_RESULT_BACKEND=<same as REDIS_URL>
```

Si utilisant django-celery-beat :

```
CELERY_BEAT_SCHEDULER=django_celery_beat.schedulers:DatabaseScheduler
```

## 🐛 Dépannage courant

| Erreur | Cause | Solution |
|--------|-------|----------|
| `Connection refused` | Redis non trouvé | Vérifier REDIS_URL, Redis service créé |
| `No module named celery` | Paquet manquant | `pip install celery` |
| `Kombu error` | Problème broker | Redémarrer Redis, vérifier URL |
| `AMQP: error` | RabbitMQ vs Redis | render.yaml utilise Redis |

## 📚 Ressources

- **Celery Docs** : https://docs.celeryproject.io/
- **Django + Celery** : https://docs.celeryproject.io/en/stable/django/
- **Flower** : https://flower.readthedocs.io/
- **Channels** : https://channels.readthedocs.io/
- **Redis** : https://redis.io/docs/

## ✅ Checklist

- [ ] Celery requis pour ce projet
- [ ] `celery.py` créé
- [ ] `__init__.py` importé
- [ ] `settings.py` configuré
- [ ] `requirements.txt` mis à jour
- [ ] Redis créé sur Render
- [ ] Variables d'environnement configurées
- [ ] Tests locaux réussis
- [ ] Monitoring via Flower (optionnel)
- [ ] Déploiement Render réussi

---

**Note** : Cette configuration est optionnelle. Si le projet ne utilise pas Celery, ignorer ce fichier.

Dernière mise à jour : 2026-05-24
