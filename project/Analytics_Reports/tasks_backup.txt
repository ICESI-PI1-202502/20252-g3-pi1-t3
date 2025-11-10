"""
Sistema inteligente de notificaciones - CON CONFIGURACIÓN ADMIN
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
# TAREA 1: RECONOCIMIENTOS (CONFIGURABLE)
# ============================================
@shared_task
def verificar_y_otorgar_reconocimientos():
    """
    Otorga reconocimientos por hitos configurables
    ✅ Respeta configuración del admin
    """
    config = ConfiguracionNotificaciones.obtener_config()
    
    if not config.reconocimientos_activos:
        return '⏸️ Reconocimientos desactivados por el admin'
    
    hitos = config.obtener_hitos()  # Lee desde BD
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
                
                # ✅ Control anti-spam: una vez por hito PARA SIEMPRE
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
                
                if notif:  # Solo si se creó
                    try:
                        send_mail(
                            subject=f"🏆 Reconocimiento - {hito} asistencias",
                            message=mensaje,
                            from_email='luis.gluis.g.io.com@gmail.com',
                            recipient_list=[participante.correo],
                            fail_silently=True
                        )
                    except:
                        pass
                    
                    reconocimientos += 1
                    break  # Solo un reconocimiento por iteración
    
    return f'✓ {reconocimientos} reconocimientos otorgados (sin duplicados)'


# ============================================
# TAREA 2: INASISTENCIAS (CONFIGURABLE)
# ============================================
@shared_task
def verificar_inasistencias_inscritos():
    """
    Alerta por inasistencia prolongada
    ✅ Respeta configuración del admin
    """
    config = ConfiguracionNotificaciones.obtener_config()
    
    if not config.alertas_inasistencia_activas:
        return '⏸️ Alertas de inasistencia desactivadas por el admin'
    
    dias_sin_asistir = config.dias_sin_asistir_alerta
    asistencias_minimas = config.asistencias_minimas_para_alertar
    fecha_limite = timezone.now().date() - timedelta(days=dias_sin_asistir)
    alertas = 0
    
    # Solo quienes YA asistieron al menos X veces
    participaciones = Participaciones.objects.filter(
        estados_participacion_id_estado_participacion_id=1,
        actividades_id_actividad__requiere_inscripcion='S'
    ).annotate(
        total_asistencias=Count('asistencias'),
        ultima_asistencia=Max('asistencias__fecha')
    ).filter(
        total_asistencias__gte=asistencias_minimas,
        ultima_asistencia__lt=fecha_limite
    ).select_related('participantes_id_participante', 'actividades_id_actividad')
    
    for participacion in participaciones:
        participante = participacion.participantes_id_participante
        actividad = participacion.actividades_id_actividad
        dias_ausente = (timezone.now().date() - participacion.ultima_asistencia).days
        
        contexto = f"inasistencia_{dias_sin_asistir}dias"
        
        # ✅ Ventana temporal configurable
        ventana_horas = None
        if config.dias_repetir_alerta_inasistencia > 0:
            ventana_horas = config.dias_repetir_alerta_inasistencia * 24
        
        if ControlNotificacionesContextual.ya_existe_notificacion(
            participante, 'Inasistencia', actividad, contexto, ventana_horas
        ):
            continue
        
        mensaje = (
            f"⚠️ Hemos notado tu ausencia en '{actividad.nombre}'. "
            f"Llevas {dias_ausente} días sin asistir. "
            f"¿Todo está bien? Estamos aquí para apoyarte."
        )
        
        notif = ControlNotificacionesContextual.registrar_notificacion(
            participante, 'Inasistencia', mensaje, actividad, contexto
        )
        
        if notif:
            try:
                send_mail(
                    subject=f'⚠️ Te extrañamos en {actividad.nombre}',
                    message=mensaje,
                    from_email='luis.gluis.g.io.com@gmail.com',
                    recipient_list=[participante.correo],
                    fail_silently=True
                )
            except:
                pass
            
            alertas += 1
    
    return f'✓ {alertas} alertas de inasistencia enviadas'


# ============================================
# TAREA 3: ENCUESTAS (CONFIGURABLE)
# ============================================
@shared_task
def enviar_encuestas_retroalimentacion():
    """
    Envía encuestas UNA VEZ por actividad finalizada
    ✅ Respeta configuración del admin
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
            
            # ✅ UNA VEZ en la vida (sin ventana temporal)
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
                        from_email='luis.gluis.g.io.com@gmail.com',
                        recipient_list=[participante.correo],
                        fail_silently=True
                    )
                except:
                    pass
                
                encuestas += 1
    
    return f'✓ {encuestas} encuestas enviadas (ÚNICAS por actividad)'


# ============================================
# TAREA 4: RECORDATORIOS DE CITAS (NUEVA)
# ============================================
@shared_task
def enviar_recordatorios_citas():
    """
    Recordatorios de citas psicológicas
    ✅ Respeta configuración del admin
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
                    from_email='luis.gluis.g.io.com@gmail.com',
                    recipient_list=[cita.participantes_id_participante.correo],
                    fail_silently=True
                )
            except:
                pass
            
            recordatorios += 1
    
    return f'✓ {recordatorios} recordatorios de citas enviados'