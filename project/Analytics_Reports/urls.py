from django.urls import path
from . import views

app_name = "Analytics_Reports"   

urlpatterns = [
    path("", views.analytics_index, name="analytics_index"),
    path("analisis-comportamiento/", views.analisis_comportamiento, name="analisis_comportamiento"),
    path("comparaciones/", views.comparaciones, name="comparaciones"),

    path("recomendaciones/", views.recomendaciones, name="recomendaciones"),
    path('configurar-notificaciones/', views.configurar_notificaciones, name='configurar_notificaciones'),




    path("asistencia/", views.asistencia, name="asistencia"),



    path('gestion-asistencia/', views.gestion_asistencia, name='gestion_asistencia'),
   path('registrar-asistencia/', views.registrar_asistencia_manual, name='registrar_asistencia_manual'),
    path('historial/<int:participante_id>/', views.historial_participante, name='historial_participante'),
   path('api/participantes-actividad/', views.obtener_participantes_actividad, name='obtener_participantes_actividad'),

]