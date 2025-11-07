# universitaryWellbeing/middleware.py
from django.contrib.auth.models import Group

class AsignarGrupoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                participante = request.user.participantes_set.first()
                if participante and participante.roles_id_rol:
                    rol = participante.roles_id_rol
                    
                    # Si el rol tiene grupo asociado, agregarlo al usuario
                    if rol.grupo_d and not request.user.groups.filter(pk=rol.grupo_d.pk).exists():
                        request.user.groups.add(rol.grupo_d)
            except:
                pass

        return self.get_response(request)