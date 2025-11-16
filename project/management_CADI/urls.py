from django.urls import path
from . import views

app_name = "management_cadi"   

urlpatterns = [
    path("", views.cadi_index, name="management_index"),
    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/", views.show_Group_Activities, name="listar_grupos_actividad"),
    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/crear/", views.create_Group_Activity, name="crear_grupo_actividad"),
    # Listar actividades de un grupo de actividad
    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/actividades/", 
        views.show_Activities, name="listar_actividades"),

    path(
    "cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/crear-actividad/",
    views.create_Activities,
    name="crear_actividad"),

    path(
        "cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/añadir-horario/",
        views.schedule_Draft,
        name="schedule_draft",
    ),

    path("cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/actividad/<int:actividad_id>/editar/",
         views.edit_Activity, name="editar_actividad"),

    path(
        "cadi-home/<slug:grupo_nombre>/<int:grupo_id>/grupo-actividad/<int:grupo_actividad_id>/actividad/<int:actividad_id>/añadir-horario/",
        views.schedule_Draft,
        name="schedule_draft_edit",
    ),

    path(
        "grupos/<slug:grupo_nombre>/<int:grupo_id>/<int:grupo_actividad_id>/add-slot/",
        views.add_slot_to_schedule,
        name="add_slot_to_schedule",
    ),

    path('noticias/gestionar/', views.manage_news, name='gestionar_noticias'),
    path('noticias/crear/', views.create_news, name="crear_noticia"),
    path('noticias/<int:id>/editar/', views.edit_news, name="editar_noticia"),
    path('noticias/<int:id>/eliminar/', views.delete_news, name="eliminar_noticia"),
    path('noticias/<slug:slug>/<int:id>/', views.news_detail, name="detalle_noticia"),
]
