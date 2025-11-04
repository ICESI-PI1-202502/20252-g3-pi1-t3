from django.db.models import Count, Avg, Q, F, Case, When, IntegerField,Max, ExpressionWrapper
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.http import HttpResponse, JsonResponse
from datetime import datetime, timedelta
import csv
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import datetime, date
from django.db import connection
import os
from universitaryWellbeing.models import (
    Participaciones, Asistencias, Actividades, Notificaciones, HistorialParticipaciones,
    Participantes, TiposActividad, Roles, Citas, ProyectosSociales, Equipos,EstadosAsistencia, ConfiguracionNotificaciones,
    RolesParticipacion,EstadosParticipacion 
)

LOG_DIR = os.path.join("Analytics_Reports", "logs", "emails")
LOG_EMAILS_FILE = os.path.join(LOG_DIR, "log_emails.txt")

def log_email(destinatarios, asunto):
    """Guarda en un TXT los destinatarios y el asunto del correo enviado"""
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_EMAILS_FILE, "a", encoding="utf-8") as f:
        linea = f"{timezone.now().strftime('%Y-%m-%d %H:%M:%S')} | {asunto} | {', '.join(destinatarios)}\n"
        f.write(linea)

def enviar_email(asunto, mensaje, destinatarios):
    """Envía un email y lo registra en el log"""
    if not destinatarios:
        return
    send_mail(
        asunto,
        mensaje,
        settings.DEFAULT_FROM_EMAIL,
        destinatarios,
        fail_silently=True
    )
    log_email(destinatarios, asunto)


# ========== FUNCIONES CORREGIDAS CON LÓGICA CLARA ==========

def obtener_alertas_riesgo():
    """
    RIESGO CRÍTICO: Estudiantes con muy pocas asistencias Y mucha inactividad
    - Menos de 2 asistencias totales
    - Sin asistir en los últimos 21 días
    """
    config = ConfiguracionNotificaciones.obtener_config()
    fecha_limite = timezone.now().date() - timedelta(days=config.dias_riesgo_critico)
    
    return (
        Participaciones.objects
        .annotate(
            total_asistencias=Count('asistencias', distinct=True),
            ultima_asistencia=Max('asistencias__fecha')
        )
        .filter(
            total_asistencias__lte=config.umbral_riesgo_critico
        )
        .filter(
            Q(ultima_asistencia__lt=fecha_limite) | Q(ultima_asistencia__isnull=True)
        )
        .select_related('participantes_id_participante', 'actividades_id_actividad')
        .order_by('total_asistencias', 'ultima_asistencia')
    )


def obtener_estudiantes_poca_asistencia():
    """
    BAJA ASISTENCIA: Estudiantes con pocas asistencias pero NO en riesgo crítico
    - Entre 3 y 5 asistencias
    - Han asistido en las últimas 3 semanas
    """
    config = ConfiguracionNotificaciones.obtener_config()
    fecha_limite_actividad = timezone.now().date() - timedelta(days=21)
    
    return (
        Participaciones.objects
        .annotate(
            total_asistencias=Count('asistencias', distinct=True),
            ultima_asistencia=Max('asistencias__fecha')
        )
        .filter(
            total_asistencias__gt=config.umbral_riesgo_critico,
            total_asistencias__lt=config.umbral_baja_asistencia
        )
        .filter(ultima_asistencia__gte=fecha_limite_actividad)
        .select_related('participantes_id_participante', 'actividades_id_actividad')
        .order_by('total_asistencias')
    )


def obtener_estudiantes_inactivos():
    """
    INACTIVOS: Estudiantes con participación previa pero sin asistir recientemente
    - Tienen más de 5 asistencias históricas
    - No han asistido en los últimos 14 días
    """
    config = ConfiguracionNotificaciones.obtener_config()
    fecha_limite = timezone.now().date() - timedelta(days=config.dias_inactividad)
    
    return (
        Participaciones.objects
        .annotate(
            total_asistencias=Count('asistencias', distinct=True),
            ultima_asistencia=Max('asistencias__fecha')
        )
        .filter(
            total_asistencias__gte=config.umbral_baja_asistencia
        )
        .filter(
            Q(ultima_asistencia__lt=fecha_limite) | Q(ultima_asistencia__isnull=True)
        )
        .select_related('participantes_id_participante', 'actividades_id_actividad')
        .order_by('-total_asistencias')
    )


def obtener_proximos_reconocimientos():
    """
    PRÓXIMOS A RECONOCIMIENTO: Estudiantes cerca de alcanzar el objetivo
    """
    config = ConfiguracionNotificaciones.obtener_config()
    meta = config.asistencias_reconocimiento
    margen = config.margen_proximo_reconocimiento
    
    return (
        Participaciones.objects
        .annotate(
            total_asistencias=Count('asistencias', distinct=True),
            asistencias_faltantes=ExpressionWrapper(
                meta - Count('asistencias', distinct=True),
                output_field=IntegerField()
            )
        )
        .filter(
            total_asistencias__gte=meta - margen,
            total_asistencias__lt=meta
        )
        .select_related('participantes_id_participante', 'actividades_id_actividad')
        .order_by('-total_asistencias')
    )


def obtener_estudiantes_destacados():
    """
    DESTACADOS: Estudiantes con excelente participación
    """
    config = ConfiguracionNotificaciones.obtener_config()
    
    return (
        Participaciones.objects
        .annotate(total_asistencias=Count('asistencias', distinct=True))
        .filter(total_asistencias__gte=config.asistencias_destacado)
        .select_related('participantes_id_participante', 'actividades_id_actividad')
        .order_by('-total_asistencias')
    )


def obtener_estudiantes_activos(dias_actividad=14):
    """
    ACTIVOS: Estudiantes con actividad reciente
    """
    fecha_limite = timezone.now().date() - timedelta(days=dias_actividad)
    return (
        Participaciones.objects
        .annotate(
            asistencias_recientes=Count(
                'asistencias',
                filter=Q(asistencias__fecha__gte=fecha_limite),
                distinct=True
            )
        )
        .filter(asistencias_recientes__gte=1)
        .select_related('participantes_id_participante', 'actividades_id_actividad')
        .order_by('-asistencias_recientes')
    )


# ========== VISTA PRINCIPAL ==========

def recomendaciones(request):
    """Vista principal para mostrar recomendaciones automáticas"""
    
    # Obtener todas las categorías
    alertas_riesgo = obtener_alertas_riesgo()
    poca_asistencia = obtener_estudiantes_poca_asistencia()
    estudiantes_inactivos = obtener_estudiantes_inactivos()
    proximos_reconocimientos = obtener_proximos_reconocimientos()
    estudiantes_destacados = obtener_estudiantes_destacados()
    estudiantes_activos = obtener_estudiantes_activos()
    
    context = {
        'alertas_riesgo': alertas_riesgo,
        'poca_asistencia': poca_asistencia,
        'estudiantes_inactivos': estudiantes_inactivos,
        'proximos_reconocimientos': proximos_reconocimientos,
        'estudiantes_destacados': estudiantes_destacados,
        'estudiantes_activos': estudiantes_activos,
        'fecha_actualizacion': timezone.now(),
        'config': ConfiguracionNotificaciones.obtener_config()
    }
    
 
    return render(request, "recomendaciones.html", context)


# ========== NOTIFICACIONES ==========
 


 

def enviar_notificacion_reconocimientos(estudiantes):
    """Notificaciones de motivación a estudiantes próximos a reconocimiento"""
    config = ConfiguracionNotificaciones.obtener_config()
    
    for est in estudiantes:
        nombre = est.participantes_id_participante.nombre
        asunto = f"🏆 ¡Estás cerca de un reconocimiento, {nombre}!"
        mensaje = f"""
Hola {nombre},

¡Excelente trabajo! Tienes {est.total_asistencias} asistencias en {est.actividades_id_actividad.nombre}.

Solo necesitas {est.asistencias_faltantes} más para obtener tu reconocimiento.

¡Sigue así! 💪

---
Equipo de Bienestar Universitario
"""
        correo = est.participantes_id_participante.correo
        if correo:
            enviar_email(asunto, mensaje, [correo])


# ========== CONFIGURACIÓN ==========

def configurar_notificaciones(request):
    """Permite configurar parámetros de las notificaciones automáticas"""
    config = ConfiguracionNotificaciones.obtener_config()
    
    if request.method == 'POST':
        config.umbral_riesgo_critico = int(request.POST.get('umbral_riesgo_critico', 2))
        config.umbral_baja_asistencia = int(request.POST.get('umbral_baja_asistencia', 5))
        config.dias_inactividad = int(request.POST.get('dias_inactividad', 14))
        config.dias_riesgo_critico = int(request.POST.get('dias_riesgo_critico', 21))
        config.asistencias_reconocimiento = int(request.POST.get('asistencias_reconocimiento', 10))
        config.margen_proximo_reconocimiento = int(request.POST.get('margen_proximo_reconocimiento', 2))
        config.asistencias_destacado = int(request.POST.get('asistencias_destacado', 15))
        config.envio_automatico = request.POST.get('envio_automatico') == 'on'
        config.frecuencia_envio = request.POST.get('frecuencia_envio', 'semanal')
        config.emails_staff = request.POST.get('emails_staff', 'admin@academia.com')
        
        config.save()
        messages.success(request, 'Configuración guardada correctamente.')
        return redirect('Analytics_Reports:recomendaciones')
    
    return render(request, 'configurar_notificaciones.html', {'config': config})

def is_admin(user):
    return user.is_authenticated and user.is_staff

def analytics_index(request):
    return render(request, "index.html")


def analisis_comportamiento(request): 
    tipo_actividad = request.GET.get("tipo_actividad")
    min_frecuencia = request.GET.get("min_frecuencia")
    export = request.GET.get("export")
    mostrar_todos = request.GET.get("mostrar_todos")  # Nuevo parámetro
    
    # Verificar si hay al menos un filtro aplicado o se solicitó mostrar todos
    has_filters = bool(tipo_actividad or min_frecuencia or mostrar_todos)
    
    # Solo consultar si hay filtros o si se está exportando
    if has_filters or export:
        # Base queryset: contamos participaciones por participante y tipo de actividad
        data = (
            Participaciones.objects.values(
                "participantes_id_participante__nombre",
                "participantes_id_participante__correo",
                "participantes_id_participante__semestre",
                "participantes_id_participante__facultad",
                "participantes_id_participante__roles_id_rol__nombre_rol",
                "actividades_id_actividad__tipos_actividad_id_tipo__nombre_tipo",
            )
            .annotate(total=Count("id_participacion"))
            .order_by("participantes_id_participante__semestre")
        )

        # Filtro por tipo de actividad
        if tipo_actividad:
            data = data.filter(
                actividades_id_actividad__tipos_actividad_id_tipo__id_tipo=tipo_actividad
            )

        # Filtro por frecuencia mínima
        if min_frecuencia:
            try:
                min_freq = int(min_frecuencia)
                data = data.filter(total__gte=min_freq)
            except ValueError:
                pass

        # --- EXPORTACIÓN CSV ---
        if export == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="analisis_comportamiento.csv"'

            writer = csv.writer(response)
            writer.writerow([
                "Usuario", "Correo", "Semestre", "Facultad",
                "Rol", "Tipo de Actividad", "Total Participaciones", "Frecuencia"
            ])

            for item in data:
                total = item["total"]
                if total >= 5:
                    frecuencia = "Alta"
                elif total >= 2:
                    frecuencia = "Media"
                else:
                    frecuencia = "Baja"

                writer.writerow([
                    item.get("participantes_id_participante__nombre", "N/A"),
                    item.get("participantes_id_participante__correo", "N/A"),
                    item.get("participantes_id_participante__semestre", "N/A"),
                    item.get("participantes_id_participante__facultad", "Sin especificar"),
                    item.get("participantes_id_participante__roles_id_rol__nombre_rol", "Sin rol"),
                    item.get("actividades_id_actividad__tipos_actividad_id_tipo__nombre_tipo", "Sin especificar"),
                    total,
                    frecuencia
                ])

            return response
    else:
        # No hay filtros aplicados, no mostrar datos
        data = None

    # --- Render normal ---
    tipos_actividad = TiposActividad.objects.all().order_by("nombre_tipo")

    return render(
        request,
        "analisis.html",
        {
            "data": data,
            "tipos_actividad": tipos_actividad,
            "has_filters": has_filters,
            "mostrar_todos": mostrar_todos,
        }
    )

 
def participantes_list(request):
    participantes = Participantes.objects.all().order_by("nombre")
    return render(request, "participantes.html", {"participantes": participantes})


def comparaciones(request):
    tiempo = request.GET.get("tiempo", "todos")
    agrupacion = request.GET.get("agrupacion", "facultad")
    semestre_filtro = request.GET.get("semestre_filtro", "")
    
    # Variable para controlar si se debe ejecutar la consulta
    ejecutar_consulta = True
    mensaje_filtro = None
    
    # Verificar si los filtros están completos según el tipo de tiempo seleccionado
    if tiempo == "semestre" and not semestre_filtro:
        ejecutar_consulta = False
        mensaje_filtro = "Selecciona un número de semestre para ver los resultados."
    elif tiempo == "periodo":
        inicio_str = request.GET.get("inicio")
        fin_str = request.GET.get("fin")
        if not inicio_str or not fin_str:
            ejecutar_consulta = False
            mensaje_filtro = "Selecciona las fechas de inicio y fin para ver los resultados."
    
    resultados = []
    
    if ejecutar_consulta:
        # Lógica de filtrado temporal
        participaciones_query = Participaciones.objects
        asistencias_query = Asistencias.objects
        participantes_query = Participantes.objects
        
        if tiempo == "semestre" and semestre_filtro:
            # Filtrar por semestre del estudiante (1, 2, 3, 4, etc.)
            participaciones_query = participaciones_query.filter(
                participantes_id_participante__semestre=semestre_filtro
            )
            participantes_query = participantes_query.filter(
                semestre=semestre_filtro
            )
            # Para asistencias, filtramos a través de la relación con participaciones
            asistencias_query = asistencias_query.filter(
                participaciones_id_participacion__participantes_id_participante__semestre=semestre_filtro
            )
        
        elif tiempo == "periodo":
            inicio_str = request.GET.get("inicio")
            fin_str = request.GET.get("fin")
            
            if inicio_str and fin_str:
                try:
                    inicio = parse_date(inicio_str.strip())
                    fin = parse_date(fin_str.strip())
                    if inicio and fin:
                        participaciones_query = participaciones_query.filter(
                            fecha_inscripcion__range=[inicio, fin]
                        )
                        asistencias_query = asistencias_query.filter(
                            fecha__range=[inicio, fin]
                        )
                except (ValueError, TypeError):
                    pass
        
        # Lógica de agrupación
        if agrupacion == "facultad":
            resultados = (
                participaciones_query
                .values("participantes_id_participante__facultad")
                .annotate(total=Count("id_participacion"))
                .order_by("participantes_id_participante__facultad")
            )
        elif agrupacion == "genero":
            resultados = (
                participaciones_query
                .values("participantes_id_participante__genero")
                .annotate(total=Count("id_participacion"))
                .order_by("participantes_id_participante__genero")
            )
        elif agrupacion == "rol":
            resultados = (
                participaciones_query
                .values("participantes_id_participante__roles_id_rol__nombre_rol")
                .annotate(total=Count("id_participacion"))
                .order_by("participantes_id_participante__roles_id_rol__nombre_rol")
            )
        elif agrupacion == "semestre":
            resultados = (
                participaciones_query
                .values("participantes_id_participante__semestre")
                .annotate(total=Count("id_participacion"))
                .order_by("participantes_id_participante__semestre")
            )
        
        # Métricas generales
        total_asistencias = asistencias_query.count()
        nuevos = participantes_query.count()
        reincidencia = (
            participaciones_query
            .values("participantes_id_participante")
            .annotate(total=Count("id_participacion"))
            .filter(total__gt=1)
            .count()
        )
        
        metricas = {
            "total_asistencias": total_asistencias,
            "nuevos": nuevos,
            "reincidencia": reincidencia,
        }
    else:
        # No se ejecuta consulta, métricas en 0
        metricas = {
            "total_asistencias": 0,
            "nuevos": 0,
            "reincidencia": 0,
        }
    
    # Obtener lista de semestres disponibles desde la base de datos
    semestres_disponibles = (
        Participantes.objects
        .values_list('semestre', flat=True)
        .distinct()
        .order_by('semestre')
    )
    # Filtrar valores nulos y convertir a lista
    semestres_disponibles = [s for s in semestres_disponibles if s is not None]
    
    context = {
        "tiempo": tiempo,
        "agrupacion": agrupacion,
        "semestre_filtro": semestre_filtro,
        "semestres_disponibles": semestres_disponibles,
        "resultados": resultados,
        "metricas": metricas,
        "ejecutar_consulta": ejecutar_consulta,
        "mensaje_filtro": mensaje_filtro,
    }
    
    return render(request, "comparaciones.html", context)







 # views.py - Sistema completo de recomendaciones  
 #######################################################
 #######################################################
 #######################################################
 #######################################################
 #######################################################

 
  
def enviar_email_staff(asunto, mensaje):
    """Envía email al personal administrativo"""
    staff_emails = ['admin@academia.com', 'coordinador@academia.com']
    enviar_email(asunto, mensaje, staff_emails)

def generar_encuesta_feedback():
    """Genera y envía encuestas de retroalimentación automáticas"""
    estudiantes_completaron = (
        Participaciones.objects
        .filter(fecha_finalizacion__isnull=False)
        .filter(fecha_finalizacion__gte=timezone.now() - timedelta(days=7))
        .select_related('participantes_id_participante', 'actividades_id_actividad')
    )
    
    for participacion in estudiantes_completaron:
        enviar_encuesta_feedback(participacion)

def enviar_encuesta_feedback(participacion):
    """Envía encuesta de feedback individual"""
    nombre_completo = f"{participacion.participantes_id_participante.nombre} {participacion.participantes_id_participante.apellido}"
    asunto = f"Tu opinión es importante - {participacion.actividades_id_actividad.nombre}"
    url_encuesta = f"https://forms.gle/encuesta?id={participacion.id_participacion}"
    mensaje = f"""
Hola {nombre_completo},

Gracias por participar en {participacion.actividades_id_actividad.nombre}.

Tu experiencia es muy valiosa para nosotros. Por favor, tómate unos minutos 
para completar esta breve encuesta:

{url_encuesta}

¡Gracias por tu tiempo!
"""
    correo = participacion.participantes_id_participante.correo
    if correo:
        enviar_email(asunto, mensaje, [correo])

 
 #######################################################
 #######################################################
 #######################################################
 #######################################################
 #######################################################
 #######################################################







 

def obtener_participantes_actividad(request):
    """API endpoint para obtener participantes de una actividad"""
    actividad_id = request.GET.get('actividad_id')
    
    if not actividad_id:
        return JsonResponse({'error': 'ID de actividad requerido'}, status=400)
    
    try:
        participaciones = Participaciones.objects.filter(
            actividades_id_actividad_id=actividad_id
        ).select_related('participantes_id_participante').order_by(
            'participantes_id_participante__nombre'
        )
        
        participantes_data = []
        for participacion in participaciones:
            participante = participacion.participantes_id_participante
            participantes_data.append({
                'participacion_id': participacion.id_participacion,
                'nombre': f"{participante.nombre} {participante.apellido}",
                'semestre': participante.semestre,
                'programa': participante.programa,
                'correo': participante.correo
            })
        
        return JsonResponse({
            'participantes': participantes_data,
            'total': len(participantes_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from datetime import datetime, timedelta
 
@login_required
def historial_participante(request, id_participante):
    """
    Vista para mostrar el historial completo de asistencia de un participante
    """
    # Obtener el participante
    participante = get_object_or_404(Participantes, pk=id_participante)
    
    # Obtener todas las participaciones del participante
    participaciones = Participaciones.objects.filter(
        participantes_id_participante=participante
    ).select_related('actividades_id_actividad')
    
    # Obtener todas las asistencias del participante
    asistencias = Asistencias.objects.filter(
        participaciones_id_participacion__participantes_id_participante=participante
    ).select_related(
        'participaciones_id_participacion__actividades_id_actividad',
        'estados_asistencia_id_estado_asistencia'
    ).order_by('-fecha')
    
    # Filtros opcionales
    actividad_filtro = request.GET.get('actividad', '')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    estado_filtro = request.GET.get('estado', '')
    
    if actividad_filtro:
        asistencias = asistencias.filter(
            participaciones_id_participacion__actividades_id_actividad__id_actividad=actividad_filtro
        )
    
    if fecha_inicio:
        asistencias = asistencias.filter(fecha__gte=fecha_inicio)
    
    if fecha_fin:
        asistencias = asistencias.filter(fecha__lte=fecha_fin)
    
    if estado_filtro:
        asistencias = asistencias.filter(
            estados_asistencia_id_estado_asistencia__id_estado_asistencia=estado_filtro
        )
    
    # Calcular estadísticas
    total_asistencias = asistencias.count()
    
    # Estadísticas por estado
    stats_estados = asistencias.values(
        'estados_asistencia_id_estado_asistencia__nombre'
    ).annotate(
        cantidad=Count('id_asistencia')
    )
    
    # Convertir a diccionario para fácil acceso
    stats_dict = {
        'presente': 0,
        'ausente': 0,
        'justificado': 0,
        'tardanza': 0
    }
    
    for stat in stats_estados:
        estado_nombre = stat['estados_asistencia_id_estado_asistencia__nombre'].lower()
        stats_dict[estado_nombre] = stat['cantidad']
    
    # Calcular porcentaje de asistencia
    if total_asistencias > 0:
        porcentaje_asistencia = round(
            (stats_dict['presente'] / total_asistencias) * 100, 2
        )
    else:
        porcentaje_asistencia = 0
    
    # Estadísticas por actividad
    stats_actividades = asistencias.values(
        'participaciones_id_participacion__actividades_id_actividad__nombre',
        'estados_asistencia_id_estado_asistencia__nombre'
    ).annotate(
        cantidad=Count('id_asistencia')
    )
    
    # Organizar estadísticas por actividad
    actividades_stats = {}
    for stat in stats_actividades:
        actividad_nombre = stat['participaciones_id_participacion__actividades_id_actividad__nombre']
        estado_nombre = stat['estados_asistencia_id_estado_asistencia__nombre']
        
        if actividad_nombre not in actividades_stats:
            actividades_stats[actividad_nombre] = {
                'nombre': actividad_nombre,
                'presente': 0,
                'ausente': 0,
                'justificado': 0,
                'tardanza': 0,
                'total': 0
            }
        
        actividades_stats[actividad_nombre][estado_nombre.lower()] = stat['cantidad']
        actividades_stats[actividad_nombre]['total'] += stat['cantidad']
    
    # Calcular porcentaje de asistencia por actividad
    for actividad in actividades_stats.values():
        if actividad['total'] > 0:
            actividad['porcentaje'] = round(
                (actividad['presente'] / actividad['total']) * 100, 2
            )
        else:
            actividad['porcentaje'] = 0
    
    # Obtener listas para filtros
    from universitaryWellbeing.models import EstadosAsistencia
    estados_asistencia = EstadosAsistencia.objects.all()
    
    context = {
        'participante': participante,
        'asistencias': asistencias,
        'participaciones': participaciones,
        'total_asistencias': total_asistencias,
        'stats': stats_dict,
        'porcentaje_asistencia': porcentaje_asistencia,
        'actividades_stats': actividades_stats.values(),
        'estados_asistencia': estados_asistencia,
        'actividad_filtro': actividad_filtro,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estado_filtro': estado_filtro,
    }
    
    return render(request, 'historial_participante.html', context)


def asistencia(request):
    data = (
        Asistencias.objects
        .values("estados_asistencia_id_estado_asistencia__nombre")
        .annotate(total=Count("id_asistencia"))
    )
    return render(request, "asistencia.html", {"data": data})



def registrar_asistencia_cedula_view(request):
    """Vista principal para registro rápido por cédula"""
    
    actividad_seleccionada = request.GET.get('actividad_id', '')
    fecha_seleccionada = request.GET.get('fecha', timezone.now().date().strftime('%Y-%m-%d'))
    
    actividades = Actividades.objects.all().order_by('nombre')
    estados_asistencia = EstadosAsistencia.objects.all().order_by('nombre')
    
    stats = {'total': 0, 'presentes': 0}
    ultimos_registros = []
    
    if actividad_seleccionada:
        try:
            fecha_obj = datetime.strptime(fecha_seleccionada, '%Y-%m-%d').date()
            
            asistencias_dia = Asistencias.objects.filter(
                fecha=fecha_obj,
                participaciones_id_participacion__actividades_id_actividad_id=actividad_seleccionada
            ).select_related(
                'estados_asistencia_id_estado_asistencia',
                'participaciones_id_participacion__participantes_id_participante'
            )
            
            stats = {
                'total': asistencias_dia.count(),
                'presentes': asistencias_dia.filter(
                    estados_asistencia_id_estado_asistencia__nombre__icontains='presente'
                ).count(),
            }
            
            ultimos_registros = asistencias_dia.order_by('-id_asistencia')[:10]
            
        except ValueError:
            pass
    
    context = {
        'actividades': actividades,
        'estados_asistencia': estados_asistencia,
        'actividad_seleccionada': actividad_seleccionada,
        'fecha_seleccionada': fecha_seleccionada,
        'stats': stats,
        'ultimos_registros': ultimos_registros,
    }
    
    return render(request, 'registrar_asistencia_cedula.html', context)


@require_http_methods(["POST"])
def registrar_asistencia_rapido(request):
    """Registra asistencia directamente con cédula"""
    
    try:
        cedula = request.POST.get('cedula', '').strip()
        estado_id = request.POST.get('estado_id')
        actividad_id = request.POST.get('actividad_id')
        fecha_str = request.POST.get('fecha')
        
        if not all([cedula, estado_id, actividad_id, fecha_str]):
            return JsonResponse({
                'error': 'Faltan datos requeridos'
            }, status=400)
        
        # Buscar o crear participante por cédula (username)
        participante, created = Participantes.objects.get_or_create(
            correo=cedula,  # Usando correo como identificador temporal
            defaults={
                'nombre': f'Usuario {cedula}',
                'apellido': '',
                'roles_id_rol_id': 1  # Ajusta según tu rol por defecto
            }
        )
        
        # Buscar o crear participación
        participacion, created = Participaciones.objects.get_or_create(
            participantes_id_participante=participante,
            actividades_id_actividad_id=actividad_id,
            defaults={
                'fecha_inscripcion': timezone.now().date(),
                'roles_participacion_id_rol_participacion_id': 1,  # Ajustar
                'estados_participacion_id_estado_participacion_id': 1  # Ajustar
            }
        )
        
        # Obtener estado y fecha
        estado = get_object_or_404(EstadosAsistencia, id_estado_asistencia=estado_id)
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        # Verificar si ya existe asistencia
        asistencia_existente = Asistencias.objects.filter(
            participaciones_id_participacion=participacion,
            fecha=fecha_obj
        ).first()
        
        if asistencia_existente:
            asistencia_existente.estados_asistencia_id_estado_asistencia = estado
            asistencia_existente.save()
            mensaje = f'✓ Asistencia actualizada - Cédula: {cedula}'
        else:
            ultimo_id = Asistencias.objects.aggregate(Max('id_asistencia'))['id_asistencia__max'] or 0
            
            Asistencias.objects.create(
                id_asistencia=ultimo_id + 1,
                fecha=fecha_obj,
                estados_asistencia_id_estado_asistencia=estado,
                participaciones_id_participacion=participacion
            )
            
            mensaje = f'✓ Registrado exitosamente - Cédula: {cedula} - Estado: {estado.nombre}'
        
        return JsonResponse({
            'success': True,
            'message': mensaje
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error: {str(e)}'
        }, status=500)
    
def registrar_asistencia_manual(request):
    """Registra asistencias por cédula, creando User y Participante si no existen"""

    actividades = Actividades.objects.values("id_actividad", "nombre")
    fecha_hoy = timezone.now().date().strftime('%Y-%m-%d')
    resultados = None

    if request.method == 'POST':
        actividad_id = request.POST.get('actividad_id')
        fecha_str = request.POST.get('fecha')
        cedulas_texto = request.POST.get('cedulas', '')

        cedulas = [c.strip() for c in cedulas_texto.split('\n') if c.strip()]
        exitosos = 0
        errores = []

        try:
            actividad = get_object_or_404(Actividades, id_actividad=actividad_id)
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()

            # Estado "Presente"
            estado_presente = EstadosAsistencia.objects.filter(nombre__icontains='presente').first()
            if not estado_presente:
                estado_presente = EstadosAsistencia.objects.first()
            
            if not estado_presente:
                messages.error(request, 'No hay estados de asistencia configurados')
                return render(request, 'registrar_asistencia.html', {
                    'actividades': actividades, 
                    'fecha_hoy': fecha_hoy, 
                    'resultados': resultados
                })

            # CRÍTICO: Obtener rol de participación válido
            rol_participacion = RolesParticipacion.objects.first()
            if not rol_participacion:
                messages.error(request, 'No hay roles de participación configurados en el sistema')
                return render(request, 'registrar_asistencia.html', {
                    'actividades': actividades, 
                    'fecha_hoy': fecha_hoy, 
                    'resultados': resultados
                })

            # Obtener estado de participación válido
            estado_participacion = EstadosParticipacion.objects.first()
            if not estado_participacion:
                messages.error(request, 'No hay estados de participación configurados')
                return render(request, 'registrar_asistencia.html', {
                    'actividades': actividades, 
                    'fecha_hoy': fecha_hoy, 
                    'resultados': resultados
                })

            # Obtener rol de participante válido
            rol_participante = Roles.objects.first()
            if not rol_participante:
                messages.error(request, 'No hay roles de participantes configurados')
                return render(request, 'registrar_asistencia.html', {
                    'actividades': actividades, 
                    'fecha_hoy': fecha_hoy, 
                    'resultados': resultados
                })

            for cedula in cedulas:
                try:
                    # User
                    user, _ = User.objects.get_or_create(
                        username=cedula,
                        defaults={
                            'email': f"{cedula}@temp.com",
                            'password': 'pbkdf2_sha256$260000$temp$temp',
                            'first_name': '',
                            'last_name': '',
                            'is_staff': False,
                            'is_active': True,
                            'is_superuser': False,
                            'date_joined': timezone.now()
                        }
                    )

                    # Participante
                    participante, creado = Participantes.objects.get_or_create(
                        correo=user.email,
                        defaults={
                            'nombre': f"Usuario {cedula}",
                            'apellido': '',
                            'roles_id_rol': rol_participante,
                            'estado_activo': 'S',
                            'user': user
                        }
                    )

                    if not creado:
                        cambios = False
                        if participante.user is None:
                            participante.user = user
                            cambios = True
                        if participante.estado_activo != 'S':
                            participante.estado_activo = 'S'
                            cambios = True
                        if cambios:
                            participante.save()

                    # Participación
                    participacion, _ = Participaciones.objects.get_or_create(
                        participantes_id_participante=participante,
                        actividades_id_actividad=actividad,
                        defaults={
                            'fecha_inscripcion': fecha_obj,
                            'roles_participacion_id_rol_participacion': rol_participacion,
                            'estados_participacion_id_estado_participacion': estado_participacion
                        }
                    )

                    # Verificar asistencia
                    if Asistencias.objects.filter(participaciones_id_participacion=participacion, fecha=fecha_obj).exists():
                        errores.append(f"Cédula {cedula}: Ya tiene asistencia registrada")
                        continue

                    # Crear asistencia
                    Asistencias.objects.create(
                        fecha=fecha_obj,
                        estados_asistencia_id_estado_asistencia=estado_presente,
                        participaciones_id_participacion=participacion
                    )

                    exitosos += 1

                except Exception as e:
                    errores.append(f"Cédula {cedula}: {str(e)}")

            resultados = {'exitosos': exitosos, 'errores': errores}

            if exitosos > 0:
                messages.success(request, f'{exitosos} asistencias registradas')
            if errores:
                messages.warning(request, f'{len(errores)} errores')

        except Exception as e:
            messages.error(request, f'Error general: {str(e)}')

    context = {'actividades': actividades, 'fecha_hoy': fecha_hoy, 'resultados': resultados}
    return render(request, 'registrar_asistencia.html', context)




#########codigo no funcionando:
def gestion_asistencia(request):
    """Vista principal para gestión de asistencias"""
    # Obtener parámetros de filtro
    fecha_filtro = request.GET.get('fecha', timezone.now().date().strftime('%Y-%m-%d'))
    actividad_filtro = request.GET.get('actividad', '')
    estado_filtro = request.GET.get('estado', '')
   
    # Convertir la fecha a datetime con zona horaria activa
    fecha_obj = datetime.strptime(fecha_filtro, '%Y-%m-%d')
    fecha_aware = timezone.make_aware(fecha_obj)


    asistencias_query = Asistencias.objects.select_related(
    'participaciones_id_participacion__participantes_id_participante',
    'participaciones_id_participacion__actividades_id_actividad',
    'estados_asistencia_id_estado_asistencia'
    ).filter(fecha__date=fecha_aware.date())
 
    # Aplicar filtros
    if actividad_filtro:
        asistencias_query = asistencias_query.filter(
            participaciones_id_participacion__actividades_id_actividad_id=actividad_filtro
        )
   
    if estado_filtro:
        asistencias_query = asistencias_query.filter(
            estados_asistencia_id_estado_asistencia_id=estado_filtro
        )
   
    # Paginación
    paginator = Paginator(asistencias_query.order_by('-id_asistencia'), 20)
    page_number = request.GET.get('page')
    asistencias = paginator.get_page(page_number)
   
    # CAMBIO AQUÍ: Obtener TODAS las actividades, no solo las que tienen asistencias en esta fecha
    actividades = Actividades.objects.all().order_by('nombre')
   
    # Obtener todos los estados de asistencia
    estados_asistencia = EstadosAsistencia.objects.all().order_by('nombre')
   
    # Estadísticas del día
    stats = {
        'total_registros': asistencias_query.count(),
        'presentes': asistencias_query.filter(
            estados_asistencia_id_estado_asistencia__nombre__icontains='presente'
        ).count(),
        'ausentes': asistencias_query.filter(
            estados_asistencia_id_estado_asistencia__nombre__icontains='ausente'
        ).count(),
        'tardios': asistencias_query.filter(
            estados_asistencia_id_estado_asistencia__nombre__icontains='tardio'
        ).count(),
    }
   
    # Agregar variable para template
    fecha_es_hoy = (fecha_obj == date.today())
   
    context = {
        'asistencias': asistencias,
        'fecha_filtro': fecha_filtro,
        'actividad_filtro': actividad_filtro,
        'estado_filtro': estado_filtro,
        'actividades': actividades,
        'estados_asistencia': estados_asistencia,
        'stats': stats,
        'fecha_obj': fecha_obj,
        'fecha_es_hoy': fecha_es_hoy,
    }
   
    return render(request, 'gestion_asistencia.html', context)

