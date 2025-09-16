from django.urls import path, include
from . import views
from . import views_analytics

urlpatterns = [
    
    path("", views.user_login, name="login"),
    path('home/', views.home, name='home'),  # Esta línea debe existir
    path("register/", views.register, name="register"),
    path("preferences/", views.preferences, name="preferences"),

    # 🔹 rutas del módulo 5
    path("analytics/", views_analytics.analytics_index, name="analytics_index"),
    path("analytics/analisis/", views_analytics.analisis_comportamiento, name="analisis_comportamiento"),
    path("analytics/comparaciones/", views_analytics.comparaciones, name="comparaciones"),
    path("analytics/visualizacion/", views_analytics.visualizacion_exportacion, name="visualizacion"),
    path("analytics/recomendaciones/", views_analytics.recomendaciones, name="recomendaciones"),
    path("analytics/asistencia/", views_analytics.asistencia, name="asistencia"),
]
