from django.urls import path
from . import views

app_name = "tournaments"

urlpatterns = [
    path("", views.lista_torneos, name="list"),
    path("<int:id>/", views.detalle_torneo, name="detail"),  
    path("<int:id>/join/", views.inscripcion_individual, name="join_individual"),
    path("<int:id>/teams/create/", views.crear_equipo, name="create_team"),
    path("<int:id>/teams/join/", views.unirse_equipo, name="join_team"),
    path("create/", views.crear_torneo, name="create"),
    
]

