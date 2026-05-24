web: daphne -b 0.0.0.0 -p $PORT academie_numerique.asgi:application
worker: celery -A academie_numerique worker -l info --concurrency=4
beat: celery -A academie_numerique beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
