#project\management_CADI\tests\apps.py
from django.apps import AppConfig

class ManagementCADITestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "management_CADI.tests"
    label = "management_cadi_tests"  # coincidir con app_label de los modelos
