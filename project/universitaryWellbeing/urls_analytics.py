from django.urls import path
from . import views_analytics

urlpatterns = [
    path("analisis/", views_analytics.analisis_comportamiento, name="analisis_comportamiento"),
    path("comparaciones/", views_analytics.comparaciones, name="comparaciones"),
    path("visualizacion/", views_analytics.visualizacion_exportacion, name="visualizacion"),
    path("recomendaciones/", views_analytics.recomendaciones, name="recomendaciones"),
    path("asistencia/", views_analytics.asistencia, name="asistencia"),
]
