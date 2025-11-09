from universitaryWellbeing.models import Notificaciones, Participantes

def user_role(request):
    """Agrega información del rol del usuario al contexto global"""
    context = {}
    
    if request.user.is_authenticated:
        try:
            participante = Participantes.objects.select_related('roles_id_rol').get(user=request.user)
            context['user_participante'] = participante
            context['user_rol'] = participante.roles_id_rol.nombre_rol
        except Participantes.DoesNotExist:
            context['user_participante'] = None
            context['user_rol'] = None
    else:
        context['user_participante'] = None
        context['user_rol'] = None
    
    return context


def notificaciones_context(request):
    """
    Devuelve notificaciones y cantidad de no leídas para el usuario autenticado
    (se inyecta automáticamente en todas las plantillas)
    """
    if not request.user.is_authenticated:
        return {}

    # CAMBIO IMPORTANTE: Ordenar por ID descendente (más reciente primero)
    # El ID es auto-incremental, por lo que IDs más altos = más recientes
    notificaciones = Notificaciones.objects.filter(
        participantes_id_participante__user_id=request.user.id
    ).order_by('-id_notificacion')  # <- CAMBIO AQUÍ

    no_leidas = notificaciones.filter(leida=False).count()

    return {
        "notificaciones": notificaciones[:10],  # solo las primeras 10 para el menú
        "notificaciones_no_leidas": no_leidas,
    }