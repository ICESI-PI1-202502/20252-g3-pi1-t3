from django.urls import path
from . import views

app_name = "searchActivities"   

urlpatterns = [
    path("", views.search, name="search"),
    path("calificar/<int:actividad_id>/", views.rateActivity, name="calificar_actividad"),
    path("add_slot/", views.add_slot_from_search, name="add_slot_from_search"),
]
