from django.urls import path
from . import views

app_name = "management_cadi"   

urlpatterns = [
    path("", views.cadi_index, name="management_index"),
    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/", views.listar_grupos_actividad, name="listar_grupos_actividad"),
    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/crear/", views.crear_grupo_actividad, name="crear_grupo_actividad"),
    path("crear-actividad/", views.create_Activities, name="form_Activities"),
    path("añadir-horario/", views.add_schedule, name="form_Activities-2"),
]
