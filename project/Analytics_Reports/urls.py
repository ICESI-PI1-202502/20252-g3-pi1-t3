from django.urls import path
from . import views

app_name = "analytics_reports"   

urlpatterns = [
    path("", views.analytics_index, name="analytics_index"),
    path("analisis-comportamiento/", views.analisis_comportamiento, name="analisis_comportamiento"),
    path("comparaciones/", views.comparaciones, name="comparaciones"),
    path("visualizacion/", views.visualizacion, name="visualizacion"),
    path("recomendaciones/", views.recomendaciones, name="recomendaciones"),
    path("asistencia/", views.asistencia, name="asistencia"),
]
