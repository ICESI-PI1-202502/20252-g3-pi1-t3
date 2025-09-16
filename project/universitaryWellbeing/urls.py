from django.urls import path, include
from . import views
 
urlpatterns = [
    
    path("", views.user_login, name="login"),
    path('home/', views.home, name='home'),  # Esta línea debe existir
    path("register/", views.register, name="register"),
    path("preferences/", views.preferences, name="preferences"),

    # 🔹 rutas del módulo 5
    path("analytics/", views.analytics_index, name="analytics_index"),
    path("analytics/analisis/", views.analisis_comportamiento, name="analisis_comportamiento"),
    path("analytics/comparaciones/", views.comparaciones, name="comparaciones"),
    path("analytics/visualizacion/", views.visualizacion_exportacion, name="visualizacion"),
    path("analytics/recomendaciones/", views.recomendaciones, name="recomendaciones"),
    path("analytics/asistencia/", views.asistencia, name="asistencia"),
]
