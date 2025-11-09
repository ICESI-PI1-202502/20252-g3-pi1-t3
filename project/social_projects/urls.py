from django.urls import path
from . import views

app_name = "social_projects"

urlpatterns = [
    path("proyectos/crear/", views.crear_proyecto_social, name="crear_proyecto"),
    path("proyectos/", views.lista_proyectos, name="lista_proyectos"),
    path("proyectos/<int:pk>/", views.detalle_proyecto, name="detalle_proyecto"), 
    path("proyectos/<int:pk>/inscribirse/", views.inscribirse_psu, name="inscribirse_psu"), 
    path("<int:pk>/consultar/", views.consultar_duda, name="consultar_duda"),
 
]