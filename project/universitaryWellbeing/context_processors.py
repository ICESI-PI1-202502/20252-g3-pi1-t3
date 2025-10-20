def user_role(request):
    """Agrega información del rol del usuario al contexto global"""
    context = {}
    
    if request.user.is_authenticated:
        try:
            from universitaryWellbeing.models import Participantes
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