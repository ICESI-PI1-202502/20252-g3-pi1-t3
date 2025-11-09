from django.urls import path
from . import views

app_name = "tournaments"

urlpatterns = [
    path("", views.lista_torneos, name="list"),
    path("<int:id>/", views.detalle_torneo, name="detail"),  
    path("<int:id>/join/", views.inscripcion_individual, name="join_individual"),
    path("<int:torneo_id>/teams/create/", views.crear_equipo_en_torneo, name="create_team"),
    path("<int:id>/teams/join/", views.unirse_equipo, name="join_team"),
    path("create/", views.crear_torneo, name="create"),
    path("<int:torneo_id>/teams/<int:team_id>/manage/", views.gestionar_equipo, name="manage_team"),
    path("<int:id>/matches/create/", views.partidos_crear, name="matches_create"),
    path("matches/<int:match_id>/result/", views.partido_resultado, name="match_result"),
    path("matches/<int:match_id>/record/", views.partido_resultado, name="match_record"),
]

