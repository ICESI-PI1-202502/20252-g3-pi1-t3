#project\Analytics_Reports\views.py
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
    RolesParticipacion,EstadosParticipacion, Torneos, Disciplinas, EstadosTorneo, TorneosEquipos, EquiposParticipantes
)

# Agregar estos imports al inicio de views.py si no están presentes
from django.db.models import (
    Count, Avg, Q, F, Case, When, IntegerField, Max, 
    ExpressionWrapper, FloatField  # ← AÑADIR FloatField
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

# ========== FUNCIONES CORREGIDAS - AGRUPADAS POR ESTUDIANTE ==========

def obtener_alertas_riesgo():
    """
    RIESGO CRÍTICO: Agrupa por estudiante, lista sus actividades en riesgo
    """
    config = ConfiguracionNotificaciones.obtener_config()


    # ✅ USAR timezone.now() en lugar de datetime.now()
    fecha_limite = timezone.now().date() - timedelta(days=config.dias_riesgo_critico)
     
    # Obtener participaciones en riesgo
    participaciones = (
        Participaciones.objects
        .annotate(
            total_asistencias=Count('asistencias', distinct=True),
            ultima_asistencia=Max('asistencias__fecha')
        )
        .filter(total_asistencias__lte=config.umbral_riesgo_critico)
        .filter(
            Q(ultima_asistencia__lt=fecha_limite) | Q(ultima_asistencia__isnull=True)
        )
        .select_related('participantes_id_participante', 'actividades_id_actividad')
    )
    
    # Agrupar por estudiante
    estudiantes_riesgo = {}
    for part in participaciones:
        estudiante_id = part.participantes_id_participante.id_participante
        
        if estudiante_id not in estudiantes_riesgo:
            estudiantes_riesgo[estudiante_id] = {
                'participante': part.participantes_id_participante,
                'actividades': [],
                'total_asistencias_minimas': 999,
            }
        
        estudiantes_riesgo[estudiante_id]['actividades'].append({
            'nombre': part.actividades_id_actividad.nombre,
            'asistencias': part.total_asistencias,
            'ultima_fecha': part.ultima_asistencia
        })
        
        # Guardar la menor cantidad de asistencias
        if part.total_asistencias < estudiantes_riesgo[estudiante_id]['total_asistencias_minimas']:
            estudiantes_riesgo[estudiante_id]['total_asistencias_minimas'] = part.total_asistencias
    
    return list(estudiantes_riesgo.values())


def obtener_estudiantes_poca_asistencia():
    """
    BAJA ASISTENCIA: Agrupa por estudiante
    """
    config = ConfiguracionNotificaciones.obtener_config()
    fecha_limite_actividad = timezone.now().date() - timedelta(days=21)
    
    participaciones = (
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
    )
    
    estudiantes_baja = {}
    for part in participaciones:
        estudiante_id = part.participantes_id_participante.id_participante
        
        if estudiante_id not in estudiantes_baja:
            estudiantes_baja[estudiante_id] = {
                'participante': part.participantes_id_participante,
                'actividades': [],
                'total_participaciones': 0,
            }
        
        estudiantes_baja[estudiante_id]['actividades'].append({
            'nombre': part.actividades_id_actividad.nombre,
            'asistencias': part.total_asistencias,
        })
        estudiantes_baja[estudiante_id]['total_participaciones'] += part.total_asistencias
    
    return list(estudiantes_baja.values())


def obtener_estudiantes_inactivos():
    """
    INACTIVOS: Agrupa por estudiante
    """
    config = ConfiguracionNotificaciones.obtener_config()
    fecha_limite = timezone.now().date() - timedelta(days=config.dias_inactividad)
    
    participaciones = (
        Participaciones.objects
        .annotate(
            total_asistencias=Count('asistencias', distinct=True),
            ultima_asistencia=Max('asistencias__fecha')
        )
        .filter(total_asistencias__gte=config.umbral_baja_asistencia)
        .filter(
            Q(ultima_asistencia__lt=fecha_limite) | Q(ultima_asistencia__isnull=True)
        )
        .select_related('participantes_id_participante', 'actividades_id_actividad')
    )
    
    estudiantes_inactivos = {}
    for part in participaciones:
        estudiante_id = part.participantes_id_participante.id_participante
        
        if estudiante_id not in estudiantes_inactivos:
            estudiantes_inactivos[estudiante_id] = {
                'participante': part.participantes_id_participante,
                'actividades': [],
                'dias_inactivo': 0,
            }
        
        estudiantes_inactivos[estudiante_id]['actividades'].append({
            'nombre': part.actividades_id_actividad.nombre,
            'ultima_asistencia': part.ultima_asistencia,
        })
        
        # Calcular días de inactividad
        if part.ultima_asistencia:
            if isinstance(part.ultima_asistencia, datetime):
                fecha_ultima = part.ultima_asistencia.date()
            else:
                fecha_ultima = part.ultima_asistencia

            dias = (timezone.now().date() - fecha_ultima).days
            
            if dias > estudiantes_inactivos[estudiante_id]['dias_inactivo']:
                estudiantes_inactivos[estudiante_id]['dias_inactivo'] = dias
    
    return list(estudiantes_inactivos.values())


def obtener_proximos_reconocimientos():
    """
    PRÓXIMOS A RECONOCIMIENTO: Agrupa por estudiante
    """
    config = ConfiguracionNotificaciones.obtener_config()
    meta = config.asistencias_reconocimiento
    margen = config.margen_proximo_reconocimiento
    
    participaciones = (
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
    )
    
    estudiantes_proximos = {}
    for part in participaciones:
        estudiante_id = part.participantes_id_participante.id_participante
        
        if estudiante_id not in estudiantes_proximos:
            estudiantes_proximos[estudiante_id] = {
                'participante': part.participantes_id_participante,
                'actividades': [],
                'menor_faltante': 999,
            }
        
        estudiantes_proximos[estudiante_id]['actividades'].append({
            'nombre': part.actividades_id_actividad.nombre,
            'asistencias': part.total_asistencias,
            'faltantes': part.asistencias_faltantes,
        })
        
        if part.asistencias_faltantes < estudiantes_proximos[estudiante_id]['menor_faltante']:
            estudiantes_proximos[estudiante_id]['menor_faltante'] = part.asistencias_faltantes
    
    return list(estudiantes_proximos.values())


def obtener_estudiantes_destacados():
    """
    DESTACADOS: Agrupa por estudiante
    """
    config = ConfiguracionNotificaciones.obtener_config()
    
    participaciones = (
        Participaciones.objects
        .annotate(total_asistencias=Count('asistencias', distinct=True))
        .filter(total_asistencias__gte=config.asistencias_destacado)
        .select_related('participantes_id_participante', 'actividades_id_actividad')
    )
    
    estudiantes_destacados = {}
    for part in participaciones:
        estudiante_id = part.participantes_id_participante.id_participante
        
        if estudiante_id not in estudiantes_destacados:
            estudiantes_destacados[estudiante_id] = {
                'participante': part.participantes_id_participante,
                'actividades': [],
                'total_asistencias': 0,
            }
        
        estudiantes_destacados[estudiante_id]['actividades'].append({
            'nombre': part.actividades_id_actividad.nombre,
            'asistencias': part.total_asistencias,
        })
        estudiantes_destacados[estudiante_id]['total_asistencias'] += part.total_asistencias
    
    return list(estudiantes_destacados.values())



def obtener_estudiantes_activos(dias_actividad=14):
    """
    ACTIVOS: Estudiantes con actividad reciente (agrupados por estudiante)
    """
    fecha_limite = timezone.now().date() - timedelta(days=dias_actividad)
    
    participaciones = (
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
    )
    
    estudiantes_activos = {}
    for part in participaciones:
        estudiante_id = part.participantes_id_participante.id_participante
        
        if estudiante_id not in estudiantes_activos:
            estudiantes_activos[estudiante_id] = {
                'participante': part.participantes_id_participante,
                'actividades': [],
                'total_asistencias_recientes': 0,
            }
        
        estudiantes_activos[estudiante_id]['actividades'].append({
            'nombre': part.actividades_id_actividad.nombre,
            'asistencias_recientes': part.asistencias_recientes,
        })
        estudiantes_activos[estudiante_id]['total_asistencias_recientes'] += part.asistencias_recientes
    
    return list(estudiantes_activos.values())


  

# ========== VISTA PRINCIPAL ACTUALIZADA ==========
# Analytics_Reports/views.py

def recomendaciones(request):
    """Vista principal con estudiantes únicos - SIN envío manual"""
    
    alertas_riesgo = obtener_alertas_riesgo()
    poca_asistencia = obtener_estudiantes_poca_asistencia()
    estudiantes_inactivos = obtener_estudiantes_inactivos()
    proximos_reconocimientos = obtener_proximos_reconocimientos()
    estudiantes_destacados = obtener_estudiantes_destacados()
    estudiantes_activos = obtener_estudiantes_activos()
    
    # ELIMINAR ESTE BLOQUE COMPLETO:
    # if request.GET.get('enviar_notificaciones') == '1':
    #     ... todo el código de envío manual ...
    
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

def configurar_notificaciones(request):
    """Permite configurar parámetros de las notificaciones automáticas"""
    config = ConfiguracionNotificaciones.obtener_config()
    
    if request.method == 'POST':
        try:
            # ========== DEBUG: Imprimir todos los valores POST ==========
            print("=== DATOS POST RECIBIDOS ===")
            for key, value in request.POST.items():
                print(f"{key}: {value}")
            print("============================")
            
            # ========== RECONOCIMIENTOS ==========
            config.asistencias_reconocimiento = int(request.POST.get('asistencias_reconocimiento', 10))
            config.margen_proximo_reconocimiento = int(request.POST.get('margen_proximo_reconocimiento', 2))
            config.asistencias_destacado = int(request.POST.get('asistencias_destacado', 15))
            
            # DEBUG: Verificar valores antes de guardar
            print(f"\n=== VALORES ANTES DE GUARDAR ===")
            print(f"asistencias_reconocimiento: {config.asistencias_reconocimiento}")
            print(f"margen_proximo_reconocimiento: {config.margen_proximo_reconocimiento}")
            print(f"asistencias_destacado: {config.asistencias_destacado}")
            
            # ========== CLASIFICACIÓN ==========
            config.umbral_baja_asistencia = int(request.POST.get('umbral_baja_asistencia', 5))
            config.umbral_riesgo_critico = int(request.POST.get('umbral_riesgo_critico', 2))
            config.dias_inactividad = int(request.POST.get('dias_inactividad', 14))
            config.dias_riesgo_critico = int(request.POST.get('dias_riesgo_critico', 21))
            
            # ========== ENCUESTAS ==========
            config.asistencias_minimas_encuesta = int(request.POST.get('asistencias_minimas_encuesta', 3))
            config.dias_despues_cierre_encuesta = int(request.POST.get('dias_despues_cierre_encuesta', 3))
            
            # ========== GENERAL ==========
            config.envio_automatico = request.POST.get('envio_automatico') == 'on'
            config.frecuencia_envio = request.POST.get('frecuencia_envio', 'semanal')
            
            # ========== VALIDACIONES ==========
            if config.asistencias_destacado <= config.asistencias_reconocimiento:
                messages.error(request, f'⚠️ El umbral de destacado ({config.asistencias_destacado}) debe ser mayor al de reconocimiento ({config.asistencias_reconocimiento})')
                return render(request, 'configurar_notificaciones.html', {'config': config})
            
            if config.umbral_baja_asistencia <= config.umbral_riesgo_critico:
                messages.error(request, '⚠️ El umbral de baja asistencia debe ser mayor al de riesgo crítico')
                return render(request, 'configurar_notificaciones.html', {'config': config})
            
            # ========== GUARDAR CON VERIFICACIÓN ==========
            config.save()
            
            # DEBUG: Verificar que se guardó correctamente
            config.refresh_from_db()
            print(f"\n=== VALORES DESPUÉS DE GUARDAR ===")
            print(f"asistencias_reconocimiento: {config.asistencias_reconocimiento}")
            print(f"margen_proximo_reconocimiento: {config.margen_proximo_reconocimiento}")
            print(f"asistencias_destacado: {config.asistencias_destacado}")
            print("==================================\n")
            
            ###messages.success(request, '✅ Configuración guardada correctamente.')
            return redirect('Analytics_Reports:configurar_notificaciones')
            
        except ValueError as e:
            messages.error(request, f'❌ Error en los valores: {str(e)}')
            print(f"ERROR ValueError: {str(e)}")
        except Exception as e:
            messages.error(request, f'❌ Error al guardar: {str(e)}')
            print(f"ERROR Exception: {str(e)}")
            import traceback
            traceback.print_exc()
    
    return render(request, 'configurar_notificaciones.html', {'config': config})

def is_admin(user):
    return user.is_authenticated and user.is_staff

def analytics_index(request):
    return render(request, "index.html")










#Fin de recomendaciones
################333
##################33
####################






import csv
import json
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Count, Min, Max, Avg
 
# === ROLES DEL SISTEMA (solo usuarios reales) ===
ROLES_SISTEMA = ['Estudiante', 'Trabajador', 'Egresado', 'Invitado']

def analisis_comportamiento(request):
    # === FILTROS (sin min_frecuencia) ===
    tipo_actividad   = request.GET.get("tipo_actividad")
    export           = request.GET.get("export")
    mostrar_todos    = request.GET.get("mostrar_todos")
    rol_filtro       = request.GET.get("rol")
    facultad_filtro  = request.GET.get("facultad")
    genero_filtro    = request.GET.get("genero")
    semestre_filtro  = request.GET.get("semestre")

    # === NUEVOS FILTROS – TORNEOS ===
    torneo_nombre_q     = request.GET.get("torneo_nombre")       # texto libre
    torneo_disciplina_q = request.GET.get("torneo_disciplina")   # id_disciplina
    torneo_estado_q     = request.GET.get("torneo_estado")       # id_estado_torneo
    mostrar_todos_torneos = request.GET.get("mostrar_todos_torneos")

    # has_filters para ACTIVIDADES + (ahora) TORNEOS
    has_filters_actividades = bool(
        tipo_actividad or mostrar_todos or
        rol_filtro or facultad_filtro or genero_filtro or semestre_filtro
    )
    torneos_has_filters = bool(
        mostrar_todos_torneos or torneo_nombre_q or torneo_disciplina_q or torneo_estado_q
    )
    # Para activar el bloque de cálculo aunque solo haya filtros de torneos:
    has_filters = has_filters_actividades or torneos_has_filters

    # Datos para gráficos (Actividades)
    datos_grafico_frecuencia = []
    datos_grafico_roles = []
    datos_grafico_facultades = []
    datos_grafico_tipos_actividad = []
    datos_grafico_reincidencia = []
    datos_grafico_dias_semana = [] 
    
    data = None
    facultades_unicas = 0
    roles_unicos = 0
    tipos_actividad_unicos = 0

    # === MÉTRICAS RF4.1 (Actividades) ===
    total_participaciones = 0
    promedio_participaciones = 0
    porcentaje_reincidencia = 0
    total_nuevos = 0

    # ============================================
    # NUEVO: Resolver filtros de TORNEOS -> participantes
    # ============================================
    torneos_data = None
    torneos_count = 0
    participante_ids_from_torneos = None  # None: no aplicar; []: aplica y vacía

    if torneos_has_filters:
        torneos_qs = (
            Torneos.objects
            .select_related("disciplinas_id_disciplina", "estados_torneo_id_estado_torneo")
            .order_by("-fecha_inicio")
        )
        if torneo_nombre_q:
            torneos_qs = torneos_qs.filter(nombre__icontains=torneo_nombre_q.strip())
        if torneo_disciplina_q:
            torneos_qs = torneos_qs.filter(disciplinas_id_disciplina__id_disciplina=torneo_disciplina_q)
        if torneo_estado_q:
            torneos_qs = torneos_qs.filter(estados_torneo_id_estado_torneo__id_estado_torneo=torneo_estado_q)

        # Para mostrar listado en la UI
        torneos_data = list(
            torneos_qs.values(
                "id_torneo", "nombre",
                "disciplinas_id_disciplina__nombre",
                "estados_torneo_id_estado_torneo__nombre",
                "fecha_inicio", "fecha_fin",
            )
        )
        torneos_count = len(torneos_data)

        # Encadenar: torneos -> equipos -> participantes
        torneo_ids = list(torneos_qs.values_list("id_torneo", flat=True))
        equipo_ids = list(
            TorneosEquipos.objects
            .filter(torneos_id_torneo_id__in=torneo_ids)
            .values_list("equipos_id_equipo_id", flat=True)
            .distinct()
        )
        participante_ids_from_torneos = list(
            EquiposParticipantes.objects
            .filter(equipos_id_equipo_id__in=equipo_ids)
            .values_list("participantes_id_participante_id", flat=True)
            .distinct()
        )

    # ============================================
    # BLOQUE ACTUAL: ACTIVIDADES / PARTICIPACIONES
    # ============================================
    if has_filters or export:
        # Base: participaciones por usuario
        queryset = Participaciones.objects.values(
            "participantes_id_participante__nombre",
            "participantes_id_participante__correo",
            "participantes_id_participante__semestre",
            "participantes_id_participante__facultad",
            "participantes_id_participante__genero",
            "participantes_id_participante__roles_id_rol__nombre_rol",
            "participantes_id_participante",
            #"actividades_id_actividad__tipos_actividad_id_tipo__nombre_tipo",
        ).annotate(
            total=Count("id_participacion"),
            primera_participacion=Min("fecha_inscripcion"),
            ultima_participacion=Max("fecha_inscripcion")
        ).order_by("-total")

        # === FILTRAR SOLO ROLES DEL SISTEMA ===
        queryset = queryset.filter(
            participantes_id_participante__roles_id_rol__nombre_rol__in=ROLES_SISTEMA
        )



        # Aplicar filtros del usuario (SIN min_frecuencia)
        if tipo_actividad:
            queryset = queryset.filter(
                actividades_id_actividad__tipos_actividad_id_tipo__id_tipo=tipo_actividad
            )
        if rol_filtro:
            queryset = queryset.filter(
                participantes_id_participante__roles_id_rol__id_rol=rol_filtro
            )
        if facultad_filtro:
            queryset = queryset.filter(
                participantes_id_participante__facultad=facultad_filtro
            )
        if genero_filtro:
            queryset = queryset.filter(
                participantes_id_participante__genero=genero_filtro
            )
        if semestre_filtro:
            queryset = queryset.filter(
                participantes_id_participante__semestre=semestre_filtro
            )

        data = list(queryset)

        # ✅ SOLUCIÓN: Para cada participante, obtener sus actividades Y tipos
        for item in data:
            participante_id = item['participantes_id_participante']
            
            # Obtener todas las participaciones del participante
            participaciones_usuario = Participaciones.objects.filter(
                participantes_id_participante_id=participante_id
            ).select_related('actividades_id_actividad__tipos_actividad_id_tipo')
            
            # Aplicar el mismo filtro de tipo_actividad si existe
            if tipo_actividad:
                participaciones_usuario = participaciones_usuario.filter(
                    actividades_id_actividad__tipos_actividad_id_tipo__id_tipo=tipo_actividad
                )
            
            # Obtener nombres de actividades
            actividades_info = []
            tipos_set = set()
            
            for part in participaciones_usuario:
                actividad = part.actividades_id_actividad
                actividades_info.append(actividad.nombre)
                
                # Agregar tipo si existe
                if actividad.tipos_actividad_id_tipo:
                    tipos_set.add(actividad.tipos_actividad_id_tipo.nombre_tipo)
            
            # Agregar al item
            item['actividades_lista'] = list(set(actividades_info))  # Únicos
            item['actividades_texto'] = ', '.join(sorted(set(actividades_info))) if actividades_info else 'Ninguna'
            item['tipos_actividad_texto'] = ', '.join(sorted(tipos_set)) if tipos_set else 'Sin tipo'

        # === ESTADÍSTICAS ÚNICAS (para cards de resumen) ===
        if data:
            facultades_unicas = len({
                item.get("participantes_id_participante__facultad")
                for item in data
                if item.get("participantes_id_participante__facultad")
            })
            roles_unicos = len({
                item.get("participantes_id_participante__roles_id_rol__nombre_rol")
                for item in data
                if item.get("participantes_id_participante__roles_id_rol__nombre_rol")
            })
            tipos_actividad_unicos = len({
                item.get("actividades_id_actividad__tipos_actividad_id_tipo__nombre_tipo")
                for item in data
                if item.get("actividades_id_actividad__tipos_actividad_id_tipo__nombre_tipo")
            })

            total_participaciones = sum(item["total"] for item in data)
            participantes_unicos_count = len({
                item["participantes_id_participante"] for item in data
            })
            promedio_participaciones = (
                round(total_participaciones / participantes_unicos_count, 1)
                if participantes_unicos_count > 0 else 0
            )

        # === REINCIDENCIA: nuevos vs reincidentes
        participantes_unicos = {item["participantes_id_participante"] for item in (data or [])}
        nuevos = reincidentes = 0
        for p_id in participantes_unicos:
            count = Participaciones.objects.filter(participantes_id_participante_id=p_id).count()
            if count > 1:
                reincidentes += 1
            else:
                nuevos += 1
        total_nuevos = nuevos
        porcentaje_reincidencia = (
            round((reincidentes / len(participantes_unicos) * 100), 1)
            if participantes_unicos else 0
        )

        # === GRÁFICO: Frecuencia de participación
        freq = {"Alta": 0, "Media": 0, "Baja": 0}
        for item in (data or []):
            t = item["total"]
            if t >= 5:
                freq["Alta"] += 1
            elif t >= 2:
                freq["Media"] += 1
            else:
                freq["Baja"] += 1
        datos_grafico_frecuencia = [
            {"label": "Alta (5+)", "value": freq["Alta"]},
            {"label": "Media (2–4)", "value": freq["Media"]},
            {"label": "Baja (1)",   "value": freq["Baja"]},
        ]

        # === GRÁFICO: Roles
        roles_count = {}
        for item in (data or []):
            rol = item.get("participantes_id_participante__roles_id_rol__nombre_rol", "Sin rol")
            roles_count[rol] = roles_count.get(rol, 0) + 1
        datos_grafico_roles = [
            {"label": rol.title(), "value": count}
            for rol, count in sorted(roles_count.items(), key=lambda x: x[1], reverse=True)
        ]

        # === GRÁFICO: Facultades (top 10)
        fac_count = {}
        for item in (data or []):
            fac = item.get("participantes_id_participante__facultad", "No especificada")
            if fac and fac != "No especificada":
                fac_count[fac] = fac_count.get(fac, 0) + 1
        datos_grafico_facultades = [
            {"label": fac, "value": count}
            for fac, count in sorted(fac_count.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        # === GRÁFICO: Tipos de actividad - RF4.2 ===
        # ✅ GRÁFICO: Tipos de actividad - CORREGIDO
        tipos_count = {}
        
        for item in data:
                tipos_texto = item.get('tipos_actividad_texto', '')
                if tipos_texto and tipos_texto != 'Sin tipo':
                    # Dividir por comas si hay múltiples tipos
                    tipos_lista = [t.strip() for t in tipos_texto.split(',')]
                    for tipo in tipos_lista:
                        tipos_count[tipo] = tipos_count.get(tipo, 0) + 1

        datos_grafico_tipos_actividad = [
            {"label": tipo, "value": count}
            for tipo, count in sorted(tipos_count.items(), key=lambda x: x[1], reverse=True)
        ]

        # === GRÁFICO: Reincidencia
        datos_grafico_reincidencia = [
            {"label": "Nuevos",       "value": nuevos},
            {"label": "Reincidentes", "value": reincidentes},
        ]


        # === NUEVO: DÍAS DE LA SEMANA ===
        asistencias_query = Asistencias.objects.filter(
            participaciones_id_participacion__participantes_id_participante__in=participantes_unicos,
            estados_asistencia_id_estado_asistencia__nombre__icontains='presente'
        )
        
        # Aplicar los mismos filtros
        if tipo_actividad:
            asistencias_query = asistencias_query.filter(
                participaciones_id_participacion__actividades_id_actividad__tipos_actividad_id_tipo__id_tipo=tipo_actividad
            )
        if rol_filtro:
            asistencias_query = asistencias_query.filter(
                participaciones_id_participacion__participantes_id_participante__roles_id_rol__id_rol=rol_filtro
            )
        if facultad_filtro:
            asistencias_query = asistencias_query.filter(
                participaciones_id_participacion__participantes_id_participante__facultad=facultad_filtro
            )
        if genero_filtro:
            asistencias_query = asistencias_query.filter(
                participaciones_id_participacion__participantes_id_participante__genero=genero_filtro
            )
        if semestre_filtro:
            asistencias_query = asistencias_query.filter(
                participaciones_id_participacion__participantes_id_participante__semestre=semestre_filtro
            )
        
        # Agrupar por día de la semana
        asistencias_por_dia = asistencias_query.annotate(
            dia_semana=ExtractWeekDay('fecha')
        ).values('dia_semana').annotate(
            total=Count('id_asistencia')
        ).order_by('dia_semana')
        
        # Mapeo de números a nombres
        dias_nombres = {
            1: 'Domingo', 2: 'Lunes', 3: 'Martes', 4: 'Miércoles',
            5: 'Jueves', 6: 'Viernes', 7: 'Sábado'
        }
        
        # Inicializar todos los días con 0
        dias_data = {dia: 0 for dia in range(1, 8)}
        
        # Llenar con datos reales
        for item in asistencias_por_dia:
            dias_data[item['dia_semana']] = item['total']
        
        # Ordenar Lunes-Domingo
        orden_dias = [2, 3, 4, 5, 6, 7, 1]
        datos_grafico_dias_semana = [
            {'label': dias_nombres[dia], 'value': dias_data[dia]}
            for dia in orden_dias
        ]

        # === EXPORTAR CSV ===
        if export == "csv":
            response = HttpResponse(content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = 'attachment; filename="estadisticas_participacion.csv"'
            response.write("\ufeff")  # BOM para Excel
            writer = csv.writer(response)
            writer.writerow([
                "Nombre", "Correo", "Semestre", "Facultad", "Género",
                "Rol", "Tipo Actividad", "Participaciones", "Frecuencia",
                "Primera vez", "Última vez",
            ])
            for item in (data or []):
                total = item["total"]
                freq_label = "Alta" if total >= 5 else "Media" if total >= 2 else "Baja"
                writer.writerow([
                    item.get("participantes_id_participante__nombre", "Anónimo"),
                    item.get("participantes_id_participante__correo", "N/A"),
                    item.get("participantes_id_participante__semestre", "N/A"),
                    item.get("participantes_id_participante__facultad", "No especificada"),
                    item.get("participantes_id_participante__genero", "No especificado"),
                    item.get("participantes_id_participante__roles_id_rol__nombre_rol", "Sin rol").title(),
                    item.get("actividades_id_actividad__tipos_actividad_id_tipo__nombre_tipo", "Otro"),
                    total,
                    freq_label,
                    item.get("primera_participacion", "N/A"),
                    item.get("ultima_participacion", "N/A"),
                ])
            return response

    # === Opciones de filtros (solo roles del sistema) ===
    tipos_actividad = TiposActividad.objects.all().order_by("nombre_tipo")
    roles = Roles.objects.filter(nombre_rol__in=ROLES_SISTEMA).order_by("nombre_rol")
    facultades = (
        Participantes.objects
        .filter(roles_id_rol__nombre_rol__in=ROLES_SISTEMA)
        .exclude(facultad__isnull=True)
        .exclude(facultad="")
        .values_list("facultad", flat=True).distinct().order_by("facultad")
    )
    generos = (
        Participantes.objects
        .filter(roles_id_rol__nombre_rol__in=ROLES_SISTEMA)
        .exclude(genero__isnull=True)
        .exclude(genero="")
        .values_list("genero", flat=True).distinct()
    )
    semestres = (
        Participantes.objects
        .filter(roles_id_rol__nombre_rol__in=ROLES_SISTEMA)
        .exclude(semestre__isnull=True)
        .values_list("semestre", flat=True).distinct().order_by("semestre")
    )

    # === Opciones de filtros – TORNEOS ===
    disciplinas_torneo = Disciplinas.objects.all().order_by("nombre")
    estados_torneo     = EstadosTorneo.objects.all().order_by("nombre")

    return render(request, "analisis.html", {
    "data": data,
    "tipos_actividad": tipos_actividad,
    "roles": roles,
    "facultades": facultades,
    "generos": generos,
    "semestres": semestres,
    "has_filters": has_filters,
    "mostrar_todos": mostrar_todos,
    # Estadísticas únicas
    "facultades_unicas": facultades_unicas,
    "roles_unicos": roles_unicos,
    "tipos_actividad_unicos": tipos_actividad_unicos,
    # === MÉTRICAS RF4.1 ===
    "total_participaciones": total_participaciones,
    "promedio_participaciones": promedio_participaciones,
    "porcentaje_reincidencia": porcentaje_reincidencia,
    "total_nuevos": total_nuevos,
    # === NUEVO: Detectar filtro de tipo actividad ===
    "tipo_actividad_filtrado": tipo_actividad,  # ← AGREGAR ESTA LÍNEA
    "tipo_actividad_nombre": TiposActividad.objects.get(id_tipo=tipo_actividad).nombre_tipo if tipo_actividad else None,  # ← AGREGAR ESTA LÍNEA
    # Gráficos
    "datos_grafico_frecuencia": json.dumps(datos_grafico_frecuencia),
    "datos_grafico_roles": json.dumps(datos_grafico_roles),
    "datos_grafico_facultades": json.dumps(datos_grafico_facultades),
    "datos_grafico_tipos_actividad": json.dumps(datos_grafico_tipos_actividad),
    "datos_grafico_reincidencia": json.dumps(datos_grafico_reincidencia),
    "datos_grafico_dias_semana": json.dumps(datos_grafico_dias_semana),  # NUEVO
 })

def participantes_list(request):
    participantes = Participantes.objects.all().order_by("nombre")
    return render(request, "participantes.html", {"participantes": participantes})
 


from django.db.models import Count, Min, Max
from django.utils.dateparse import parse_date
from datetime import datetime, date
import json

def comparaciones(request):
    """Vista mejorada con periodos intersemestrales, filtros por año y múltiples tipos de gráficas"""
    
    tipo_comparacion = request.GET.get("tipo", "periodos_semestrales")
    agrupacion = request.GET.get("agrupacion", "ninguna")
    metrica = request.GET.get("metrica", "participaciones")
    tipo_grafica = request.GET.get("tipo_grafica", "barras")
    
    # Filtros para periodos semestrales
    periodos_semestrales = request.GET.getlist("periodos_semestrales[]")
    año_inicio_filtro = request.GET.get("año_inicio")
    año_fin_filtro = request.GET.get("año_fin")
    
    # Para comparación de periodos personalizados
    periodo1_inicio = request.GET.get("periodo1_inicio")
    periodo1_fin = request.GET.get("periodo1_fin")
    periodo2_inicio = request.GET.get("periodo2_inicio")
    periodo2_fin = request.GET.get("periodo2_fin")
    
    ejecutar_consulta = False
    mensaje_filtro = None
    datos_comparacion = []
    
    # ========== HELPER: Convertir periodo semestral a rango de fechas ==========
    def periodo_a_fechas(periodo):
        """
        Convierte periodo tipo "2024-1", "2024-Intersemestral-1", "2024-2" a fechas
        Retorna objetos date (no datetime)
        """
        partes = periodo.split("-")
        año = partes[0]
        
        if len(partes) == 2:
            semestre = partes[1]
            if semestre == "1":
                # Semestre 1: Enero - Junio
                return parse_date(f"{año}-01-01"), parse_date(f"{año}-06-15")
            elif semestre == "2":
                # Semestre 2: Agosto - Diciembre
                return parse_date(f"{año}-08-01"), parse_date(f"{año}-12-15")
        
        elif len(partes) == 3 and partes[1] == "Intersemestral":
            intersemestre = partes[2]
            if intersemestre == "1":
                # Intersemestral 1: Junio - Julio (entre semestre 1 y 2)
                return parse_date(f"{año}-06-16"), parse_date(f"{año}-07-31")
            elif intersemestre == "2":
                # Intersemestral 2: Diciembre - Enero siguiente
                return parse_date(f"{año}-12-16"), parse_date(f"{int(año)+1}-01-31")
        
        return None, None
    
    # ========== HELPER: Convertir fecha de DB a date si es datetime ==========
    def normalizar_fecha(fecha):
        """Convierte datetime a date si es necesario"""
        if isinstance(fecha, datetime):
            return fecha.date()
        return fecha
    
    # ========== COMPARACIÓN ENTRE PERIODOS SEMESTRALES ==========
    if tipo_comparacion == "periodos_semestrales":
        if len(periodos_semestrales) < 2:
            mensaje_filtro = "Selecciona al menos 2 periodos semestrales para comparar."
        else:
            ejecutar_consulta = True
            
            for periodo in periodos_semestrales:
                inicio, fin = periodo_a_fechas(periodo)
                
                if not inicio or not fin:
                    continue
                
                participaciones = Participaciones.objects.filter(
                    fecha_inscripcion__range=[inicio, fin]
                )
                
                # SIN AGRUPAR - Solo totales
                if agrupacion == "ninguna":
                    if metrica == "participaciones":
                        total = participaciones.count()
                    
                    elif metrica == "nuevos":
                        participantes_ids = participaciones.values_list(
                            'participantes_id_participante', flat=True
                        ).distinct()
                        
                        nuevos = 0
                        for p_id in participantes_ids:
                            primera = (
                                Participaciones.objects
                                .filter(participantes_id_participante=p_id)
                                .order_by('fecha_inscripcion')
                                .first()
                            )
                            if primera:
                                fecha_primera = normalizar_fecha(primera.fecha_inscripcion)
                                if inicio <= fecha_primera <= fin:
                                    nuevos += 1
                        total = nuevos
                    
                    elif metrica == "reincidentes":
                        participantes_ids = participaciones.values_list(
                            'participantes_id_participante', flat=True
                        ).distinct()
                        
                        reincidentes = 0
                        for p_id in participantes_ids:
                            anteriores = (
                                Participaciones.objects
                                .filter(participantes_id_participante=p_id)
                                .filter(fecha_inscripcion__lt=inicio)
                            )
                            if anteriores.exists():
                                reincidentes += 1
                        total = reincidentes
                    
                    datos_comparacion.append({
                        'label': periodo,
                        'datos': [{'categoria': 'Total', 'total': total}],
                        'total': total
                    })
                
                # CON AGRUPACIÓN
                else:
                    if agrupacion == "facultad":
                        campo = "participantes_id_participante__facultad"
                    elif agrupacion == "genero":
                        campo = "participantes_id_participante__genero"
                    elif agrupacion == "rol":
                        campo = "participantes_id_participante__roles_id_rol__nombre_rol"
                    elif agrupacion == "semestre_academico":
                        campo = "participantes_id_participante__semestre"
                    
                    if metrica == "participaciones":
                        resultados = (
                            participaciones
                            .values(campo)
                            .annotate(total=Count("id_participacion"))
                            .order_by(campo)
                        )
                    
                    elif metrica == "nuevos":
                        resultados = []
                        grupos = participaciones.values_list(campo, flat=True).distinct()
                        
                        for grupo in grupos:
                            participantes_grupo = participaciones.filter(**{campo: grupo}).values_list(
                                'participantes_id_participante', flat=True
                            ).distinct()
                            
                            nuevos = 0
                            for p_id in participantes_grupo:
                                primera = (
                                    Participaciones.objects
                                    .filter(participantes_id_participante=p_id)
                                    .order_by('fecha_inscripcion')
                                    .first()
                                )
                                if primera:
                                    fecha_primera = normalizar_fecha(primera.fecha_inscripcion)
                                    if inicio <= fecha_primera <= fin:
                                        nuevos += 1
                            
                            resultados.append({campo: grupo, 'total': nuevos})
                    
                    elif metrica == "reincidentes":
                        resultados = []
                        grupos = participaciones.values_list(campo, flat=True).distinct()
                        
                        for grupo in grupos:
                            participantes_grupo = participaciones.filter(**{campo: grupo}).values_list(
                                'participantes_id_participante', flat=True
                            ).distinct()
                            
                            reincidentes = 0
                            for p_id in participantes_grupo:
                                anteriores = (
                                    Participaciones.objects
                                    .filter(participantes_id_participante=p_id)
                                    .filter(fecha_inscripcion__lt=inicio)
                                )
                                if anteriores.exists():
                                    reincidentes += 1
                            
                            resultados.append({campo: grupo, 'total': reincidentes})
                    
                    datos_comparacion.append({
                        'label': periodo,
                        'datos': list(resultados),
                        'total': sum(r['total'] for r in resultados)
                    })
    
    # ========== COMPARACIÓN ENTRE PERIODOS PERSONALIZADOS ==========
    elif tipo_comparacion == "periodos_personalizados":
        if not all([periodo1_inicio, periodo1_fin, periodo2_inicio, periodo2_fin]):
            mensaje_filtro = "Completa las fechas de ambos periodos para comparar."
        else:
            ejecutar_consulta = True
            
            periodos = [
                {
                    'inicio': parse_date(periodo1_inicio),
                    'fin': parse_date(periodo1_fin),
                    'label': f'Periodo 1 ({periodo1_inicio} a {periodo1_fin})'
                },
                {
                    'inicio': parse_date(periodo2_inicio),
                    'fin': parse_date(periodo2_fin),
                    'label': f'Periodo 2 ({periodo2_inicio} a {periodo2_fin})'
                }
            ]
            
            for periodo in periodos:
                participaciones = Participaciones.objects.filter(
                    fecha_inscripcion__range=[periodo['inicio'], periodo['fin']]
                )
                
                # SIN AGRUPAR
                if agrupacion == "ninguna":
                    if metrica == "participaciones":
                        total = participaciones.count()
                    elif metrica == "nuevos":
                        participantes_ids = participaciones.values_list(
                            'participantes_id_participante', flat=True
                        ).distinct()
                        
                        nuevos = 0
                        for p_id in participantes_ids:
                            primera = (
                                Participaciones.objects
                                .filter(participantes_id_participante=p_id)
                                .order_by('fecha_inscripcion')
                                .first()
                            )
                            if primera:
                                fecha_primera = normalizar_fecha(primera.fecha_inscripcion)
                                if periodo['inicio'] <= fecha_primera <= periodo['fin']:
                                    nuevos += 1
                        total = nuevos
                    
                    elif metrica == "reincidentes":
                        participantes_ids = participaciones.values_list(
                            'participantes_id_participante', flat=True
                        ).distinct()
                        
                        reincidentes = 0
                        for p_id in participantes_ids:
                            anteriores = (
                                Participaciones.objects
                                .filter(participantes_id_participante=p_id)
                                .filter(fecha_inscripcion__lt=periodo['inicio'])
                            )
                            if anteriores.exists():
                                reincidentes += 1
                        total = reincidentes
                    
                    datos_comparacion.append({
                        'label': periodo['label'],
                        'datos': [{'categoria': 'Total', 'total': total}],
                        'total': total
                    })
                
                # CON AGRUPACIÓN
                else:
                    if agrupacion == "facultad":
                        campo = "participantes_id_participante__facultad"
                    elif agrupacion == "genero":
                        campo = "participantes_id_participante__genero"
                    elif agrupacion == "rol":
                        campo = "participantes_id_participante__roles_id_rol__nombre_rol"
                    elif agrupacion == "semestre_academico":
                        campo = "participantes_id_participante__semestre"
                    
                    if metrica == "participaciones":
                        resultados = (
                            participaciones
                            .values(campo)
                            .annotate(total=Count("id_participacion"))
                            .order_by(campo)
                        )
                    
                    elif metrica == "nuevos":
                        resultados = []
                        grupos = participaciones.values_list(campo, flat=True).distinct()
                        
                        for grupo in grupos:
                            participantes_grupo = participaciones.filter(**{campo: grupo}).values_list(
                                'participantes_id_participante', flat=True
                            ).distinct()
                            
                            nuevos = 0
                            for p_id in participantes_grupo:
                                primera = (
                                    Participaciones.objects
                                    .filter(participantes_id_participante=p_id)
                                    .order_by('fecha_inscripcion')
                                    .first()
                                )
                                if primera:
                                    fecha_primera = normalizar_fecha(primera.fecha_inscripcion)
                                    if periodo['inicio'] <= fecha_primera <= periodo['fin']:
                                        nuevos += 1
                            
                            resultados.append({campo: grupo, 'total': nuevos})
                    
                    elif metrica == "reincidentes":
                        resultados = []
                        grupos = participaciones.values_list(campo, flat=True).distinct()
                        
                        for grupo in grupos:
                            participantes_grupo = participaciones.filter(**{campo: grupo}).values_list(
                                'participantes_id_participante', flat=True
                            ).distinct()
                            
                            reincidentes = 0
                            for p_id in participantes_grupo:
                                anteriores = (
                                    Participaciones.objects
                                    .filter(participantes_id_participante=p_id)
                                    .filter(fecha_inscripcion__lt=periodo['inicio'])
                                )
                                if anteriores.exists():
                                    reincidentes += 1
                            
                            resultados.append({campo: grupo, 'total': reincidentes})
                    
                    datos_comparacion.append({
                        'label': periodo['label'],
                        'datos': list(resultados),
                        'total': sum(r['total'] for r in resultados)
                    })
    
    # ========== PREPARAR DATOS PARA GRÁFICAS ==========
    datos_grafica = {
        'labels': [],
        'datasets': []
    }
    
    if ejecutar_consulta and datos_comparacion:
        # Sin agrupar - gráfica simple
        if agrupacion == "ninguna":
            datos_grafica['labels'] = [grupo['label'] for grupo in datos_comparacion]
            datos_grafica['datasets'] = [{
                'label': metrica.capitalize(),
                'data': [grupo['total'] for grupo in datos_comparacion],
                'backgroundColor': 'rgba(0, 123, 255, 0.6)',
                'borderColor': '#007bff',
                'borderWidth': 2,
                'fill': tipo_grafica == 'area'
            }]
        
        # Con agrupación - gráfica comparativa
        else:
            categorias = set()
            for grupo in datos_comparacion:
                for dato in grupo['datos']:
                    if agrupacion == "facultad":
                        cat = dato.get('participantes_id_participante__facultad', 'Sin especificar')
                    elif agrupacion == "genero":
                        cat = dato.get('participantes_id_participante__genero', 'Sin especificar')
                    elif agrupacion == "rol":
                        cat = dato.get('participantes_id_participante__roles_id_rol__nombre_rol', 'Sin especificar')
                    elif agrupacion == "semestre_academico":
                        cat = f"Semestre {dato.get('participantes_id_participante__semestre', 'N/A')}"
                    categorias.add(cat)
            
            datos_grafica['labels'] = sorted(list(categorias))
            
            colores = [
                'rgba(0, 123, 255, 0.6)',
                'rgba(40, 167, 69, 0.6)',
                'rgba(255, 193, 7, 0.6)',
                'rgba(220, 53, 69, 0.6)',
                'rgba(111, 66, 193, 0.6)',
                'rgba(23, 162, 184, 0.6)'
            ]
            
            colores_borde = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#17a2b8']
            
            for idx, grupo in enumerate(datos_comparacion):
                valores = []
                datos_dict = {}
                
                for dato in grupo['datos']:
                    if agrupacion == "facultad":
                        key = dato.get('participantes_id_participante__facultad', 'Sin especificar')
                    elif agrupacion == "genero":
                        key = dato.get('participantes_id_participante__genero', 'Sin especificar')
                    elif agrupacion == "rol":
                        key = dato.get('participantes_id_participante__roles_id_rol__nombre_rol', 'Sin especificar')
                    elif agrupacion == "semestre_academico":
                        key = f"Semestre {dato.get('participantes_id_participante__semestre', 'N/A')}"
                    datos_dict[key] = dato['total']
                
                for categoria in datos_grafica['labels']:
                    valores.append(datos_dict.get(categoria, 0))
                
                datos_grafica['datasets'].append({
                    'label': grupo['label'],
                    'data': valores,
                    'backgroundColor': colores[idx % len(colores)],
                    'borderColor': colores_borde[idx % len(colores_borde)],
                    'borderWidth': 2,
                    'fill': tipo_grafica == 'area'
                })
    
    # ========== GENERAR PERIODOS DISPONIBLES CON FILTRO POR AÑO ==========
    periodos_disponibles = []
    años_disponibles = []
    fecha_min = Participaciones.objects.aggregate(Min('fecha_inscripcion'))['fecha_inscripcion__min']
    fecha_max = Participaciones.objects.aggregate(Max('fecha_inscripcion'))['fecha_inscripcion__max']
    
    if fecha_min and fecha_max:
        # Normalizar fechas si son datetime
        fecha_min = normalizar_fecha(fecha_min)
        fecha_max = normalizar_fecha(fecha_max)
        
        año_min = fecha_min.year
        año_max = fecha_max.year
        
        # Generar lista de años disponibles
        años_disponibles = list(range(año_min, año_max + 1))
        
        # Aplicar filtro de años si se seleccionó
        if año_inicio_filtro and año_fin_filtro:
            año_inicio_rango = int(año_inicio_filtro)
            año_fin_rango = int(año_fin_filtro)
        else:
            # Por defecto mostrar últimos 3 años
            año_inicio_rango = max(año_min, año_max - 2)
            año_fin_rango = año_max
        
        # Generar periodos (semestrales + intersemestrales)
        for año in range(año_inicio_rango, año_fin_rango + 1):
            periodos_disponibles.append(f"{año}-1")
            periodos_disponibles.append(f"{año}-Intersemestral-1")
            periodos_disponibles.append(f"{año}-2")
            if año < año_fin_rango:
                periodos_disponibles.append(f"{año}-Intersemestral-2")
    
    context = {
        "tipo_comparacion": tipo_comparacion,
        "agrupacion": agrupacion,
        "metrica": metrica,
        "tipo_grafica": tipo_grafica,
        "periodos_semestrales": periodos_semestrales,
        "periodos_disponibles": periodos_disponibles,
        "años_disponibles": años_disponibles,
        "año_inicio_filtro": int(año_inicio_filtro) if año_inicio_filtro else (años_disponibles[-3] if len(años_disponibles) >= 3 else años_disponibles[0] if años_disponibles else None),
        "año_fin_filtro": int(año_fin_filtro) if año_fin_filtro else (años_disponibles[-1] if años_disponibles else None),
        "datos_comparacion": datos_comparacion,
        "datos_grafica": json.dumps(datos_grafica),
        "ejecutar_consulta": ejecutar_consulta,
        "mensaje_filtro": mensaje_filtro,
        "periodo1_inicio": periodo1_inicio,
        "periodo1_fin": periodo1_fin,
        "periodo2_inicio": periodo2_inicio,
        "periodo2_fin": periodo2_fin,
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

# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

@login_required
def menu_analisis(request):
    """Menú personalizado según rol del usuario"""
    
    # Obtener rol del usuario actual
    try:
        participante = request.user.participantes_set.first()
        rol = participante.roles_id_rol.nombre_rol
    except:
        return redirect('login')
    
    # Definir opciones según rol
    opciones = []
    
    if rol in ['Administrador', 'Coordinador']:
        opciones = [
            {
                'titulo': 'Análisis de Comportamiento',
                'descripcion': 'Visualiza patrones de participación global',
                'url': 'Analytics_Reports:analisis_comportamiento',
                'icono': 'bi-graph-up'
            },
            {
                'titulo': 'Comparaciones y Estadísticas',
                'descripcion': 'Compara periodos y métricas',
                'url': 'Analytics_Reports:comparaciones',
                'icono': 'bi-bar-chart'
            },
            {
                'titulo': 'Recomendaciones',
                'descripcion': 'Sistema de sugerencias automáticas',
                'url': 'Analytics_Reports:recomendaciones',
                'icono': 'bi-lightbulb'
            },
            {
                'titulo': 'Registrar Asistencia',
                'descripcion': 'Control manual de asistencia',
                'url': 'Analytics_Reports:registrar_asistencia_manual',
                'icono': 'bi-clipboard-check'
            }
        ]
    
    elif rol == 'profesor':
        opciones = [
            {
                'titulo': 'Mis Actividades',
                'descripcion': 'Análisis de tus clases y talleres',
                'url': 'Analytics_Reports:dashboard_docente',
                'icono': 'bi-person-workspace'
            },
            {
                'titulo': 'Mis Estudiantes',
                'descripcion': 'Seguimiento de participantes',
                'url': 'Analytics_Reports:mis_estudiantes',
                'icono': 'bi-people'
            },
            {
                'titulo': 'Registrar Asistencia',
                'descripcion': 'Tomar asistencia en tus clases',
                'url': 'Analytics_Reports:registrar_asistencia_manual',
                'icono': 'bi-clipboard-check'
            },
            {
                'titulo': 'Comparar Grupos',
                'descripcion': 'Compara tus diferentes secciones',
                'url': 'Analytics_Reports:comparar_mis_grupos',
                'icono': 'bi-bar-chart'
            }
        ]
    
    elif rol == 'Estudiante':
        opciones = [
            {
                'titulo': 'Mi Historial',
                'descripcion': 'Ver mis participaciones',
                'url': 'Analytics_Reports:mi_historial',
                'icono': 'bi-calendar-check'
            },
            {
                'titulo': 'Mis Certificados',
                'descripcion': 'Descargar certificados',
                'url': 'Analytics_Reports:mis_certificados',
                'icono': 'bi-award'
            }
        ]
    
    context = {
        'rol': rol,
        'opciones': opciones,
        'nombre_usuario': participante.nombre
    }
    
    return render(request, 'menu_analisis.html', context)




# Reemplaza tu función dashboard_docente actual con esta:



# Agregar estos imports al inicio del archivo views.py
from django.db.models.functions import ExtractWeekDay, TruncMonth

# AGREGAR AL INICIO DE views.py:
from django.db.models.functions import ExtractWeekDay, TruncMonth

@login_required
def dashboard_docente(request):
    """Dashboard exclusivo para profesores - VERSIÓN CORREGIDA"""
    
    try:
        participante = request.user.participantes_set.first()
        
        if not participante:
            messages.error(request, 'No se encontró tu perfil de participante.')
            return redirect('home')
        
        rol = participante.roles_id_rol.nombre_rol.lower()
        
    except Exception as e:
        messages.error(request, f'Error al obtener perfil: {str(e)}')
        return redirect('home')
    
    if rol not in ['profesor', 'docente']:
        messages.warning(request, 'Esta sección es solo para profesores.')
        return redirect('Analytics_Reports:analytics_index')
    
    # ========== OBTENER ACTIVIDADES ==========
    mis_actividades = Actividades.objects.filter(responsable=participante)
    
    if not mis_actividades.exists():
        mis_participaciones_ids = Participaciones.objects.filter(
            participantes_id_participante=participante
        ).values_list('actividades_id_actividad', flat=True).distinct()
        
        mis_actividades = Actividades.objects.filter(
            id_actividad__in=mis_participaciones_ids
        )
    
    if not mis_actividades.exists() and participante.facultad:
        mis_actividades = Actividades.objects.filter(
            Q(nombre__icontains=participante.facultad) |
            Q(descripcion__icontains=participante.facultad)
        )
    
    if not mis_actividades.exists():
        context = {
            'participante': participante,
            'mensaje_sin_actividades': True,
            'total_mis_actividades': 0,
            'total_asistentes': 0,
            'promedio_asistencia': 0,
            'total_asistencias': 0,
            'sesiones_realizadas': 0,
            'top_estudiantes': [],
            'actividades_populares': [],
            'datos_actividades_populares': '[]',
            'datos_asistencia_por_dia': '[]',
            'asistencia_actividad_dia': [],
            'nombre_docente': f"{participante.nombre} {participante.apellido}",
            'facultad': participante.facultad or 'Sin facultad',
        }
        return render(request, 'dashboard_docente.html', context)
    
    # ========== MÉTRICAS GENERALES - CORREGIDAS ==========
    total_mis_actividades = mis_actividades.count()
    
    participaciones_estudiantes = Participaciones.objects.filter(
        actividades_id_actividad__in=mis_actividades,
        participantes_id_participante__roles_id_rol__nombre_rol='Estudiante'
    )
    
    total_asistentes = participaciones_estudiantes.values(
        'participantes_id_participante'
    ).distinct().count()
    
    # ✅ CORRECCIÓN CRÍTICA: Sesiones = fechas únicas con asistencias
    sesiones_realizadas = Asistencias.objects.filter(
        participaciones_id_participacion__actividades_id_actividad__in=mis_actividades
    ).values('fecha').distinct().count()
    
    # Total de asistencias "Presente"
    total_asistencias = Asistencias.objects.filter(
        participaciones_id_participacion__actividades_id_actividad__in=mis_actividades,
        estados_asistencia_id_estado_asistencia__nombre__icontains='presente'
    ).count()
    
    # ✅ PROMEDIO CORREGIDO: Total asistencias / Sesiones reales
    promedio_asistencia = round(
        total_asistencias / max(sesiones_realizadas, 1), 1
    )
    
    # ========== TOP ESTUDIANTES ==========
    top_estudiantes = (
        Participantes.objects
        .filter(
            roles_id_rol__nombre_rol='Estudiante',
            participaciones__actividades_id_actividad__in=mis_actividades
        )
        .annotate(
            total_asistencias=Count(
                'participaciones__asistencias__id_asistencia',
                filter=Q(
                    participaciones__asistencias__estados_asistencia_id_estado_asistencia__nombre__icontains='presente'
                ),
                distinct=True
            )
        )
        .filter(total_asistencias__gt=0)
        .values(
            'id_participante',
            'nombre',
            'apellido',
            'total_asistencias'
        )
        .order_by('-total_asistencias')[:10]
    )
    
    # ========== ACTIVIDADES POPULARES (solo si hay más de 1) ==========
    datos_actividades_populares = []
    if total_mis_actividades > 1:
        actividades_populares = mis_actividades.annotate(
            total_estudiantes=Count(
                'participaciones__participantes_id_participante',
                filter=Q(participaciones__participantes_id_participante__roles_id_rol__nombre_rol='Estudiante'),
                distinct=True
            )
        ).order_by('-total_estudiantes')[:5]
        
        datos_actividades_populares = [
            {
                'label': act.nombre,
                'value': act.total_estudiantes
            }
            for act in actividades_populares
        ]
    
    # ========== ASISTENCIA POR DÍA DE LA SEMANA ==========
    asistencias_por_dia = Asistencias.objects.filter(
        participaciones_id_participacion__actividades_id_actividad__in=mis_actividades,
        estados_asistencia_id_estado_asistencia__nombre__icontains='presente'
    ).annotate(
        dia_semana=ExtractWeekDay('fecha')
    ).values('dia_semana').annotate(
        total=Count('id_asistencia'),
        sesiones=Count('fecha', distinct=True)
    ).order_by('dia_semana')
    
    dias_nombres = {
        1: 'Domingo', 2: 'Lunes', 3: 'Martes', 4: 'Miércoles',
        5: 'Jueves', 6: 'Viernes', 7: 'Sábado'
    }
    
    datos_asistencia_por_dia = []
    for item in asistencias_por_dia:
        dia_num = item['dia_semana']
        total_asistencias_dia = item['total']
        sesiones_dia = item['sesiones']
        promedio_dia = round(total_asistencias_dia / max(sesiones_dia, 1), 1)
        
        datos_asistencia_por_dia.append({
            'label': dias_nombres.get(dia_num, 'N/A'),
            'value': promedio_dia,
            'total_asistencias': total_asistencias_dia,
            'sesiones': sesiones_dia
        })
    
    # ========== DETALLE POR ACTIVIDAD Y DÍA ==========
    asistencia_actividad_dia = []
    
    for actividad in mis_actividades:
        asistencias_act = Asistencias.objects.filter(
            participaciones_id_participacion__actividades_id_actividad=actividad,
            estados_asistencia_id_estado_asistencia__nombre__icontains='presente'
        ).annotate(
            dia_semana=ExtractWeekDay('fecha')
        ).values('dia_semana').annotate(
            total=Count('id_asistencia'),
            sesiones=Count('fecha', distinct=True)
        )
        
        dias_actividad = []
        for item in asistencias_act:
            dia_num = item['dia_semana']
            total_asist = item['total']
            sesiones = item['sesiones']
            promedio = round(total_asist / max(sesiones, 1), 1)
            
            dias_actividad.append({
                'dia': dias_nombres.get(dia_num, 'N/A'),
                'promedio': promedio,
                'sesiones': sesiones,
                'total': total_asist
            })
        
        if dias_actividad:
            # Ordenar por día de la semana
            orden_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            dias_actividad.sort(key=lambda x: orden_dias.index(x['dia']) if x['dia'] in orden_dias else 999)
            
            asistencia_actividad_dia.append({
                'actividad': actividad.nombre,
                'dias': dias_actividad
            })
    
    # ========== CONTEXTO FINAL ==========
    context = {
        'participante': participante,
        'total_mis_actividades': total_mis_actividades,
        'total_asistentes': total_asistentes,
        'promedio_asistencia': promedio_asistencia,
        'total_asistencias': total_asistencias,
        'sesiones_realizadas': sesiones_realizadas,
        'top_estudiantes': top_estudiantes,
        'datos_actividades_populares': json.dumps(datos_actividades_populares),
        'datos_asistencia_por_dia': json.dumps(datos_asistencia_por_dia),
        'asistencia_actividad_dia': asistencia_actividad_dia,
        'nombre_docente': f"{participante.nombre} {participante.apellido}",
        'facultad': participante.facultad or 'Sin facultad',
        'mensaje_sin_actividades': False
    }
    
    return render(request, 'dashboard_docente.html', context)


# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Count, Q
from datetime import datetime
# Reemplaza tu función mi_historial_estudiante actual con esta:
@login_required
def mi_historial_estudiante(request):
    # Obtener el participante del usuario logueado
    participante = get_object_or_404(Participantes, user=request.user)
    
    # ✅ CORRECCIÓN: Contar asistencias desde la tabla Asistencias
    # Filtramos por estado "Presente" y participante actual
    asistencias = Asistencias.objects.filter(
        participaciones_id_participacion__participantes_id_participante=participante,
        estados_asistencia_id_estado_asistencia__nombre='Presente'
    ).select_related(
        'participaciones_id_participacion__actividades_id_actividad',
        'estados_asistencia_id_estado_asistencia'
    ).order_by('-fecha')
    
    # Estadísticas generales
    stats = {
        'presente': asistencias.count(),  # ✅ Ahora cuenta correctamente
    }
    
    # ✅ Progreso hacia la camiseta (10 asistencias)
    META_CAMISETA = 10
    progreso_camiseta = {
        'total_presentes': stats['presente'],
        'meta': META_CAMISETA,
        'falta': max(0, META_CAMISETA - stats['presente']),
        'porcentaje': min(100, (stats['presente'] / META_CAMISETA * 100)),
        'alcanzado': stats['presente'] >= META_CAMISETA
    }
    
    # ✅ Estadísticas por actividad
    actividades_stats = Asistencias.objects.filter(
        participaciones_id_participacion__participantes_id_participante=participante,
        estados_asistencia_id_estado_asistencia__nombre='Presente'
    ).values(
        'participaciones_id_participacion__actividades_id_actividad__nombre'
    ).annotate(
        presente=Count('id_asistencia')
    ).order_by('-presente')
    
    # Renombrar clave para usar en template
    actividades_stats = [
        {
            'nombre': act['participaciones_id_participacion__actividades_id_actividad__nombre'],
            'presente': act['presente']
        }
        for act in actividades_stats
    ]
    
    context = {
        'participante': participante,
        'asistencias': asistencias,
        'stats': stats,
        'progreso_camiseta': progreso_camiseta,
        'actividades_stats': actividades_stats,
    }
    
    return render(request, 'mi_historial_estudiante.html', context)


# Analytics_Reports/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

@login_required
def analytics_index(request):
    """
    Menú principal que decide qué mostrar según el rol del usuario
    """
    try:
        # ✅ CAMBIO AQUÍ: participantes_set en lugar de participante
        participante = request.user.participantes_set.first()
        
        if not participante:
            # Si no tiene participante, redirigir al home
            return redirect('home')
        
        rol = participante.roles_id_rol.nombre_rol
    except:
        return redirect('home')
    
    # Contexto base
    context = {
        'participante': participante,
        'rol': rol,
        'nombre_usuario': participante.nombre
    }
    
    # Decidir qué template mostrar según el rol
    if rol == 'Administrador' or request.user.is_superuser:
        return render(request, 'index.html', context)
    
    elif rol == 'Coordinador':
        return render(request, 'index.html', context)
    
    elif rol == 'profesor':
        return redirect('Analytics_Reports:dashboard_docente')
    
    elif rol == 'Estudiante':
        return redirect('Analytics_Reports:mi_historial')
    
    else:
        return redirect('home')
 



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