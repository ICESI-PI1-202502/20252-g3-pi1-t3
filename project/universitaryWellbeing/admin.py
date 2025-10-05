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
# READ-ONLY MODELS
# -----------------------

class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

readonly_models = [
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