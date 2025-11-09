from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from universitaryWellbeing.models import HorariosParticipante, Notificaciones
from notificaciones.views import crear_notificacion_validada, TiposNotificacion, es_dia_lectivo


@shared_task
def generar_notificaciones_horarios_task():
    """
    Crea notificaciones automáticas para eventos próximos según el horario del participante.
    Usa la zona horaria de Colombia (America/Bogota) configurada en Django.
    """
    #  Activar zona horaria Colombia explícitamente
    timezone.activate('America/Bogota')
    
    #   Obtener hora actual en Colombia (aware datetime)
    ahora = timezone.localtime(timezone.now())
    
    #   Rango: próximas 2 horas en Colombia
    en_2_horas = ahora + timedelta(hours=2)
    
    print("\n" + "="*60)
    print(f" GENERANDO NOTIFICACIONES - {ahora.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("="*60)
    print(f"Zona horaria activa: {timezone.get_current_timezone_name()}")
    print(f"Hora actual (Colombia): {ahora}")
    print(f"Buscando eventos hasta: {en_2_horas}")
    
    #  Buscar horarios próximos
    # fecha_inicio está en UTC en la BD, Django lo convierte automáticamente
    proximos = HorariosParticipante.objects.filter(
        fecha_inicio__gte=ahora,
        fecha_inicio__lte=en_2_horas
    )
    
    print(f" Horarios encontrados: {proximos.count()}")
    
    # Obtener o crear tipo de notificación
    tipo_recordatorio, _ = TiposNotificacion.objects.get_or_create(
        nombre="Recordatorio de actividad"
    )
    
    contador_creadas = 0
    contador_saltadas = 0
    
    for horario in proximos:
        participante = horario.participantes_id_participante
        
        #  Convertir fecha del evento a hora Colombia
        fecha_evento = timezone.localtime(horario.fecha_inicio)
        lugar = horario.notas or "lugar asignado"
        
        print(f"\n   Procesando: '{horario.titulo}'")
        print(f"     Participante: {participante.user.username}")
        print(f"     Fecha evento: {fecha_evento.strftime('%d/%m/%Y %H:%M')}")
        
        # Verificar si es día lectivo
        if not es_dia_lectivo(fecha_evento.date()):
            print(f"     ⊗ Saltado: Día no lectivo")
            contador_saltadas += 1
            continue
        
        #  Verificar si ya existe notificación similar reciente
        existe = Notificaciones.objects.filter(
            participantes_id_participante=participante,
            mensaje__contains=horario.titulo,
            fecha__gte=ahora - timedelta(hours=2)
        ).exists()
        
        if existe:
            print(f"  Saltado: Notificación duplicada")
            contador_saltadas += 1
            continue
        
        # Crear mensaje
        mensaje = (
            f"Recordatorio: Tienes '{horario.titulo}' programado el "
            f"{fecha_evento.strftime('%d/%m/%Y a las %H:%M')} en {lugar}."
        )
        
        #  Crear notificación usando la función validada
        resultado = crear_notificacion_validada(
            mensaje=mensaje,
            fecha_deseada=ahora,  # Se envía ahora mismo
            participante=participante,
            tipo_notificacion=tipo_recordatorio,
            auto_reprogramar=False  # No reprogramar recordatorios automáticos
        )
        
        if resultado['success']:
            print(f"  Notificación creada ID: {resultado['notificacion'].id_notificacion}")
            contador_creadas += 1
        else:
            print(f"  Error: {resultado['motivo']}")
            contador_saltadas += 1
    
    print("\n" + "="*60)
    print(f" Total creadas: {contador_creadas}")
    print(f" Total saltadas: {contador_saltadas}")
    print("="*60 + "\n")
    
    return {
        'creadas': contador_creadas,
        'saltadas': contador_saltadas,
        'hora_ejecucion': ahora.isoformat()
    }