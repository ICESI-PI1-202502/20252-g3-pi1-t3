# Analytics_Reports/apps.py

from django.apps import AppConfig

class AnalyticsReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Analytics_Reports'
    
    def ready(self):
        # Importar tareas cuando la app esté lista
        import Analytics_Reports.tasks  # noqa