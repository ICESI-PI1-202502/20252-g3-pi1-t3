from universitaryWellbeing.models import Notificaciones, Participantes

#def user_rol(request):  # ← Nombre de la función
#    if request.user.is_authenticated:
#        try:
#            participante = request.user.participantes_set.first()
#            if participante and participante.roles_id_rol:
#                return {
#                    'user_rol': participante.roles_id_rol.nombre_rol.title(),
#                    'user_grupos': request.user.groups.all()
#                }
#        except:
#            pass
#    return {'user_rol': None, 'user_grupos': []}


# universitaryWellbeing/context_processors.py
# Agregar esto a settings.py en TEMPLATES['OPTIONS']['context_processors']:
# 'universitaryWellbeing.context_processors.user_role_processor',


# universitaryWellbeing/context_processors.py
# Agregar esto a settings.py en TEMPLATES['OPTIONS']['context_processors']:
# 'universitaryWellbeing.context_processors.user_role_processor',

def user_rol(request):
    """
    Context processor que agrega el rol del usuario a todas las plantillas
    """
    context = {
        'user_rol': None,
        'es_coordinador': False,
        'es_profesor': False,
        'es_psicologo': False,
        'es_admin_bienestar': False,
        'es_super_admin': False,
    }
    
    if request.user.is_authenticated:
        try:
            # Obtener el participante asociado al usuario
            participante = request.user.participantes_set.first()
            
            if participante and participante.roles_id_rol:
                # Normalizar el nombre del rol (minúsculas y sin espacios extras)
                rol_nombre = participante.roles_id_rol.nombre_rol.lower().strip()
                
                # Agregar el nombre del rol original
                context['user_rol'] = participante.roles_id_rol.nombre_rol
                
                # Flags booleanos para cada rol (comparación flexible)
                context['es_coordinador'] = rol_nombre in ['coordinador', 'coordinator']
                context['es_profesor'] = rol_nombre in ['profesor', 'teacher']
                context['es_psicologo'] = rol_nombre in ['psicologo', 'psicólogo', 'psychologist']
                context['es_admin_bienestar'] = rol_nombre in ['admin_bienestar', 'admin bienestar']
                context['es_super_admin'] = rol_nombre in ['super_admin', 'super admin', 'superadmin']
                
        except Exception as e:
            # Log del error pero no interrumpir
            print(f"Error en context processor: {e}")
    
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