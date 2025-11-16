"""
Sistema inteligente de notificaciones - SOLO POSITIVAS
Control anti-spam mediante hash_unicidad
"""

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.db.models import Count, Q, Max
from datetime import timedelta
from universitaryWellbeing.models import (
    Participaciones, Asistencias, Participantes, 
    Notificaciones, TiposNotificacion, Actividades,
    CalificacionesActividad, ConfiguracionNotificaciones, Citas
)

from .control_notificaciones import ControlNotificacionesContextual


# ============================================
# TAREA 1: RECONOCIMIENTOS (SOLO POSITIVO)
# ============================================
@shared_task
def verificar_y_otorgar_reconocimientos():
    """
    ✅ Otorga reconocimientos por hitos configurables
    ✅ SOLO mensajes positivos
    """
    config = ConfiguracionNotificaciones.obtener_config()
    
    if not config.reconocimientos_activos:
        return '⏸️ Reconocimientos desactivados por el admin'
    
    hitos = config.obtener_hitos()  # [10, 20, 30...]
    reconocimientos = 0
    
    participaciones = Participaciones.objects.filter(
        estados_participacion_id_estado_participacion_id=1,
        actividades_id_actividad__requiere_inscripcion='S'
    ).select_related('participantes_id_participante', 'actividades_id_actividad')
    
    for participacion in participaciones:
        participante = participacion.participantes_id_participante
        actividad = participacion.actividades_id_actividad
        
        asistencias = Asistencias.objects.filter(
            participaciones_id_participacion=participacion,
            estados_asistencia_id_estado_asistencia__nombre='Presente'
        ).count()
        
        for hito in hitos:
            if asistencias >= hito:
                contexto = f"hito_{hito}"
                
                # ✅ Control anti-spam
                if ControlNotificacionesContextual.ya_existe_notificacion(
                    participante, 'Reconocimiento', actividad, contexto
                ):
                    continue
                
                mensaje = (
                    f"🏆 ¡Felicitaciones! Has alcanzado {hito} asistencias en "
                    f"'{actividad.nombre}'. ¡Excelente compromiso!"
                )
                
                notif = ControlNotificacionesContextual.registrar_notificacion(
                    participante, 'Reconocimiento', mensaje, actividad, contexto
                )
                
                if notif:
                    try:
                        send_mail(
                            subject=f"🏆 Reconocimiento - {hito} asistencias",
                            message=mensaje,
                            from_email='bienestar@universidad.edu',
                            recipient_list=[participante.correo],
                            fail_silently=True
                        )
                    except:
                        pass
                    
                    reconocimientos += 1
                    break  # Solo un reconocimiento por iteración
    
    return f'✓ {reconocimientos} reconocimientos otorgados'


# ============================================
# TAREA 2: CLASIFICACIÓN (NO ENVÍA CORREOS)
# ============================================
@shared_task
def clasificar_estudiantes_para_admin():
    """
    ❌ NO envía correos a estudiantes
    ✅ Solo actualiza clasificaciones para análisis del admin
    
    Categorías:
    - Riesgo crítico: ≤2 asistencias + sin asistir hace ≥21 días
    - Baja asistencia: <5 asistencias
    - Inactivos: sin asistir hace ≥14 días
    - Destacados: ≥15 asistencias
    """
    config = ConfiguracionNotificaciones.obtener_config()
    
    # Estos datos se usan en la vista recomendaciones.html para el admin
    clasificados = {
        'riesgo_critico': 0,
        'baja_asistencia': 0,
        'inactivos': 0,
        'destacados': 0
    }
    
    participaciones = Participaciones.objects.filter(
        estados_participacion_id_estado_participacion_id=1,
        actividades_id_actividad__requiere_inscripcion='S'
    ).annotate(
        total_asistencias=Count('asistencias'),
        ultima_asistencia=Max('asistencias__fecha')
    ).select_related('participantes_id_participante', 'actividades_id_actividad')
    
    ahora = timezone.now().date()
    
    for participacion in participaciones:
        asistencias = participacion.total_asistencias
        ultima = participacion.ultima_asistencia
        
        # Calcular días sin asistir
        dias_sin_asistir = (ahora - ultima).days if ultima else 999
        
        # Clasificar (sin enviar correos)
        if asistencias <= config.umbral_riesgo_critico and dias_sin_asistir >= config.dias_riesgo_critico:
            clasificados['riesgo_critico'] += 1
        elif asistencias < config.umbral_baja_asistencia:
            clasificados['baja_asistencia'] += 1
        elif dias_sin_asistir >= config.dias_inactividad:
            clasificados['inactivos'] += 1
        elif asistencias >= config.asistencias_destacado:
            clasificados['destacados'] += 1
    
    return f"✓ Clasificación completada: {clasificados}"


# ============================================
# TAREA 3: ENCUESTAS (SOLO POSITIVO)
# ============================================
@shared_task
def enviar_encuestas_retroalimentacion():
    """
    ✅ Envía encuestas UNA VEZ por actividad finalizada
    ✅ SOLO a quienes cumplan asistencias mínimas
    """
    config = ConfiguracionNotificaciones.obtener_config()
    
    if not config.encuestas_activas:
        return '⏸️ Encuestas desactivadas por el admin'
    
    ahora = timezone.now()
    fecha_limite = ahora - timedelta(days=config.dias_despues_cierre_encuesta)
    encuestas = 0
    
    actividades_finalizadas = Actividades.objects.filter(
        fecha_cierre_ins__lte=ahora,
        fecha_cierre_ins__gte=fecha_limite,
        requiere_inscripcion='S'
    )
    
    for actividad in actividades_finalizadas:
        participaciones = Participaciones.objects.filter(
            actividades_id_actividad=actividad,
            estados_participacion_id_estado_participacion_id=1
        ).annotate(
            num_asistencias=Count(
                'asistencias',
                filter=Q(asistencias__estados_asistencia_id_estado_asistencia__nombre='Presente')
            )
        ).filter(num_asistencias__gte=config.asistencias_minimas_encuesta)
        
        for participacion in participaciones:
            participante = participacion.participantes_id_participante
            
            # Ya calificó
            if CalificacionesActividad.objects.filter(
                actividades_id_actividad=actividad,
                participantes_id_participante=participante
            ).exists():
                continue
            
            # ✅ Control anti-spam
            if ControlNotificacionesContextual.ya_existe_notificacion(
                participante, 'Encuesta', actividad, 'solicitud_inicial'
            ):
                continue
            
            mensaje = (
                f"📝 ¡Tu opinión importa! Califica tu experiencia en '{actividad.nombre}'. "
                f"Ayúdanos a mejorar nuestras actividades."
            )
            
            notif = ControlNotificacionesContextual.registrar_notificacion(
                participante, 'Encuesta', mensaje, actividad, 'solicitud_inicial'
            )
            
            if notif:
                try:
                    send_mail(
                        subject=f'📝 Encuesta: {actividad.nombre}',
                        message=mensaje,
                        from_email='bienestar@universidad.edu',
                        recipient_list=[participante.correo],
                        fail_silently=True
                    )
                except:
                    pass
                
                encuestas += 1
    
    return f'✓ {encuestas} encuestas enviadas'


# ============================================
# TAREA 4: RECORDATORIOS DE CITAS (POSITIVO)
# ============================================
@shared_task
def enviar_recordatorios_citas():
    """
    ✅ Recordatorios de citas psicológicas
    ✅ Solo para citas confirmadas
    """
    config = ConfiguracionNotificaciones.obtener_config()
    
    if not config.recordatorios_citas_activos:
        return '⏸️ Recordatorios de citas desactivados'
    
    ahora = timezone.now()
    recordatorios = 0
    
    # Recordatorio X días antes
    fecha_dias_antes = ahora + timedelta(days=config.recordatorio_cita_dias_antes)
    
    citas_proximas = Citas.objects.filter(
        fecha__date=fecha_dias_antes.date(),
        estados_cita_id_estado_cita__nombre__in=['Programada', 'Confirmada']
    ).select_related('participantes_id_participante')
    
    for cita in citas_proximas:
        contexto = f"cita_{cita.id_cita}_dias_antes"
        
        if ControlNotificacionesContextual.ya_existe_notificacion(
            cita.participantes_id_participante, 'Recordatorio', None, contexto
        ):
            continue
        
        mensaje = (
            f"🩺 Recordatorio: Tienes una cita programada para el "
            f"{cita.fecha.strftime('%d/%m/%Y a las %H:%M')}. "
            f"Motivo: {cita.motivo}"
        )
        
        notif = ControlNotificacionesContextual.registrar_notificacion(
            cita.participantes_id_participante, 'Recordatorio', mensaje, None, contexto
        )
        
        if notif:
            try:
                send_mail(
                    subject='🩺 Recordatorio de cita',
                    message=mensaje,
                    from_email='bienestar@universidad.edu',
                    recipient_list=[cita.participantes_id_participante.correo],
                    fail_silently=True
                )
            except:
                pass
            
            recordatorios += 1
    
    return f'✓ {recordatorios} recordatorios de citas enviados'


# ============================================
# TAREA 5: CANCELACIONES DE ACTIVIDADES
# ============================================
@shared_task
def notificar_cancelacion_actividad(actividad_id, motivo=""):
    """
    ✅ Notifica cancelaciones a todos los inscritos
    ✅ Mensajes informativos, no negativos
    """
    try:
        actividad = Actividades.objects.get(id_actividad=actividad_id)
    except Actividades.DoesNotExist:
        return f'❌ Actividad {actividad_id} no existe'
    
    participaciones = Participaciones.objects.filter(
        actividades_id_actividad=actividad,
        estados_participacion_id_estado_participacion_id=1
    ).select_related('participantes_id_participante')
    
    notificados = 0
    
    for participacion in participaciones:
        participante = participacion.participantes_id_participante
        
        contexto = f"cancelacion_{actividad_id}"
        
        if ControlNotificacionesContextual.ya_existe_notificacion(
            participante, 'Cancelacion', actividad, contexto
        ):
            continue
        
        mensaje = (
            f"⚠️ Información importante: La actividad '{actividad.nombre}' "
            f"ha sido cancelada. "
            f"{motivo if motivo else 'Te informaremos sobre nuevas fechas.'}"
        )
        
        notif = ControlNotificacionesContextual.registrar_notificacion(
            participante, 'Cancelacion', mensaje, actividad, contexto
        )
        
        if notif:
            try:
                send_mail(
                    subject=f'⚠️ Cancelación: {actividad.nombre}',
                    message=mensaje,
                    from_email='bienestar@universidad.edu',
                    recipient_list=[participante.correo],
                    fail_silently=True
                )
            except:
                pass
            
            notificados += 1
    
    return f'✓ {notificados} notificaciones de cancelación enviadas'