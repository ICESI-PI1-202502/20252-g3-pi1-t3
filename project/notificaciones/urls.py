from django.urls import path
from . import views

app_name = "notificaciones"  # ← NECESARIO

urlpatterns = [
    path('', views.ver_notificaciones, name='ver_notificaciones'),
    path('crear/', views.crear_notificacion, name='crear_notificacion'),
    
    # Marcar como leída (AJAX desde dropdown)
    path('<int:notificacion_id>/marcar-leida/', views.marcar_notificacion_leida, name='marcar_leida'),
  
]
