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
    Participantes, TiposActividad, Roles, Citas, ProyectosSociales, Equipos,EstadosAsistencia
)

LOG_DIR = os.path.join("Analytics_Reports","logs", "emails")
LOG_EMAILS_FILE = os.path.join(LOG_DIR, "log_emails.txt")

def is_admin(user):
    return user.is_authenticated and user.is_staff

def analytics_index(request):
    return render(request, "index.html")

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

 
def participantes_list(request):
    participantes = Participantes.objects.all().order_by("nombre")
    return render(request, "participantes.html", {"participantes": participantes})


def comparaciones(request):
    tiempo = request.GET.get("tiempo", "todos")
    agrupacion = request.GET.get("agrupacion", "facultad")
    semestre_filtro = request.GET.get("semestre_filtro", "")
    
    resultados = []
    
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
    
    # Obtener lista de semestres disponibles desde la base de datos
    semestres_disponibles = (
        Participantes.objects
        .values_list('semestre', flat=True)
        .distinct()
        .order_by('semestre')
    )
    # Filtrar valores nulos y convertir a lista
    semestres_disponibles = [s for s in semestres_disponibles if s is not None]
    
    metricas = {
        "total_asistencias": total_asistencias,
        "nuevos": nuevos,
        "reincidencia": reincidencia,
    }
    
    context = {
        "tiempo": tiempo,
        "agrupacion": agrupacion,
        "semestre_filtro": semestre_filtro,
        "semestres_disponibles": semestres_disponibles,
        "resultados": resultados,
        "metricas": metricas,
    }
    
    return render(request, "comparaciones.html", context)








 # views.py - Sistema completo de recomendaciones  
 #######################################################
 #######################################################
 #######################################################
 #######################################################
 #######################################################


def obtener_estudiantes_activos(dias_actividad=14):
    """
    Devuelve estudiantes que han tenido al menos una asistencia en los últimos `dias_actividad` días.
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

def log_email(destinatarios, asunto):
    """Guarda en un TXT los destinatarios y el asunto del correo enviado"""
    
    # Crea el directorio si no existe
    os.makedirs(LOG_DIR, exist_ok=True)

    # Abre el archivo en modo append y guarda la línea
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

def recomendaciones(request):
    """Vista principal para mostrar recomendaciones automáticas"""
    poca_asistencia = obtener_estudiantes_poca_asistencia()
    proximos_reconocimientos = obtener_proximos_reconocimientos()
    estudiantes_inactivos = obtener_estudiantes_inactivos()
    estudiantes_destacados = obtener_estudiantes_destacados()
    alertas_riesgo = obtener_alertas_riesgo()
    estudiantes_activos = obtener_estudiantes_activos()  
    context = {
        'poca_asistencia': poca_asistencia,
        'proximos_reconocimientos': proximos_reconocimientos,
        'estudiantes_inactivos': estudiantes_inactivos,
        'estudiantes_destacados': estudiantes_destacados,
        'alertas_riesgo': alertas_riesgo,
        'estudiantes_activos': estudiantes_activos, 
        'fecha_actualizacion': timezone.now()
    }
    
    if request.GET.get('enviar_notificaciones'):
        enviar_notificaciones_automaticas(context)
        messages.success(request, 'Notificaciones enviadas correctamente.')
    
    return render(request, "recomendaciones.html", context)

def obtener_estudiantes_poca_asistencia(umbral_asistencias=3):
    return (
        Participaciones.objects
        .annotate(total_asistencias=Count('asistencias'))
        .filter(total_asistencias__lt=umbral_asistencias)
        .select_related('participantes_id_participante', 'actividades_id_actividad')
        .order_by('total_asistencias')
    )

def obtener_proximos_reconocimientos():
    return (
        Participaciones.objects
        .annotate(
            total_asistencias=Count('asistencias', distinct=True),
            asistencias_faltantes=ExpressionWrapper(
                10 - Count('asistencias', distinct=True),
                output_field=IntegerField()
            )
        )
        .filter(total_asistencias__gte=8, total_asistencias__lt=10)
        .select_related('participantes_id_participante', 'actividades_id_actividad')
        .order_by('-total_asistencias')
    )







def obtener_estudiantes_inactivos(dias_inactividad=14):
    fecha_limite = timezone.now().date() - timedelta(days=dias_inactividad)
    return (
        Participaciones.objects
        .annotate(
            asistencias_recientes=Count(
                'asistencias',
                filter=Q(asistencias__fecha__gte=fecha_limite),
                distinct=True
            )
        )
        .filter(asistencias_recientes=0)
        .select_related('participantes_id_participante', 'actividades_id_actividad')
    )

def obtener_estudiantes_destacados():
    return (
        Participaciones.objects
        .annotate(total_asistencias=Count('asistencias'))
        .filter(total_asistencias__gte=15)
        .select_related('participantes_id_participante', 'actividades_id_actividad')
        .order_by('-total_asistencias')
    )

def obtener_alertas_riesgo():
    fecha_limite = timezone.now().date() - timedelta(days=7)
    return (
        Participaciones.objects
        .annotate(
            asistencias_recientes=Count(
                'asistencias',
                filter=Q(asistencias__fecha__gte=fecha_limite),
                distinct=True
            ),
            total_asistencias=Count('asistencias')
        )
        .filter(Q(asistencias_recientes=0) & Q(total_asistencias__lt=5))
        .select_related('participantes_id_participante', 'actividades_id_actividad')
    )

def enviar_notificaciones_automaticas(context):
    """Envía notificaciones automáticas por email"""
    if context['poca_asistencia']:
        enviar_alerta_poca_asistencia(context['poca_asistencia'])
    if context['proximos_reconocimientos']:
        enviar_notificacion_reconocimientos(context['proximos_reconocimientos'])
    if context['estudiantes_inactivos']:
        enviar_alerta_inactividad(context['estudiantes_inactivos'])

def enviar_alerta_poca_asistencia(estudiantes):
    """Envía alertas por poca asistencia al staff"""
    asunto = f"Alerta: {len(estudiantes)} estudiantes con baja asistencia"
    mensaje = "Estudiantes que requieren intervención por baja asistencia:\n\n"
    for est in estudiantes:
        mensaje += f"• {est.participantes_id_participante.nombre} {est.participantes_id_participante.apellido} - {est.total_asistencias} asistencias\n"
        mensaje += f"  Actividad: {est.actividades_id_actividad.nombre}\n\n"
    enviar_email_staff(asunto, mensaje)

def enviar_notificacion_reconocimientos(estudiantes):
    """Envía notificaciones sobre reconocimientos próximos a los participantes (por correo)."""
    for est in estudiantes:
        nombre_completo = f"{est.participantes_id_participante.nombre} {est.participantes_id_participante.apellido}"
        asunto = f"¡Estás cerca de un reconocimiento, {est.participantes_id_participante.nombre}!"
        mensaje = f"""
Hola {nombre_completo},
¡Felicidades! Tienes {est.total_asistencias} asistencias en {est.actividades_id_actividad.nombre}.
Solo necesitas {10 - est.total_asistencias} más para obtener tu reconocimiento.

¡Sigue así!
"""
        correo = est.participantes_id_participante.correo
        if correo:
            enviar_email(asunto, mensaje, [correo])

def enviar_alerta_inactividad(estudiantes):
    """Envía alertas sobre estudiantes inactivos al staff"""
    asunto = f"Alerta: {len(estudiantes)} estudiantes inactivos"
    mensaje = "Estudiantes que no han asistido recientemente:\n\n"
    for est in estudiantes:
        mensaje += f"• {est.participantes_id_participante.nombre} {est.participantes_id_participante.apellido} - Actividad: {est.actividades_id_actividad.nombre}\n"
    enviar_email_staff(asunto, mensaje)

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

def configurar_notificaciones(request):
    """Permite configurar parámetros de las notificaciones automáticas"""
    if request.method == 'POST':
        configuracion = {
            'umbral_asistencia': int(request.POST.get('umbral_asistencia', 50)),
            'dias_inactividad': int(request.POST.get('dias_inactividad', 14)),
            'envio_automatico': request.POST.get('envio_automatico') == 'on',
            'frecuencia_envio': request.POST.get('frecuencia_envio', 'semanal')
        }
        messages.success(request, 'Configuración guardada correctamente.')
    return render(request, 'configurar_notificaciones.html')

 #######################################################
 #######################################################
 #######################################################
 #######################################################
 #######################################################
 #######################################################
 #######################################################









def gestion_asistencia(request):
    """Vista principal para gestión de asistencias"""
    
    # Obtener parámetros de filtro
    fecha_filtro = request.GET.get('fecha', timezone.now().date().strftime('%Y-%m-%d'))
    actividad_filtro = request.GET.get('actividad', '')
    participante_filtro = request.GET.get('participante', '')
    estado_filtro = request.GET.get('estado', '')
    
    # Convertir fecha string a objeto date
    try:
        fecha_obj = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
    except ValueError:
        fecha_obj = timezone.now().date()
    
    # Query base de asistencias
    asistencias_query = Asistencias.objects.select_related(
        'participaciones_id_participacion__participantes_id_participante',
        'participaciones_id_participacion__actividades_id_actividad',
        'estados_asistencia_id_estado_asistencia'
    ).filter(fecha=fecha_obj)
    
    # Aplicar filtros
    if actividad_filtro:
        asistencias_query = asistencias_query.filter(
            participaciones_id_participacion__actividades_id_actividad_id=actividad_filtro
        )
    
    if participante_filtro:
        asistencias_query = asistencias_query.filter(
            participaciones_id_participacion__participantes_id_participante__nombre__icontains=participante_filtro
        )
    
    if estado_filtro:
        asistencias_query = asistencias_query.filter(
            estados_asistencia_id_estado_asistencia_id=estado_filtro
        )
    
    # Paginación
    paginator = Paginator(asistencias_query.order_by('-id_asistencia'), 20)
    page_number = request.GET.get('page')
    asistencias = paginator.get_page(page_number)
    
    # Obtener datos para filtros
    actividades = Actividades.objects.filter(
        participaciones__asistencias__fecha=fecha_obj
    ).distinct().order_by('nombre')
    
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
        'participante_filtro': participante_filtro,
        'estado_filtro': estado_filtro,
        'actividades': actividades,
        'estados_asistencia': estados_asistencia,
        'stats': stats,
        'fecha_obj': fecha_obj,
        'fecha_es_hoy': fecha_es_hoy,  # <-- variable booleana para JS/template
    }
    
    return render(request, 'gestion_asistencia.html', context)

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

def historial_participante(request, participante_id):
    """Vista para mostrar historial completo de un participante"""
    
    participante = get_object_or_404(Participantes, id_participante=participante_id)
    
    # Obtener todas las participaciones del estudiante
    participaciones = Participaciones.objects.filter(
        participantes_id_participante=participante
    ).select_related('actividades_id_actividad').order_by('-fecha_inscripcion')
    
    # Obtener historial de asistencias por participación
    historial_data = []
    
    for participacion in participaciones:
        asistencias = Asistencias.objects.filter(
            participaciones_id_participacion=participacion
        ).select_related('estados_asistencia_id_estado_asistencia').order_by('-fecha')
        
        # Estadísticas de la participación
        total_asistencias = asistencias.count()
        presentes = asistencias.filter(
            estados_asistencia_id_estado_asistencia__nombre__icontains='presente'
        ).count()
        
        porcentaje_asistencia = (presentes * 100 / total_asistencias) if total_asistencias > 0 else 0
        
        historial_data.append({
            'participacion': participacion,
            'asistencias': asistencias[:10],  # Últimas 10 asistencias
            'total_asistencias': total_asistencias,
            'presentes': presentes,
            'porcentaje': round(porcentaje_asistencia, 1)
        })
    
    # Obtener notas del historial
    notas_historial = HistorialParticipaciones.objects.filter(
        participaciones_id_participacion__in=participaciones
    ).order_by('-fecha')[:20]  # Últimas 20 notas
    
    context = {
        'participante': participante,
        'historial_data': historial_data,
        'notas_historial': notas_historial,
        'total_participaciones': participaciones.count()
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

    actividades = Actividades.objects.all().order_by('nombre')
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
                            'id_participante': user,  # Vincular con el ID del usuario
                            'nombre': f"Usuario {cedula}",
                            'apellido': '',
                            'roles_id_rol_id': 1,  # Rol por defecto
                            'estado_activo': 'S',  # Activo
                            'user': user  # Vincular al modelo User
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
                            'roles_participacion_id_rol_participacion_id': 1,
                            'estados_participacion_id_estado_participacion_id': 1
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
            messages.error(request, f'Error: {str(e)}')

    context = {'actividades': actividades, 'fecha_hoy': fecha_hoy, 'resultados': resultados}
    return render(request, 'registrar_asistencia.html', context)