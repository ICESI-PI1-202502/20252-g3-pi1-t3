from django.urls import path
from . import views

app_name = "management_cadi"   

urlpatterns = [
    path("", views.cadi_index, name="management_index"),
    path("crear-clasificacion/", views.create_Clasification, name="form_Clasifications"),
    path("crear-actividad/", views.create_Activities, name="form_Activities"),
    path("añadir-horario/", views.add_schedule, name="form_Activities-2"),
]
