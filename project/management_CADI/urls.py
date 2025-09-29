from django.urls import path
from . import views

app_name = "management_cadi"   

urlpatterns = [
    path("", views.cadi_index, name="management_index"),
    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/", views.listar_grupos_actividad, name="listar_grupos_actividad"),
    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/crear/", views.crear_grupo_actividad, name="crear_grupo_actividad"),
    # Listar actividades de un grupo de actividad
    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/actividades/", 
        views.listar_actividades, name="listar_actividades"),

    path(
    "cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/crear-actividad/",
    views.create_Activities,
    name="crear_actividad"),

    path(
        "cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/añadir-horario/",
        views.schedule_draft,
        name="schedule_draft",
    ),

    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/actividad/<int:actividad_id>/editar/",
         views.editar_actividad, name="editar_actividad"),

    path(
        "cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/actividad/<int:actividad_id>/añadir-horario/",
        views.schedule_draft,
        name="schedule_draft_edit",
    ),
]
