# 20252-g3-pi1-t3\project\Analytics_Reports\urls.py
# Analytics_Reports/urls.py
from django.urls import path
from . import views

app_name = 'Analytics_Reports'

urlpatterns = [
    # Punto de entrada principal (decide según rol)
    path('', views.analytics_index, name='analytics_index'),
    
    # === ADMIN/COORDINADOR ===
    path('analisis-comportamiento/', views.analisis_comportamiento, name='analisis_comportamiento'),
    path('comparaciones/', views.comparaciones, name='comparaciones'),
    path('recomendaciones/', views.recomendaciones, name='recomendaciones'),
    path('configurar-notificaciones/', views.configurar_notificaciones, name='configurar_notificaciones'),
  
    # === DOCENTES ===
    path('dashboard-docente/', views.dashboard_docente, name='dashboard_docente'),
    path('historial/<int:id_participante>/', views.historial_participante, name='historial_participante'),

    
    # === ESTUDIANTES ===
    path('mi-historial/', views.mi_historial_estudiante, name='mi_historial'),
     
    # === COMÚN (con restricciones internas) ===
    path('registrar-asistencia/', views.registrar_asistencia_manual, name='registrar_asistencia_manual'),
]