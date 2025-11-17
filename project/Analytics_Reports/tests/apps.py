# Analytics_Reports/tests/apps.py
from django.apps import AppConfig

class AnalyticsReportsTestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Analytics_Reports.tests'
    label = 'analytics_reports_tests'  # ← CRÍTICO: etiqueta única