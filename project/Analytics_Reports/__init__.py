# Analytics_Reports/__init__.py

# Importar las tareas explícitamente para que Celery las descubra
from __future__ import absolute_import, unicode_literals

# Esto asegura que las tareas se registren al cargar el app
default_app_config = 'Analytics_Reports.apps.AnalyticsReportsConfig'