# Analytics_Reports/views.py

from django.db.models import Count
from django.db.models import Count  # Import correction
from universitaryWellbeing.models import Participaciones, Asistencias, Actividades, Notificaciones, Participantes, TiposActividad

from django.shortcuts import render

def is_admin(user):
    return user.is_authenticated and user.is_staff

# @user_passes_test(is_admin)  # Uncomment if you want to restrict access
def analytics_index(request):
    return render(request, "index.html")  # Relative path to Analytics_Reports/templates/


##def analisis_comportamiento(request):
    tipo_actividad = request.GET.get("tipo_actividad")
    min_frecuencia = request.GET.get("min_frecuencia")

    # Query base
    qs = Participaciones.objects.all()

    if tipo_actividad:
        qs = qs.filter(actividades_id_actividad__tipos_actividad_id_tipo_id=tipo_actividad)

    # Agrupación administrativa: total por participante y tipo de actividad
    data = qs.values(
        "participantes_id_participante__id",
        "participantes_id_participante__nombre",
        "participantes_id_participante__semestre",
        "actividades_id_actividad__tipos_actividad_id_tipo__nombre_tipo"
    ).annotate(
        total=Count("id_participacion")
    ).order_by("participantes_id_participante__semestre")

    # Filtrar por frecuencia mínima si se solicita
    if min_frecuencia:
        try:
            min_freq = int(min_frecuencia)
            data = [d for d in data if d['total'] >= min_freq]
        except ValueError:
            pass

    tipos_actividad = TiposActividad.objects.all().order_by("nombre_tipo")

    return render(
        request,
        "analisis.html",
        {
            "data": data,
            "tipos_actividad": tipos_actividad,
        }
    )##

def analisis_comportamiento(request): 
    tipo_actividad = request.GET.get("tipo_actividad")
    min_frecuencia = request.GET.get("min_frecuencia")

    # Base queryset: contamos participaciones por participante y tipo de actividad
    data = Participaciones.objects.values(
        "participantes_id_participante__nombre",
        "participantes_id_participante__semestre",
        "actividades_id_actividad__tipos_actividad_id_tipo__nombre_tipo"
    ).annotate(total=Count("id_participacion")).order_by("participantes_id_participante__semestre")

    # Filtro por tipo de actividad (si se pasa)
    if tipo_actividad:
        data = data.filter(actividades_id_actividad__tipos_actividad_id_tipo__id_tipo=tipo_actividad)

    # Filtro por frecuencia mínima
    if min_frecuencia:
        try:
            min_freq = int(min_frecuencia)
            data = data.filter(total__gte=min_freq)
        except ValueError:
            pass

    tipos_actividad = TiposActividad.objects.all().order_by("nombre_tipo")

    return render(
        request,
        "analisis.html",
        {
            "data": data,
            "tipos_actividad": tipos_actividad,
        }
    )



# Story 2: Comparisons and statistics
def comparaciones(request):
    data = (
        Participaciones.objects
        .values("participantes_id_participante__roles_id_rol")  # Cambiado
        .annotate(total=Count("id_participacion"))
    )
    return render(request, "comparaciones.html", {"data": data})


# Story 3: Visualization and export
def visualizacion(request):
    data = (
        Participaciones.objects
        .values("id_actividad__nombre")
        .annotate(total=Count("id_participacion"))
    )
    return render(request, "visualizacion.html", {"data": data})

# Story 4: Automatic recommendations (simple example)
def recomendaciones(request):
    poca_asistencia = (
        Asistencias.objects
        .values("id_participacion__id_participante__nombre")
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



def participantes_list(request):
    # Obtener todos los participantes
    participantes = Participantes.objects.all().order_by("nombre")
    
    return render(request, "participantes.html", {"participantes": participantes})