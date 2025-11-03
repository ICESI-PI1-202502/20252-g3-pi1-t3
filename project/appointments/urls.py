from django.urls import path
from . import views

app_name = "appointments"

urlpatterns = [
    path("", views.appointments_home, name="home"),
    path("create/", views.create_appointment, name="create"),
    path("list/", views.my_appointments, name="list"),
     path("pro/", views.my_appointments_pro, name="pro_list"),
    path("detail/<int:id>/", views.appointment_detail, name="detail"),
    path("<int:id>/cancel/", views.appointment_cancel, name="cancel"),
    path("<int:id>/reschedule/", views.appointment_reschedule, name="reschedule"),
]

