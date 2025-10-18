from django.urls import path
from . import views

app_name = "searchActivities"   

urlpatterns = [
    path("", views.search, name="search"),
    path("calificar/<int:actividad_id>/", views.calificar_actividad, name="calificar_actividad"),
    
]
