"""
Sistema de Control Anti-Spam para Notificaciones
Usa hash_unicidad para prevenir duplicados
"""

from django.utils import timezone
from datetime import timedelta
import hashlib
from universitaryWellbeing.models import Notificaciones, TiposNotificacion


class ControlNotificacionesContextual:
    """Previene notificaciones duplicadas usando hash único"""
    
    @staticmethod
    def generar_hash_unicidad(participante_id, tipo_notif, actividad_id=None, contexto=None):
        """
        Genera hash único MD5
        Ejemplo: "123_Reconocimiento_45_hito_10" -> "a1b2c3d4..."
        """
        componentes = [
            str(participante_id),
            tipo_notif,
            str(actividad_id) if actividad_id else "global",
            contexto if contexto else "general"
        ]
        hash_str = "_".join(componentes)
        return hashlib.md5(hash_str.encode()).hexdigest()
    
    @staticmethod
    def ya_existe_notificacion(participante, tipo_notif, actividad=None, contexto=None, ventana_horas=None):
        """
        Verifica si ya existe notificación idéntica
        
        Args:
            participante: Objeto Participante
            tipo_notif: Nombre del tipo ('Reconocimiento', 'Inasistencia', 'Encuesta')
            actividad: Objeto Actividad (opcional)
            contexto: String para diferenciar (ej: 'hito_10', 'dias_7')
            ventana_horas: Si se especifica, solo verifica dentro de este período
        
        Returns:
            bool: True si ya existe (NO enviar de nuevo)
        """
        actividad_id = actividad.id_actividad if actividad else None
        hash_unico = ControlNotificacionesContextual.generar_hash_unicidad(
            participante.id_participante,
            tipo_notif,
            actividad_id,
            contexto
        )
        
        filtro = {
            'participantes_id_participante': participante,
            'tipos_notificacion_id_tipo_notificacion__nombre': tipo_notif,
            'hash_unicidad': hash_unico
        }
        
        # Ventana temporal opcional (para inasistencias que se repiten)
        if ventana_horas:
            limite_tiempo = timezone.now() - timedelta(hours=ventana_horas)
            filtro['created_at__gte'] = limite_tiempo
        
        return Notificaciones.objects.filter(**filtro).exists()
    
    @staticmethod
    def registrar_notificacion(participante, tipo_notif, mensaje, actividad=None, contexto=None):
        """
        Registra notificación con control de duplicados
        
        Returns:
            Notificacion creada o None si ya existía
        """
        actividad_id = actividad.id_actividad if actividad else None
        hash_unico = ControlNotificacionesContextual.generar_hash_unicidad(
            participante.id_participante,
            tipo_notif,
            actividad_id,
            contexto
        )
        
        # Verificar si ya existe (doble check)
        if Notificaciones.objects.filter(hash_unicidad=hash_unico).exists():
            return None
        
        tipo = TiposNotificacion.objects.get(nombre=tipo_notif)
        
        notif = Notificaciones.objects.create(
            participantes_id_participante=participante,
            tipos_notificacion_id_tipo_notificacion=tipo,
            mensaje=mensaje,
            fecha=timezone.now(),
            leida=False,
            actividad_relacionada=actividad,
            contexto_hito=contexto,
            hash_unicidad=hash_unico
        )
        
        return notif