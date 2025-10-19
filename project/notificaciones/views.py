#from django.shortcuts import render
#from django.contrib.auth.decorators import login_required
#from universitaryWellbeing.models import Notificaciones

#@login_required
#def ver_notificaciones(request):
#    notificaciones = Notificaciones.objects.filter(
#        participantes_id_participante__user_id=request.user.id
#    ).order_by('-fecha')
#
#    return render(request, "notificaciones.html", {
#        "notificaciones": notificaciones
##    })

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime, timedelta, date
from universitaryWellbeing.models import Notificaciones, TiposNotificacion, Participantes
import logging

logger = logging.getLogger(__name__)


# ============================================
# LÓGICA DE CALENDARIO ACADÉMICO
# ============================================

def get_calendario_academico():
    """Obtiene el calendario académico desde settings"""
    return getattr(settings, 'CALENDARIO_ACADEMICO', {})


def es_dia_lectivo(fecha):
    """Verifica si una fecha es día lectivo"""
    fecha_str = fecha.strftime('%Y-%m-%d')
    calendario = get_calendario_academico()
    return fecha_str not in calendario


def get_info_dia_no_lectivo(fecha):
    """Obtiene información de un día no lectivo"""
    fecha_str = fecha.strftime('%Y-%m-%d')
    calendario = get_calendario_academico()
    return calendario.get(fecha_str)


def permite_notificaciones_criticas(fecha):
    """
    Verifica si un día no lectivo permite notificaciones críticas.
    Solo festivos permiten críticas, recesos y parciales NO.
    """
    info = get_info_dia_no_lectivo(fecha)
    if not info:
        return True  # Día lectivo, permite todo
    
    tipo_dia = info.get('tipo', 'festivo')
    return tipo_dia == 'festivo'


def es_notificacion_critica(tipo_notificacion_nombre):
    """
    Determina si una notificación es crítica basándose en su nombre
    """
    palabras_criticas = [
        'cancelación', 'cancelacion', 'suspensión', 'suspension',
        'seguridad', 'emergencia', 'urgente', 'critico', 'crítico', 'alerta',
    ]
    
    nombre_lower = tipo_notificacion_nombre.lower()
    return any(palabra in nombre_lower for palabra in palabras_criticas)


def validar_envio_notificacion(fecha_programada, tipo_notificacion):
    """
    Valida si se puede enviar una notificación en la fecha programada
    
    Returns:
        tuple: (puede_enviar: bool, motivo: str)
    """
    # Obtener nombre del tipo
    if isinstance(tipo_notificacion, TiposNotificacion):
        nombre_tipo = tipo_notificacion.nombre
    elif isinstance(tipo_notificacion, str):
        nombre_tipo = tipo_notificacion
    else:
        try:
            tipo_obj = TiposNotificacion.objects.get(id_tipo_notificacion=tipo_notificacion)
            nombre_tipo = tipo_obj.nombre
        except TiposNotificacion.DoesNotExist:
            return False, "Tipo de notificación no encontrado"
    
    fecha_solo = fecha_programada.date() if isinstance(fecha_programada, datetime) else fecha_programada
    
    # Verificar si es día lectivo
    if es_dia_lectivo(fecha_solo):
        return True, "Día lectivo - envío permitido"
    
    # Si no es lectivo, verificar si es crítico
    es_critico = es_notificacion_critica(nombre_tipo)
    
    if not es_critico:
        info = get_info_dia_no_lectivo(fecha_solo)
        desc = info.get('descripcion', 'día no lectivo') if info else 'día no lectivo'
        return False, f"Día no lectivo ({desc}) y notificación no crítica"
    
    # Si es crítico, verificar si el día permite críticos
    if permite_notificaciones_criticas(fecha_solo):
        return True, "Día no lectivo pero notificación crítica permitida"
    else:
        info = get_info_dia_no_lectivo(fecha_solo)
        desc = info.get('descripcion', 'día no lectivo') if info else 'día no lectivo'
        return False, f"Día no lectivo ({desc}) que no permite notificaciones críticas"


def buscar_proximo_dia_lectivo(fecha_inicio, max_dias=30):
    """Busca el próximo día lectivo a partir de una fecha"""
    fecha_actual = fecha_inicio
    
    for _ in range(max_dias):
        fecha_solo = fecha_actual.date() if isinstance(fecha_actual, datetime) else fecha_actual
        if es_dia_lectivo(fecha_solo):
            return fecha_actual
        fecha_actual += timedelta(days=1)
    
    return None


def crear_notificacion_validada(mensaje, fecha_deseada, participante, tipo_notificacion, auto_reprogramar=True):
    """
    Crea una notificación aplicando las reglas de calendario académico
    
    Returns:
        dict: resultado con información del proceso
    """
    puede_enviar, motivo = validar_envio_notificacion(fecha_deseada, tipo_notificacion)
    fecha_final = fecha_deseada
    reprogramada = False
    
    # Si no puede enviar y se permite reprogramar
    if not puede_enviar and auto_reprogramar:
        es_critico = es_notificacion_critica(tipo_notificacion.nombre)
        
        # Solo reprogramar las no críticas
        if not es_critico:
            proximo = buscar_proximo_dia_lectivo(fecha_deseada)
            if proximo:
                fecha_final = proximo
                puede_enviar = True
                reprogramada = True
                motivo = f"Reprogramada de {fecha_deseada.date()} a {fecha_final.date()}"
            else:
                return {
                    'success': False,
                    'mensaje': 'No se encontró día lectivo disponible en los próximos 30 días',
                    'notificacion': None
                }
    
    # Crear la notificación si es posible
    if puede_enviar:
        try:
            notificacion = Notificaciones.objects.create(
                mensaje=mensaje,
                fecha=fecha_final,
                participantes_id_participante=participante,
                tipos_notificacion_id_tipo_notificacion=tipo_notificacion
            )
            
            #logger.info(f"Notificación {notificacion.id_notificacion} creada - {motivo}")
            
            return {
                'success': True,
                'mensaje': motivo,
                'notificacion': notificacion,
                'reprogramada': reprogramada,
                'fecha_original': fecha_deseada if reprogramada else None,
                'fecha_final': fecha_final
            }
        except Exception as e:
            logger.error(f"Error al crear notificación: {e}")
            return {
                'success': False,
                'mensaje': f"Error al crear notificación: {str(e)}",
                'notificacion': None
            }
    
    return {
        'success': False,
        'mensaje': motivo,
        'notificacion': None
    }


# ============================================
# VISTAS
# ============================================

@login_required
def ver_notificaciones(request):
    """Vista original - Lista notificaciones del usuario"""
    notificaciones = Notificaciones.objects.filter(
        participantes_id_participante__user_id=request.user.id
    ).order_by('-fecha')

    return render(request, "notificaciones.html", {
        "notificaciones": notificaciones
    })


@login_required
def crear_notificacion(request):
    """Crea una nueva notificación con validación de calendario"""
    # Obtener tipos de notificación y participantes para el formulario
    tipos = TiposNotificacion.objects.all()
    participantes = Participantes.objects.filter(estado_activo='1')
    
    if request.method == 'POST':
        # Obtener datos del formulario
        mensaje = request.POST.get('mensaje')
        fecha_str = request.POST.get('fecha')
        participante_id = request.POST.get('participante_id')
        tipo_id = request.POST.get('tipo_id')
        auto_reprogramar = request.POST.get('auto_reprogramar') == 'on'
        
        try:
            # Convertir fecha
            fecha = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
            
            # Obtener objetos
            participante = Participantes.objects.get(id_participante=participante_id)
            tipo = TiposNotificacion.objects.get(id_tipo_notificacion=tipo_id)
            
            # Crear notificación con validación
            resultado = crear_notificacion_validada(
                mensaje=mensaje,
                fecha_deseada=fecha,
                participante=participante,
                tipo_notificacion=tipo,
                auto_reprogramar=auto_reprogramar
            )
            
            if resultado['success']:
                if resultado.get('reprogramada'):
                    messages.warning(request, f"✓ Notificación creada y reprogramada. {resultado['mensaje']}")
                else:
                    messages.success(request, f"✓ Notificación creada. {resultado['mensaje']}")
                return redirect('ver_notificaciones')
            else:
                messages.error(request, f"✗ No se pudo crear: {resultado['mensaje']}")
                
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    context = {
        'tipos': tipos,
        'participantes': participantes,
    }
    
    return render(request, 'crear_notificacion.html', context)

 



def generar_notificaciones_horarios():
    """
    Crea notificaciones automáticas para eventos próximos según el horario del participante.
    """
    from universitaryWellbeing.models import HorariosParticipante, Notificaciones, TiposNotificacion
    
    ahora = timezone.now()
    en_48_horas = ahora + timedelta(hours=48)  # AMPLIADO A 48 HORAS

    # Obtener o crear tipo de notificación
    tipo_recordatorio, _ = TiposNotificacion.objects.get_or_create(
        nombre="Recordatorio de actividad"
    )

    # Buscar horarios próximos
    proximos = HorariosParticipante.objects.filter(
        fecha_inicio__gte=ahora,
        fecha_inicio__lte=en_48_horas
    )

    print(f"\n=== Generando notificaciones ===")
    print(f"Fecha actual: {ahora}")
    print(f"Buscando hasta: {en_48_horas}")
    print(f"Horarios encontrados: {proximos.count()}")
    
    contador = 0
    for bloque in proximos:
        participante = bloque.participantes_id_participante
        fecha_evento = bloque.fecha_inicio
        lugar = bloque.notas or "lugar asignado"
        
        mensaje = f"Recordatorio: Tienes '{bloque.titulo}' programado el {fecha_evento.strftime('%d/%m/%Y a las %H:%M')} en {lugar}."

        print(f"\n  Procesando: {bloque.titulo}")
        print(f"    Fecha evento: {fecha_evento}")
        
        # Validar si el día es lectivo
        if not es_dia_lectivo(fecha_evento.date()):
            print(f"    ⊗ Día no lectivo")
            continue
        
        print(f"    ✓ Día lectivo")
        
        # Verificar si ya existe
        existe = Notificaciones.objects.filter(
            participantes_id_participante=participante,
            mensaje__contains=bloque.titulo,
            fecha__gte=ahora - timedelta(hours=2)
        ).exists()
        
        if existe:
            print(f"    ⊗ Notificación duplicada")
            continue

        print(f"    ✓ Creando notificación...")
        
        # Crear notificación
        resultado = crear_notificacion_validada(
            mensaje=mensaje,
            fecha_deseada=ahora,
            participante=participante,
            tipo_notificacion=tipo_recordatorio,
            auto_reprogramar=False
        )
        
        if resultado['success']:
            contador += 1
            print(f"    ✓✓ ID: {resultado['notificacion'].id_notificacion}")
        else:
            print(f"    ✗✗ Error: {resultado['mensaje']}")
    
    print(f"\n=== Total creadas: {contador} ===\n")
    return contador