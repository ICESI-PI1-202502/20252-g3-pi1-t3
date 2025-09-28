# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.utils.text import slugify
import os

class Actividades(models.Model):
    id_actividad = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    requiere_inscripcion = models.CharField(max_length=1, blank=True, null=True)
    modalidad = models.CharField(max_length=1, blank=True, null=True)
    aforo = models.FloatField(blank=True, null=True)
    fecha_apertura_ins = models.DateField(blank=True, null=True)
    fecha_cierre_ins = models.DateField(blank=True, null=True)
    tipos_actividad_id_tipo = models.ForeignKey('TiposActividad', models.DO_NOTHING, db_column='tipos_actividad_id_tipo', blank=True, null=True)
    id_tipo = models.FloatField(blank=True, null=True)
    actividades_grupos_id_actividad_grupo = models.ForeignKey('ActividadesGrupos', models.DO_NOTHING, db_column='actividades_grupos_id_actividad_grupo', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'actividades'


class ActividadesGrupos(models.Model):
    id_actividad_grupo = models.FloatField(primary_key=True)
    grupos_actividad_id_grupo_actividad = models.OneToOneField('GruposActividad', models.DO_NOTHING, db_column='grupos_actividad_id_grupo_actividad')
    actividades_id_actividad = models.FloatField()

    class Meta:
        managed = False
        db_table = 'actividades_grupos'


class AgendaPsicologos(models.Model):
    id_agenda_slot = models.FloatField(primary_key=True)
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado_slot = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'agenda_psicologos'


class Asistencias(models.Model):
    id_asistencia = models.FloatField(primary_key=True)
    fecha = models.DateField()
    estados_asistencia_id_estado_asistencia = models.ForeignKey('EstadosAsistencia', models.DO_NOTHING, db_column='estados_asistencia_id_estado_asistencia')
    participaciones_id_participacion = models.ForeignKey('Participaciones', models.DO_NOTHING, db_column='participaciones_id_participacion')

    class Meta:
        managed = False
        db_table = 'asistencias'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128, blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class CalificacionesActividad(models.Model):
    id_calificacion = models.FloatField(primary_key=True)
    actividades_id_actividad = models.ForeignKey(Actividades, models.DO_NOTHING, db_column='actividades_id_actividad')
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    estrellas = models.FloatField()
    comentario = models.CharField(max_length=500, blank=True, null=True)
    fecha = models.DateField()

    class Meta:
        managed = False
        db_table = 'calificaciones_actividad'
        unique_together = (('actividades_id_actividad', 'participantes_id_participante'),)


class Citas(models.Model):
    id_cita = models.FloatField(primary_key=True)
    fecha = models.DateField()
    motivo = models.CharField(max_length=200, blank=True, null=True)
    observaciones = models.CharField(max_length=500, blank=True, null=True)
    estados_cita_id_estado_cita = models.OneToOneField('EstadosCita', models.DO_NOTHING, db_column='estados_cita_id_estado_cita')
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    participantes_id_participante2 = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante2', related_name='citas_participantes_id_participante2_set')
    motivos_cita_id_motivo = models.OneToOneField('MotivosCita', models.DO_NOTHING, db_column='motivos_cita_id_motivo', blank=True, null=True)
    agenda_psicologos_id_agenda_slot = models.ForeignKey(AgendaPsicologos, models.DO_NOTHING, db_column='agenda_psicologos_id_agenda_slot', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'citas'


class Clasificaciones(models.Model):
    pk = models.CompositePrimaryKey('torneos_id_torneo', 'equipos_id_equipo')
    torneos_id_torneo = models.ForeignKey('Torneos', models.DO_NOTHING, db_column='torneos_id_torneo')
    equipos_id_equipo = models.ForeignKey('Equipos', models.DO_NOTHING, db_column='equipos_id_equipo')
    pj = models.FloatField()
    pg = models.FloatField()
    pe = models.FloatField()
    pp = models.FloatField()
    gf = models.FloatField()
    gc = models.FloatField()
    pts = models.FloatField()

    class Meta:
        managed = False
        db_table = 'clasificaciones'


class Disciplinas(models.Model):
    id_disciplina = models.FloatField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=80)

    class Meta:
        managed = False
        db_table = 'disciplinas'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200, blank=True, null=True)
    action_flag = models.IntegerField()
    change_message = models.TextField(blank=True, null=True)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField(blank=True, null=True)
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Equipos(models.Model):
    id_equipo = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=100)
    fecha_creacion = models.DateField()
    cantidad_personas = models.FloatField(blank=True, null=True)
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    disciplinas_id_disciplina = models.ForeignKey(Disciplinas, models.DO_NOTHING, db_column='disciplinas_id_disciplina', blank=True, null=True)
    capacidad_min = models.FloatField(blank=True, null=True)
    capacidad_max = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'equipos'


class EquiposParticipantes(models.Model):
    id = models.BigAutoField(primary_key=True) 
    equipos_id_equipo = models.ForeignKey('Equipos', models.DO_NOTHING, db_column='equipos_id_equipo')
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    id_participante1 = models.BigIntegerField()  
    class Meta:
        managed = False
        db_table = 'equipos_participantes'
        unique_together = (('equipos_id_equipo', 'participantes_id_participante'),)



class EstadosAsistencia(models.Model):
    id_estado_asistencia = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'estados_asistencia'


class EstadosCita(models.Model):
    id_estado_cita = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=30)
    citas_id_cita = models.OneToOneField(Citas, models.DO_NOTHING, db_column='citas_id_cita')

    class Meta:
        managed = False
        db_table = 'estados_cita'


class EstadosParticipacion(models.Model):
    id_estado_participacion = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'estados_participacion'


class EstadosTorneo(models.Model):
    id_estado_torneo = models.FloatField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=30)
    class Meta:
        managed = False
        db_table = 'estados_torneo'


class FkProysocCoordinador(models.Model):
    pk = models.CompositePrimaryKey('participantes_id_participante', 'proyectos_sociales_id_proyecto')
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    proyectos_sociales_id_proyecto = models.ForeignKey('ProyectosSociales', models.DO_NOTHING, db_column='proyectos_sociales_id_proyecto')

    class Meta:
        managed = False
        db_table = 'fk_proysoc_coordinador'


class Grupos(models.Model):
    id_grupo = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'grupos'


def actividad_upload_to(instance, filename):
    # id del grupo (ejemplo: 3)
    grupo_id = instance.grupos_id_grupo.id_grupo
    # slug del nombre (ejemplo: futbol)
    actividad_slug = slugify(instance.nombre)
    # extensión original
    ext = filename.split('.')[-1]
    # nombre de archivo fijo
    filename = f"{actividad_slug}.{ext}"
    # ruta final: media/<grupo_id>/<actividad_slug>/<actividad_slug>.ext
    return os.path.join(str(grupo_id), actividad_slug, filename)

class GruposActividad(models.Model):
    id_grupo_actividad = models.FloatField(primary_key=True)
    grupos_id_grupo = models.ForeignKey(Grupos, models.DO_NOTHING, db_column='grupos_id_grupo')
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    imagen = models.ImageField(upload_to=actividad_upload_to, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'grupos_actividad'


class HistorialCitas(models.Model):
    id_historial = models.FloatField(primary_key=True)
    citas_id_cita = models.ForeignKey(Citas, models.DO_NOTHING, db_column='citas_id_cita')
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    fecha = models.DateField()
    nota = models.CharField(max_length=2000)

    class Meta:
        managed = False
        db_table = 'historial_citas'


class HistorialParticipaciones(models.Model):
    id_historial = models.FloatField(primary_key=True)
    participaciones_id_participacion = models.ForeignKey('Participaciones', models.DO_NOTHING, db_column='participaciones_id_participacion')
    fecha = models.DateField()
    nota = models.CharField(max_length=1000)

    class Meta:
        managed = False
        db_table = 'historial_participaciones'


class HorariosParticipante(models.Model):
    id_horario = models.FloatField(primary_key=True)
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    titulo = models.CharField(max_length=150)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    fuente_manual = models.CharField(max_length=1, blank=True, null=True)
    actividades_id_actividad = models.ForeignKey(Actividades, models.DO_NOTHING, db_column='actividades_id_actividad', blank=True, null=True)
    citas_id_cita = models.ForeignKey(Citas, models.DO_NOTHING, db_column='citas_id_cita', blank=True, null=True)
    partidos_id_partido = models.ForeignKey('Partidos', models.DO_NOTHING, db_column='partidos_id_partido', blank=True, null=True)
    notas = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'horarios_participante'
        unique_together = (('participantes_id_participante', 'fecha_inicio', 'fecha_fin'),)


class InscripcionesPsu(models.Model):
    id_inscripcion_psu = models.FloatField(primary_key=True)
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    proyectos_sociales_id_proyecto = models.ForeignKey('ProyectosSociales', models.DO_NOTHING, db_column='proyectos_sociales_id_proyecto')
    fecha_inscripcion = models.DateField()
    estados_participacion_id_estado_participacion = models.ForeignKey(EstadosParticipacion, models.DO_NOTHING, db_column='estados_participacion_id_estado_participacion')

    class Meta:
        managed = False
        db_table = 'inscripciones_psu'
        unique_together = (('participantes_id_participante', 'proyectos_sociales_id_proyecto'),)


class MotivosCita(models.Model):
    id_motivo = models.FloatField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=80)
    citas_id_cita = models.OneToOneField(Citas, models.DO_NOTHING, db_column='citas_id_cita', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'motivos_cita'


class Notificaciones(models.Model):
    id_notificacion = models.FloatField(primary_key=True)
    mensaje = models.CharField(max_length=500)
    fecha = models.DateField()
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    tipos_notificacion_id_tipo_notificacion = models.ForeignKey('TiposNotificacion', models.DO_NOTHING, db_column='tipos_notificacion_id_tipo_notificacion')

    class Meta:
        managed = False
        db_table = 'notificaciones'


class Participaciones(models.Model):
    id_participacion = models.FloatField(primary_key=True)
    fecha_inscripcion = models.DateField()
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    actividades_id_actividad = models.ForeignKey(Actividades, models.DO_NOTHING, db_column='actividades_id_actividad')
    roles_participacion_id_rol_participacion = models.ForeignKey('RolesParticipacion', models.DO_NOTHING, db_column='roles_participacion_id_rol_participacion')
    estados_participacion_id_estado_participacion = models.ForeignKey(EstadosParticipacion, models.DO_NOTHING, db_column='estados_participacion_id_estado_participacion')
    equipos_id_equipo = models.ForeignKey(Equipos, models.DO_NOTHING, db_column='equipos_id_equipo', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'participaciones'
        unique_together = (('participantes_id_participante', 'actividades_id_actividad'),)


class Participantes(models.Model):
    id_participante = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.CharField(unique=True, max_length=150)
    semestre = models.FloatField(blank=True, null=True)
    estado_activo = models.CharField(max_length=1, blank=True, null=True)
    roles_id_rol = models.ForeignKey('Roles', models.DO_NOTHING, db_column='roles_id_rol')
    facultad = models.CharField(max_length=80, blank=True, null=True)
    programa = models.CharField(max_length=120, blank=True, null=True)
    genero = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'participantes'


class Partidos(models.Model):
    id_partido = models.FloatField(primary_key=True)
    torneos_id_torneo = models.ForeignKey('Torneos', models.DO_NOTHING, db_column='torneos_id_torneo')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)
    equipos_id_equipo = models.ForeignKey(Equipos, models.DO_NOTHING, db_column='equipos_id_equipo')
    equipos_id_equipo2 = models.ForeignKey(Equipos, models.DO_NOTHING, db_column='equipos_id_equipo2', related_name='partidos_equipos_id_equipo2_set')
    marcador_a = models.FloatField(blank=True, null=True)
    marcador_b = models.FloatField(blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'partidos'


class Preferencias(models.Model):
    id_preferencia = models.FloatField(primary_key=True)
    participantes_id_participante = models.OneToOneField(Participantes, models.DO_NOTHING, db_column='participantes_id_participante')
    fecha_registro = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'preferencias'


class PreferenciasActividades(models.Model):
    id_preferencia_actividad = models.FloatField(primary_key=True)
    preferencias_id_preferencia = models.ForeignKey(Preferencias, models.DO_NOTHING, db_column='preferencias_id_preferencia')
    actividades_id_actividad = models.ForeignKey(Actividades, models.DO_NOTHING, db_column='actividades_id_actividad')

    class Meta:
        managed = False
        db_table = 'preferencias_actividades'
        unique_together = (('preferencias_id_preferencia', 'actividades_id_actividad'),)


class ProyectosSociales(models.Model):
    id_proyecto = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=1000, blank=True, null=True)
    coordinador_id = models.FloatField()
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    aforo = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'proyectos_sociales'


class Roles(models.Model):
    id_rol = models.FloatField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'roles'


class RolesParticipacion(models.Model):
    id_rol_participacion = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'roles_participacion'


class TiposActividad(models.Model):
    id_tipo = models.FloatField(primary_key=True)
    nombre_tipo = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'tipos_actividad'


class TiposNotificacion(models.Model):
    id_tipo_notificacion = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'tipos_notificacion'


class Torneos(models.Model):
    id_torneo = models.BigAutoField(db_column="id_torneo", primary_key=True) 
    nombre = models.CharField(max_length=150)
    disciplinas_id_disciplina = models.ForeignKey(Disciplinas, models.DO_NOTHING, db_column='disciplinas_id_disciplina')
    fecha_inicio = models.DateTimeField()
    fecha_fin    = models.DateTimeField()
    estados_torneo_id_estado_torneo = models.ForeignKey(EstadosTorneo,models.DO_NOTHING,db_column='estados_torneo_id_estado_torneo'
)
    reglas_elegibilidad = models.CharField(max_length=1000, blank=True, null=True)
    aforo_equipos = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'torneos'


class TorneosEquipos(models.Model):
    id = models.BigAutoField(primary_key=True)  # NEW surrogate PK
    torneos_id_torneo = models.ForeignKey('Torneos', models.DO_NOTHING, db_column='torneos_id_torneo')
    equipos_id_equipo = models.ForeignKey('Equipos', models.DO_NOTHING, db_column='equipos_id_equipo')

    class Meta:
        managed = False
        db_table = 'torneos_equipos'
        unique_together = (('torneos_id_torneo', 'equipos_id_equipo'),)