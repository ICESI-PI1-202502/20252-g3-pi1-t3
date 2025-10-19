from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Configura el módulo settings de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BienestarUniversitario.settings')

app = Celery('BienestarUniversitario')

# Carga la configuración de Django con prefijo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubre tareas de todos los apps automáticamente
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
