#project\universitaryWellbeing\apps.py
from django.apps import AppConfig


class UniversitarywellbeingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'universitaryWellbeing'
    
    def ready(self):
        import universitaryWellbeing.signals

 
 