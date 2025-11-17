from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)
print("🚨 signals.py CARGADO")

@receiver(m2m_changed, sender=User.groups.through)
def actualizar_rol_cuando_cambia_grupo(sender, instance, action, pk_set, **kwargs):
    """
    Sincroniza el rol del Participante cuando cambian los grupos del User.
    Prioridad: último grupo agregado o primer grupo disponible.
    """
    print(f"🔔 Signal activado: action={action}, pk_set={pk_set}, user={instance.username}")
    
    # Solo actuamos cuando se agregan o eliminan grupos
    if action not in ["post_add", "post_remove", "post_clear"]:
        return
    
    try:
        from universitaryWellbeing.models import Roles, Participantes
        
        # Verificar que el usuario tenga un participante asociado
        try:
            participante = Participantes.objects.get(user=instance)
        except Participantes.DoesNotExist:
            logger.warning(f"⚠️ User {instance.username} no tiene Participante asociado")
            return
        
        # Obtener todos los grupos actuales del usuario
        grupos_actuales = instance.groups.all()
        
        if not grupos_actuales.exists():
            logger.info(f"ℹ️ User {instance.username} no tiene grupos asignados")
            return
        
        # Intentar encontrar un rol para alguno de los grupos
        # Prioridad: último grupo agregado (si es post_add) o primer grupo con rol
        grupos_a_revisar = grupos_actuales
        
        if action == "post_add" and pk_set:
            # Priorizar el grupo recién agregado
            grupos_a_revisar = grupos_actuales.filter(id__in=pk_set)
        
        rol_encontrado = None
        for grupo in grupos_a_revisar:
            try:
                rol = Roles.objects.get(grupo_d=grupo)
                rol_encontrado = rol
                logger.info(f"✅ Rol encontrado: {rol.nombre_rol} para grupo {grupo.name}")
                break
            except Roles.DoesNotExist:
                continue
        
        # Si no se encontró rol en grupos priorizados, buscar en todos
        if not rol_encontrado:
            for grupo in grupos_actuales:
                try:
                    rol = Roles.objects.get(grupo_d=grupo)
                    rol_encontrado = rol
                    break
                except Roles.DoesNotExist:
                    continue
        
        if rol_encontrado:
            if participante.roles_id_rol != rol_encontrado:
                participante.roles_id_rol = rol_encontrado
                participante.save()
                logger.info(f"✅ Rol actualizado: {instance.username} -> {rol_encontrado.nombre_rol}")
                print(f"✅ ROL ACTUALIZADO: {instance.username} -> {rol_encontrado.nombre_rol}")
            else:
                logger.info(f"ℹ️ Rol ya estaba correcto: {rol_encontrado.nombre_rol}")
        else:
            logger.warning(f"⚠️ Ningún grupo de {instance.username} tiene rol asociado")
            print(f"⚠️ NINGÚN GRUPO TIENE ROL ASOCIADO")
    
    except Exception as e:
        logger.error(f"❌ Error en signal actualizar_rol_cuando_cambia_grupo: {e}", exc_info=True)
        print(f"❌ ERROR EN SIGNAL: {e}")