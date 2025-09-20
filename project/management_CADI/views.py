
from django.db.models import Count  # Import correction
from .models import Participaciones, Asistencias, Actividades, Notificaciones
from django.shortcuts import render

def is_admin(user):
    return user.is_authenticated and user.is_staff

# @user_passes_test(is_admin)  # Uncomment if you want to restrict access
def cadi_index(request):
    return render(request, "./cadi_Activities.html")
