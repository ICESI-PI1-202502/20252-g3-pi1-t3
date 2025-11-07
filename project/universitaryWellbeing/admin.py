from django.contrib import admin
from .models import (
    Equipos, Torneos, Participantes, Disciplinas, Roles, Actividades,
    ActividadesGrupos, AgendaPsicologos, Asistencias, CalificacionesActividad,
    Citas, EquiposParticipantes, EstadosAsistencia,
    EstadosCita, EstadosParticipacion, EstadosTorneo, Grupos, GruposActividad,
    HistorialCitas, HistorialParticipaciones, HorariosParticipante,
    InscripcionesPsu, MotivosCita, Notificaciones, Participaciones, Partidos,
    Preferencias, PreferenciasActividades, ProyectosSociales,
    RolesParticipacion, TiposActividad, TiposNotificacion, TorneosEquipos
)
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
# -----------------------
# ADMIN PERSONALIZADOS
# -----------------------

@admin.register(Equipos)
class EquiposAdmin(admin.ModelAdmin):
    list_display = ('id_equipo', 'nombre', 'fecha_creacion', 'participantes_id_participante', 'disciplinas_id_disciplina')
    search_fields = ('nombre',)
    list_filter = ('fecha_creacion', 'disciplinas_id_disciplina')

@admin.register(Torneos)
class TorneosAdmin(admin.ModelAdmin):
    list_display = ('id_torneo', 'nombre', 'fecha_inicio', 'fecha_fin', 'aforo_equipos')
    search_fields = ('nombre',)
    list_filter = ('fecha_inicio', 'disciplinas_id_disciplina')

@admin.register(Participantes)
class ParticipantesAdmin(admin.ModelAdmin):
    list_display = ('id_participante', 'nombre', 'apellido', 'correo', 'estado_activo')
    search_fields = ('nombre', 'apellido', 'correo')
    list_filter = ('estado_activo', 'facultad', 'programa')

@admin.register(Roles)
class RolesAdmin(admin.ModelAdmin):
    list_display = ('id_rol', 'nombre_rol', 'grupo_d')
    search_fields = ('nombre_rol',)


# -----------------------
# ADMIN DE USUARIOS
# -----------------------

class UsuarioAdmin(BaseUserAdmin):
    # Solo agregar la columna personalizada, NO modificar fieldsets
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_grupos', 'is_staff']
    
    def get_grupos(self, obj):
        grupos = obj.groups.all()
        return ", ".join([g.name for g in grupos]) if grupos else "Sin roles"
    get_grupos.short_description = 'Roles Especiales'

# Desregistrar el User por defecto y registrar el personalizado
admin.site.unregister(User)
admin.site.register(User, UsuarioAdmin)

# -----------------------
# READ-ONLY MODELS
# -----------------------

# -----------------------
# READ-ONLY MODELS
# -----------------------

class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request): 
        return False
    def has_change_permission(self, request, obj=None): 
        return False
    def has_delete_permission(self, request, obj=None): 
        return False

# CRÍTICO: Excluir modelos que ya tienen admin personalizado
readonly_models = [
    # Equipos, Torneos, Participantes, Roles <- YA ESTÁN REGISTRADOS ARRIBA
    Disciplinas, Actividades, ActividadesGrupos, AgendaPsicologos,
    Asistencias, CalificacionesActividad, Citas,
    EquiposParticipantes, EstadosAsistencia, EstadosCita,
    EstadosParticipacion, EstadosTorneo, Grupos, GruposActividad,
    HistorialCitas, HistorialParticipaciones, HorariosParticipante,
    InscripcionesPsu, MotivosCita, Notificaciones, Participaciones,
    Partidos, Preferencias, PreferenciasActividades, ProyectosSociales,
    RolesParticipacion, TiposActividad, TiposNotificacion, TorneosEquipos
]

for model in readonly_models:
    admin.site.register(model, ReadOnlyAdmin)