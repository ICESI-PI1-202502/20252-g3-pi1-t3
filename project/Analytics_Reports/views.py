# Analytics_Reports/views.py
from django.db.models import Count
from universitaryWellbeing.models import Participaciones, Asistencias, Actividades, Notificaciones
from django.shortcuts import render

def is_admin(user):
    return user.is_authenticated and user.is_staff

# @user_passes_test(is_admin)
def analytics_index(request):
    return render(request, "index.html")  # Relative path to Analytics_Reports/templates/

# Story 1: Student behavior analysis
def analisis_comportamiento(request):
    data = (
        Participaciones.objects
        .values("participantes_id_participante__nombre",
                "participantes_id_participante__semestre",
                "id_actividad__nombre")
        .annotate(total=Count("id_participacion"))
        .order_by("participantes_id_participante__semestre")
    )
    return render(request, "analisis.html", {"data": data})

# Story 2: Comparisons and statistics
def comparaciones(request):
    data = (
        Participaciones.objects
        .values("participantes_id_participante__roles_id_rol")  # objeto rol
        # .values("participantes_id_participante__roles_id_rol_id")  # solo ID
        .annotate(total=Count("id_participacion"))
    )
    return render(request, "comparaciones.html", {"data": data})

# Story 3: Visualization and export
def visualizacion(request):
    data = (
        Participaciones.objects
        .values("actividades_id_actividad__nombre")
        .annotate(total=Count("id_participacion"))
    )
    return render(request, "visualizacion.html", {"data": data})

# Story 4: Automatic recommendations (simple example)
def recomendaciones(request):
    poca_asistencia = (
        Asistencias.objects
        .values("participantes_id_participante__nombre")
        .annotate(total=Count("id_asistencia"))
        .filter(total__lt=2)
    )
    return render(request, "recomendaciones.html", {"data": poca_asistencia})

# Story 5: Attendance and contingency management
def asistencia(request):
    data = (
        Asistencias.objects
        .values("id_estado_asistencia__nombre")
        .annotate(total=Count("id_asistencia"))
    )
    return render(request, "asistencia.html", {"data": data})

# Story 6: Data testing / debugging
def prueba_datos(request):
    data = (
        Participaciones.objects
        .select_related("participantes_id_participante")
        .values(
            "participantes_id_participante__nombre",
            "participantes_id_participante__facultad",
            "participantes_id_participante__genero",
            "participantes_id_participante__semestre",
        )
    )
    return render(request, "prueba_datos.html", {"data": data})
