from django.apps import AppConfig

class RealtimeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'realtime'
    verbose_name = 'Temps Réel'
    
    def ready(self):
        """Importer les signaux quand l'application est prête"""
        import realtime.signals
