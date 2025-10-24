from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta, date
from universitaryWellbeing.models import (
    Notificaciones, 
    TiposNotificacion, 
    Participantes,
    HorariosParticipante
)
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
    
    Args:
        fecha_programada: datetime.date o datetime.datetime
        tipo_notificacion: TiposNotificacion object, str (nombre), int (ID), o Mock
    
    Returns:
        tuple: (puede_enviar: bool, motivo: str)
    """
    # Validación de entrada - verificar lista PRIMERO
    if isinstance(tipo_notificacion, (list, tuple)):
        return False, "Tipo de notificación debe ser un objeto, ID o nombre, no una lista"
    
    # Luego verificar si es None o vacío
    if not tipo_notificacion:
        return False, "Tipo de notificación vacío o inválido"
    
    # Obtener nombre del tipo según el tipo de entrada
    nombre_tipo = None
    
    try:
        # Primero intentar obtener atributo 'nombre' (funciona con objetos reales y Mocks)
        if hasattr(tipo_notificacion, 'nombre'):
            nombre_tipo = tipo_notificacion.nombre
            
        elif isinstance(tipo_notificacion, str):
            # Es un string (nombre del tipo)
            nombre_tipo = tipo_notificacion
            
        elif isinstance(tipo_notificacion, int):
            # Es un ID, buscar en BD (solo en producción)
            try:
                tipo_obj = TiposNotificacion.objects.get(id_tipo_notificacion=tipo_notificacion)
                nombre_tipo = tipo_obj.nombre
            except TiposNotificacion.DoesNotExist:
                return False, f"Tipo de notificación con ID {tipo_notificacion} no encontrado"
            except Exception:
                # En tests sin BD, puede fallar
                return False, "No se puede acceder a la base de datos"
        else:
            return False, f"Tipo de notificación inválido: {type(tipo_notificacion).__name__}"
            
    except Exception as e:
        return False, f"Error al procesar tipo de notificación: {str(e)}"
    
    if not nombre_tipo:
        return False, "No se pudo determinar el nombre del tipo de notificación"
    
    # Convertir fecha a date si es datetime
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
    
    # Retornar early si tipo_notificacion es inválido
    if not puede_enviar and not tipo_notificacion:
        return {
            'success': False,
            'motivo': motivo,
            'mensaje': motivo,
            'notificacion': None
        }
    
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
                
                fecha_original_str = fecha_deseada.strftime('%Y-%m-%d') if isinstance(fecha_deseada, (date, datetime)) else str(fecha_deseada)
                fecha_final_str = fecha_final.strftime('%Y-%m-%d') if isinstance(fecha_final, (date, datetime)) else str(fecha_final)
                
                motivo = f"Reprogramada de {fecha_original_str} a {fecha_final_str}"
            else:
                return {
                    'success': False,
                    'motivo': 'No se encontró día lectivo disponible en los próximos 30 días',
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
            
            return {
                'success': True,
                'motivo': motivo,
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
                'motivo': f"Error al crear notificación: {str(e)}",
                'mensaje': f"Error al crear notificación: {str(e)}",
                'notificacion': None
            }
    
    return {
        'success': False,
        'motivo': motivo,
        'mensaje': motivo,
        'notificacion': None
    }


# ============================================
# VISTAS
# ============================================

@login_required
def ver_notificaciones(request):
    """
    Muestra TODAS las notificaciones del usuario en una página completa
    """
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
            # Usar timezone.now() y localtime para Colombia
            fecha = timezone.make_aware(
                datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M'),
                timezone.get_current_timezone()
            )
            
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


@login_required
@require_POST
def marcar_notificacion_leida(request, notificacion_id):
    """
    Marca una notificación como leída (llamada desde el dropdown)
    """
    try:
        notificacion = Notificaciones.objects.get(
            id_notificacion=notificacion_id,
            participantes_id_participante__user_id=request.user.id
        )
        notificacion.leida = True
        notificacion.save()
        
        return JsonResponse({'success': True})
    except Notificaciones.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Notificación no encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)