from django.urls import path
from . import views

app_name = "management_cadi"   

urlpatterns = [
    path("", views.cadi_index, name="management_index"),
    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/", views.showGroupActivities, name="listar_grupos_actividad"),
    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/crear/", views.createGroupActivity, name="crear_grupo_actividad"),
    # Listar actividades de un grupo de actividad
    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/actividades/", 
        views.showActivities, name="listar_actividades"),

    path(
    "cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/crear-actividad/",
    views.createActivities,
    name="crear_actividad"),

    path(
        "cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/añadir-horario/",
        views.scheduleDraft,
        name="schedule_draft",
    ),

    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/actividad/<int:actividad_id>/editar/",
         views.editActivity, name="editar_actividad"),

    path(
        "cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/actividad/<int:actividad_id>/añadir-horario/",
        views.scheduleDraft,
        name="schedule_draft_edit",
    ),

    path(
        "grupos/<slug:grupo_nombre>/<int:grupo_id>/<int:grupo_actividad_id>/add-slot/",
        views.add_slot_to_schedule,
        name="add_slot_to_schedule",
    ),
]
