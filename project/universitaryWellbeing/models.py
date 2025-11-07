from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User,Group
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
import os

class Actividades(models.Model):
    id_actividad = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=500, blank=True, null=True)

    requiere_inscripcion = models.CharField(max_length=1, blank=True, null=True)
    modalidad = models.CharField(max_length=1, blank=True, null=True)
    aforo = models.FloatField(blank=True, null=True)

    fecha_apertura_ins = models.DateTimeField(blank=True, null=True)
    fecha_cierre_ins = models.DateTimeField(blank=True, null=True)

    tipos_actividad_id_tipo = models.ForeignKey(
        'TiposActividad',
        models.DO_NOTHING,
        db_column='tipos_actividad_id_tipo',
        blank=True, null=True
    )

    #id_tipo = models.FloatField(blank=True, null=True)
    actividades_grupos_id_actividad_grupo = models.ForeignKey(
        'ActividadesGrupos',
        models.DO_NOTHING,
        db_column='act_grup_id',
        blank=True, null=True
    )

    promedio_calificacion = models.FloatField(default=0, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'actividades'


# Estos son nuevos modelos para la solucón del problema
class HorariosBloque(models.Model):
    id_horario_bloque = models.BigAutoField(primary_key=True)
    actividades_id_actividad = models.ForeignKey(
        Actividades, models.DO_NOTHING, db_column='actividades_id_actividad'
    )
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    profesor = models.CharField(max_length=150, blank=True, null=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'horarios_bloque'

class HorariosActividad(models.Model):
    id_horario = models.BigAutoField(primary_key=True)
    actividades_id_actividad = models.ForeignKey(
        Actividades, models.DO_NOTHING, db_column='actividades_id_actividad'
    )
    horario_bloque = models.ForeignKey(
        HorariosBloque, models.DO_NOTHING, db_column='horario_bloque_id', null=True, blank=True
    )
    dia_semana = models.SmallIntegerField()

    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    profesor = models.CharField(max_length=150, blank=True, null=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'horarios_actividad'


class ActividadesGrupos(models.Model):
    id_actividad_grupo = models.BigAutoField(primary_key=True)
    grupos_actividad = models.ForeignKey(
        'GruposActividad',
        models.DO_NOTHING,
        db_column='grp_act_id'     # <- antes: grupos_actividad_id_grupo_actividad
    )
    actividad = models.ForeignKey(
        'Actividades',
        models.DO_NOTHING,
        db_column='actividades_id_actividad'
    )

    class Meta:
        managed = False
        db_table = 'actividades_grupos'



class AgendaPsicologos(models.Model):

    id_agenda_slot = models.BigAutoField(primary_key=True)
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    estado_slot = models.CharField(max_length=20)
    class Meta:
        managed = False
        db_table = 'agenda_psicologos'

class Asistencias(models.Model):

    id_asistencia = models.BigAutoField(primary_key=True)
    fecha = models.DateTimeField()
    estados_asistencia_id_estado_asistencia = models.ForeignKey('EstadosAsistencia', models.DO_NOTHING, db_column='estados_asistencia_id_estado_asistencia')
    participaciones_id_participacion = models.ForeignKey('Participaciones', models.DO_NOTHING, db_column='participaciones_id_participacion')
    class Meta:
        managed = False
        db_table = 'asistencias'


class AuthGroup(models.Model):

    name = models.CharField(unique=True, max_length=150)
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

    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


CALIFICACION_CHOICES = [(i, str(i)) for i in range(6)]

class CalificacionesActividad(models.Model):
    id_calificacion = models.BigAutoField(primary_key=True)
    actividades_id_actividad = models.ForeignKey('Actividades', on_delete=models.DO_NOTHING, db_column='actividades_id_actividad')
    participantes_id_participante = models.ForeignKey('Participantes', on_delete=models.DO_NOTHING, db_column='participantes_id_participante')
    
    estrellas = models.SmallIntegerField(
        null=True, blank=True, choices=CALIFICACION_CHOICES,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        default=0
    )
    comentario = models.CharField(max_length=500, blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)  # Por defecto se asigna la fecha actual al crear la calificación

    class Meta:
        managed = False  
        db_table = 'calificaciones_actividad'
        unique_together = (('actividades_id_actividad', 'participantes_id_participante'),)  # Única combinación de actividad y participante

    def save(self, *args, **kwargs):
        if not self.fecha:
            self.fecha = models.DateTimeField(auto_now_add=True)  # Si no se pasa la fecha, se pone la actual
        super().save(*args, **kwargs)

class Citas(models.Model):

    id_cita = models.BigAutoField(primary_key=True)
    fecha = models.DateTimeField()
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
    pj = models.IntegerField()
    pg = models.IntegerField()
    pe = models.IntegerField()
    pp = models.IntegerField()
    gf = models.IntegerField()
    gc = models.IntegerField()
    pts = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'clasificaciones'

class Disciplinas(models.Model):
    id_disciplina = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=80)
    class Meta:
        managed = False
        db_table = 'disciplinas'

class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(User, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'

class DjangoContentType(models.Model):

    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)

class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'django_migrations'

class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'django_session'

class Equipos(models.Model):
    id_equipo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField()
    cantidad_personas = models.BigIntegerField(blank=True, null=True)
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    disciplinas_id_disciplina = models.ForeignKey(Disciplinas, models.DO_NOTHING, db_column='disciplinas_id_disciplina', blank=True, null=True)
    capacidad_min = models.IntegerField(blank=True, null=True)
    capacidad_max = models.IntegerField(blank=True, null=True)
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

class EstadosAsistencia(models.Model):

    id_estado_asistencia = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=30)
    class Meta:
        managed = False
        db_table = 'estados_asistencia'
class EstadosCita(models.Model):

    id_estado_cita = models.BigAutoField(primary_key=True)
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

    id_estado_torneo = models.BigAutoField(primary_key=True)
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
    id_grupo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = False
        db_table = 'grupos'


def actividad_upload_to(instance, filename):

    grupo_id = instance.grupos_id_grupo.id_grupo

    actividad_slug = slugify(instance.nombre)

    ext = filename.split('.')[-1]

    filename = f"{actividad_slug}.{ext}"
    
    return os.path.join(str(grupo_id), actividad_slug, filename)

class GruposActividad(models.Model):
    
    id_grupo_actividad = models.BigAutoField(
        db_column='id_grupo_actividad', primary_key=True
    )
    grupos_id_grupo = models.ForeignKey(
        Grupos, models.DO_NOTHING, db_column='grupos_id_grupo'
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    imagen = models.ImageField(upload_to=actividad_upload_to, blank=True, null=True)

    class Meta:
        managed = False            # (seguimos sin migrar esta tabla desde Django)
        db_table = 'grupos_actividad'


class HistorialCitas(models.Model):

    id_historial = models.BigAutoField(primary_key=True)
    citas_id_cita = models.ForeignKey(Citas, models.DO_NOTHING, db_column='citas_id_cita')
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    fecha = models.DateTimeField()
    nota = models.CharField(max_length=2000)
    class Meta:
        managed = False
        db_table = 'historial_citas'

class HistorialParticipaciones(models.Model):

    id_historial = models.BigAutoField(primary_key=True)
    participaciones_id_participacion = models.ForeignKey('Participaciones', models.DO_NOTHING, db_column='participaciones_id_participacion')
    fecha = models.DateTimeField()
    nota = models.CharField(max_length=1000)
    class Meta:
        managed = False
        db_table = 'historial_participaciones'

class HorariosParticipante(models.Model):

    id_horario = models.BigAutoField(primary_key=True)
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    titulo = models.CharField(max_length=150)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    fuente_manual = models.CharField(max_length=1)
    actividades_id_actividad = models.ForeignKey(Actividades, models.DO_NOTHING, db_column='actividades_id_actividad', blank=True, null=True)
    citas_id_cita = models.ForeignKey(Citas, models.DO_NOTHING, db_column='citas_id_cita', blank=True, null=True)
    partidos_id_partido = models.ForeignKey('Partidos', models.DO_NOTHING, db_column='partidos_id_partido', blank=True, null=True)
    notas = models.CharField(max_length=500, blank=True, null=True)
    # A unique constraint could not be introspected.
    class Meta:
        managed = False
        db_table = 'horarios_participante'
        unique_together = (('participantes_id_participante', 'fecha_inicio', 'fecha_fin'),)

def clean(self):
    # Buscar solapamientos con otros eventos del mismo participante
    conflictos = HorariosParticipante.objects.filter(
        participantes_id_participante=self.participantes_id_participante,
        fecha_inicio__lt=self.fecha_fin,
        fecha_fin__gt=self.fecha_inicio
    ).exclude(id_horario=self.id_horario)
    if conflictos.exists():
        raise ValidationError("Conflicto de hora: ya tienes una actividad, cita o materia en este horario.")

class InscripcionesPsu(models.Model):

    id_inscripcion_psu = models.BigAutoField(primary_key=True)
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    proyectos_sociales_id_proyecto = models.ForeignKey('ProyectosSociales', models.DO_NOTHING, db_column='proyectos_sociales_id_proyecto')
    fecha_inscripcion = models.DateTimeField()
    estados_participacion_id_estado_participacion = models.ForeignKey(EstadosParticipacion, models.DO_NOTHING, db_column='estados_participacion_id_estado_participacion')
    class Meta:
        managed = False
        db_table = 'inscripciones_psu'
        unique_together = (('participantes_id_participante', 'proyectos_sociales_id_proyecto'),)

class MotivosCita(models.Model):

    id_motivo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=80)
    citas_id_cita = models.OneToOneField(Citas, models.DO_NOTHING, db_column='citas_id_cita', blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'motivos_cita'


class Notificaciones(models.Model):
    id_notificacion = models.BigAutoField(primary_key=True)
    mensaje = models.CharField(max_length=500)
    fecha = models.DateTimeField()
    participantes_id_participante = models.ForeignKey(
        'Participantes',
        models.DO_NOTHING,
        db_column='participantes_id_participante'
    )
    tipos_notificacion_id_tipo_notificacion = models.ForeignKey(
        'TiposNotificacion',
        models.DO_NOTHING,
        db_column='tipos_notificacion_id_tipo_notificacion'
    )
    leida = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    # ✅ NUEVOS CAMPOS (coinciden con el SQL)
    actividad_relacionada = models.ForeignKey(
        'Actividades',
        models.DO_NOTHING,
        db_column='actividad_relacionada',
        null=True,
        blank=True,
        help_text="Actividad específica relacionada"
    )
    
    contexto_hito = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Ej: 'hito_10', 'inasistencia_7dias'"
    )
    
    hash_unicidad = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Hash único para evitar duplicados"
    )

    class Meta:
        managed = False
        db_table = 'notificaciones'
    
    def __str__(self):
        return f"{self.mensaje[:50]}..."

class Participaciones(models.Model):

    id_participacion = models.BigAutoField(primary_key=True)
    fecha_inscripcion = models.DateTimeField()
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    actividades_id_actividad = models.ForeignKey(Actividades, models.DO_NOTHING, db_column='actividades_id_actividad')
    roles_participacion_id_rol_participacion = models.ForeignKey('RolesParticipacion', models.DO_NOTHING, db_column='roles_participacion_id_rol_participacion')
    estados_participacion_id_estado_participacion = models.ForeignKey(EstadosParticipacion, models.DO_NOTHING, db_column='estados_participacion_id_estado_participacion')
    equipos_id_equipo = models.ForeignKey(Equipos, models.DO_NOTHING, db_column='equipos_id_equipo', blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'participaciones'
        unique_together = (('participantes_id_participante', 'actividades_id_actividad'),)

class TiposParticipante(models.Model):
    id_tipo_participante = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    
    # Campos útiles para tu contexto universitario
    requiere_validacion = models.BooleanField(
        default=False,
        help_text='Requiere aprobación de admin (ej: Docentes)'
    )
    puede_crear_actividades = models.BooleanField(
        default=False,
        help_text='Puede crear actividades (ej: Coordinadores, Docentes)'
    )
    activo = models.BooleanField(
        default=True,
        help_text='Tipo disponible para selección'
    )
    orden = models.IntegerField(
        default=0,
        help_text='Orden de aparición en formularios'
    )
    
    class Meta:
        managed = False
        db_table = 'tipos_participante'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre
    
class Participantes(models.Model):

    id_participante = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.CharField(unique=True, max_length=150)
    semestre = models.BigIntegerField(blank=True, null=True)
    estado_activo = models.CharField(max_length=1, blank=True, null=True)
    roles_id_rol = models.ForeignKey('Roles', models.DO_NOTHING, db_column='roles_id_rol')
    facultad = models.CharField(max_length=80, blank=True, null=True)
    programa = models.CharField(max_length=120, blank=True, null=True)
    genero = models.CharField(max_length=20, blank=True, null=True)
    user = models.ForeignKey(User, db_column='user', to_field='id', on_delete=models.CASCADE)
    tipo_participante = models.ForeignKey(
        'TiposParticipante',
        models.DO_NOTHING,
        db_column='tipo_participante_id',
        blank=True,
        null=True,
        verbose_name='Tipo de Usuario'
    )
    
    class Meta:
        managed = False
        db_table = 'participantes'

class Partidos(models.Model):

    id_partido = models.BigAutoField(primary_key=True)
    torneos_id_torneo = models.ForeignKey('Torneos', models.DO_NOTHING, db_column='torneos_id_torneo')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(blank=True, null=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)
    equipos_id_equipo = models.ForeignKey(Equipos, models.DO_NOTHING, db_column='equipos_id_equipo')
    equipos_id_equipo2 = models.ForeignKey(Equipos, models.DO_NOTHING, db_column='equipos_id_equipo2', related_name='partidos_equipos_id_equipo2_set')
    marcador_a = models.IntegerField(blank=True, null=True)
    marcador_b = models.IntegerField(blank=True, null=True)
    estado = models.CharField(max_length=20)
    class Meta:
        managed = False
        db_table = 'partidos'

class Preferencias(models.Model):

    id_preferencia = models.BigAutoField(primary_key=True)
    participantes_id_participante = models.OneToOneField(Participantes, models.DO_NOTHING, db_column='participantes_id_participante')
    fecha_registro = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'preferencias'

class PreferenciasActividades(models.Model):
    id_preferencia_actividad = models.BigAutoField(primary_key=True)
    preferencia = models.ForeignKey(Preferencias, models.DO_NOTHING, db_column='preferencias_id_preferencia', related_name='actividades')
    tipo_actividad = models.ForeignKey('TiposActividad', models.DO_NOTHING, db_column='tipos_id_actividad')
    class Meta:
        managed = False
        db_table = 'preferencias_actividades'
        unique_together = (('preferencia', 'tipo_actividad'),)

class ProyectosSociales(models.Model):

    id_proyecto = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=1000, blank=True, null=True)
    coordinador_id = models.BigIntegerField()
    fecha_inicio = models.DateTimeField(blank=True, null=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    aforo = models.BigIntegerField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'proyectos_sociales'

class Roles(models.Model):
    id_rol = models.BigAutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)
    grupo_d = models.OneToOneField(
        Group, 
        on_delete=models.SET_NULL,  # Cambiado de DO_NOTHING
        db_column='group_id', 
        null=True, 
        blank=True
    )

    def save(self, *args, **kwargs):
        # Auto-crear grupo si el rol requiere permisos
        ROLES_CON_PERMISOS = ['coordinador', 'profesor', 'psicologo', 'admin_bienestar', 'super_admin']
        
        if self.nombre_rol.lower() in ROLES_CON_PERMISOS and not self.grupo_d:
            # Crear grupo con nombre capitalizado
            nombre_grupo = self.nombre_rol.replace('_', ' ').title()
            grupo, created = Group.objects.get_or_create(name=nombre_grupo)
            self.grupo_d = grupo
        
        super().save(*args, **kwargs)

    class Meta:
        managed = False
        db_table = 'roles'

class RolesParticipacion(models.Model):

    id_rol_participacion = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    class Meta:
        managed = False
        db_table = 'roles_participacion'


class TiposActividad(models.Model):
    id_tipo = models.FloatField(primary_key=True)
    nombre_tipo = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipos_actividad'


class TiposNotificacion(models.Model):

    id_tipo_notificacion = models.BigAutoField(primary_key=True)
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
    limite_inscripcion = models.DateTimeField(blank=True, null=True)

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



class ConfiguracionNotificaciones(models.Model):
    """Configuración completa del sistema de notificaciones"""
    
    # ============ RECONOCIMIENTOS ============
    hitos_reconocimiento = models.CharField(
        max_length=100,
        default='10,20,30,40,50',
        help_text='Hitos separados por comas (ej: 10,20,30)'
    )
    reconocimientos_activos = models.BooleanField(
        default=True,
        help_text='¿Enviar reconocimientos automáticos?'
    )
    
    # ============ INASISTENCIAS ============
    dias_sin_asistir_alerta = models.IntegerField(
        default=7,
        help_text='Días sin asistir para generar alerta'
    )
    dias_repetir_alerta_inasistencia = models.IntegerField(
        default=7,
        help_text='Cada cuántos días repetir alerta (0 = no repetir)'
    )
    alertas_inasistencia_activas = models.BooleanField(
        default=True,
        help_text='¿Enviar alertas de inasistencia?'
    )
    asistencias_minimas_para_alertar = models.IntegerField(
        default=1,
        help_text='Debe haber asistido antes para alertar'
    )
    
    # ============ ENCUESTAS ============
    dias_despues_cierre_encuesta = models.IntegerField(
        default=7,
        help_text='Días después del cierre para enviar encuesta'
    )
    asistencias_minimas_encuesta = models.IntegerField(
        default=3,
        help_text='Asistencias mínimas para enviar encuesta'
    )
    encuestas_activas = models.BooleanField(
        default=True,
        help_text='¿Enviar encuestas automáticas?'
    )
    
    # ============ CITAS ============
    recordatorio_cita_dias_antes = models.IntegerField(
        default=1,
        help_text='Días antes de la cita para recordatorio'
    )
    recordatorio_cita_horas_antes = models.IntegerField(
        default=2,
        help_text='Horas antes de la cita para recordatorio'
    )
    recordatorios_citas_activos = models.BooleanField(
        default=True,
        help_text='¿Enviar recordatorios de citas?'
    )
    
    # ============ EVENTOS (Torneos/Proyectos) ============
    recordatorio_evento_dias_antes = models.IntegerField(
        default=3,
        help_text='Días antes del evento'
    )
    recordatorio_evento_dia_antes = models.BooleanField(
        default=True,
        help_text='¿Recordatorio el día anterior?'
    )
    recordatorios_eventos_activos = models.BooleanField(
        default=True,
        help_text='¿Enviar recordatorios de eventos?'
    )
    
    # ============ CAMPOS EXISTENTES (mantener) ============
    umbral_riesgo_critico = models.IntegerField(default=2)
    umbral_baja_asistencia = models.IntegerField(default=5)
    dias_inactividad = models.IntegerField(default=14)
    dias_riesgo_critico = models.IntegerField(default=21)
    asistencias_reconocimiento = models.IntegerField(default=10)
    margen_proximo_reconocimiento = models.IntegerField(default=2)
    asistencias_destacado = models.IntegerField(default=15)
    envio_automatico = models.BooleanField(default=True)
    frecuencia_envio = models.CharField(max_length=20, default='semanal')
    emails_staff = models.TextField(default='luis.gluis.g.io.com@gmail.com')
    
    ultima_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'configuracion_notificaciones'
        verbose_name = 'Configuración de Notificaciones'
        verbose_name_plural = 'Configuración de Notificaciones'
    
    def save(self, *args, **kwargs):
        self.pk = 1  # Singleton
        super().save(*args, **kwargs)
    
    @classmethod
    def obtener_config(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config
    
    def obtener_hitos(self):
        """Retorna lista de hitos como enteros"""
        return [int(h.strip()) for h in self.hitos_reconocimiento.split(',')]
    
    def obtener_emails_staff(self):
        return [email.strip() for email in self.emails_staff.split(',') if email.strip()]