# project\appointments\tests\models.py
from django.db import models
from django.contrib.auth.models import User, Group
 
##PORFAVOR CORRER LOS TEST CON python manage.py test appointments --keepdb

# ==========================================
# CONFIGURACIÓN GLOBAL
# ==========================================
APP_LABEL = 'tests_appointments'

# ==========================================
# MODELOS BASE
# ==========================================

class Grupos(models.Model):
    id_grupo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = True
        db_table = "grupos"
        app_label = APP_LABEL


class Roles(models.Model):
    id_rol = models.BigAutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)
    
    group = models.ForeignKey(
        Group, models.DO_NOTHING, db_column="group_id",
        null=True, blank=True, related_name="+", db_constraint=False
    )

    class Meta:
        managed = True
        db_table = "roles"
        app_label = APP_LABEL


class GruposActividad(models.Model):
    id_grupo_actividad = models.BigAutoField(primary_key=True, db_column="id_grupo_actividad")
    grupos_id_grupo = models.ForeignKey(Grupos, models.DO_NOTHING, db_column="grupos_id_grupo")
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    imagen = models.ImageField(upload_to="dummy/", blank=True, null=True)

    class Meta:
        managed = True
        db_table = "grupos_actividad"
        app_label = APP_LABEL


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
        managed = True
        db_table = 'tipos_participante'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre
    


class Participantes(models.Model):
    id_participante = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100, blank=True, null=True, default='')
    apellido = models.CharField(max_length=100, blank=True, null=True, default='')
    correo = models.CharField(max_length=150, unique=True)
    
    semestre = models.BigIntegerField(blank=True, null=True, default=None)
    estado_activo = models.CharField(max_length=1, blank=True, null=True, default=None)
    facultad = models.CharField(max_length=80, blank=True, null=True, default=None)
    programa = models.CharField(max_length=120, blank=True, null=True, default=None)
    genero = models.CharField(max_length=20, blank=True, null=True, default=None)

    roles_id_rol = models.ForeignKey(Roles, models.DO_NOTHING, db_column="roles_id_rol")

    tipo_participante = models.ForeignKey(
        TiposParticipante,
        models.DO_NOTHING,
        db_column="tipo_participante_id",
        blank=True,
        null=True,
        default=None
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user',
        related_name='+',
        db_constraint=False
    )

    class Meta:
        managed = True
        db_table = "participantes"
        app_label = APP_LABEL


# ==========================================
# MODELOS DE AGENDA Y CITAS
# ==========================================

class AgendaPsicologos(models.Model):
    id_agenda_slot = models.BigAutoField(primary_key=True)
    participantes_id_participante = models.ForeignKey(
        Participantes, models.DO_NOTHING, db_column="participantes_id_participante"
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    estado_slot = models.CharField(max_length=20)
    lugar = models.CharField(max_length=150, blank=True, null=True)
    
    class Meta:
        managed = True
        db_table = "agenda_psicologos"
        app_label = APP_LABEL


class Citas(models.Model):
    id_cita = models.BigAutoField(primary_key=True)
    fecha = models.DateTimeField()
    motivo = models.CharField(max_length=200, blank=True, null=True)
    observaciones = models.CharField(max_length=500, blank=True, null=True)

    estados_cita_id_estado_cita = models.OneToOneField(
        "EstadosCita", models.DO_NOTHING,
        db_column="estados_cita_id_estado_cita", null=True, blank=True
    )

    participantes_id_participante = models.ForeignKey(
        Participantes, models.DO_NOTHING, db_column="participantes_id_participante", related_name="+"
    )
    participantes_id_participante2 = models.ForeignKey(
        Participantes, models.DO_NOTHING, db_column="participantes_id_participante2", related_name="+"
    )
    agenda_psicologos_id_agenda_slot = models.ForeignKey(
        AgendaPsicologos, models.DO_NOTHING,
        db_column="agenda_psicologos_id_agenda_slot", null=True, blank=True
    )
    motivos_cita_id_motivo = models.OneToOneField(
        "MotivosCita", models.DO_NOTHING,
        db_column="motivos_cita_id_motivo", null=True, blank=True
    )
    
    class Meta:
        managed = True
        db_table = "citas"
        app_label = APP_LABEL


class EstadosCita(models.Model):
    id_estado_cita = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=30)
    citas_id_cita = models.OneToOneField(
        Citas, models.DO_NOTHING, db_column="citas_id_cita", related_name="+"
    )
    
    class Meta:
        managed = True
        db_table = "estados_cita"
        app_label = APP_LABEL


class MotivosCita(models.Model):
    id_motivo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=80, unique=True)
    citas_id_cita = models.OneToOneField(
        Citas, models.DO_NOTHING, db_column="citas_id_cita", null=True, blank=True, related_name="+"
    )
    
    class Meta:
        managed = True
        db_table = "motivos_cita"
        app_label = APP_LABEL


class HistorialCitas(models.Model):
    id_historial = models.BigAutoField(primary_key=True)
    citas_id_cita = models.ForeignKey(Citas, models.DO_NOTHING, db_column="citas_id_cita")
    participantes_id_participante = models.ForeignKey(
        Participantes, models.DO_NOTHING, db_column="participantes_id_participante"
    )
    fecha = models.DateTimeField()
    nota = models.CharField(max_length=2000)
    
    class Meta:
        managed = True
        db_table = "historial_citas"
        app_label = APP_LABEL


# ==========================================
# MODELOS DE ACTIVIDADES
# ==========================================

class TiposActividad(models.Model):
    id_tipo = models.FloatField(primary_key=True)
    nombre_tipo = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "tipos_actividad"
        app_label = APP_LABEL


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
        TiposActividad, models.DO_NOTHING, db_column="tipos_actividad_id_tipo",
        blank=True, null=True
    )

    class Meta:
        managed = True
        db_table = "actividades"
        app_label = APP_LABEL


class ActividadesGrupos(models.Model):
    id_actividad_grupo = models.BigAutoField(primary_key=True)
    grupos_actividad = models.ForeignKey(GruposActividad, models.DO_NOTHING, db_column="grp_act_id")
    actividad = models.ForeignKey(Actividades, models.DO_NOTHING, db_column="actividades_id_actividad")

    class Meta:
        managed = True
        db_table = "actividades_grupos"
        app_label = APP_LABEL


# ==========================================
# MODELOS DE HORARIOS
# ==========================================

class HorariosBloque(models.Model):
    id_horario_bloque = models.BigAutoField(primary_key=True)
    actividades_id_actividad = models.ForeignKey(
        Actividades, models.DO_NOTHING, db_column="actividades_id_actividad"
    )
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    profesor = models.CharField(max_length=150, blank=True, null=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "horarios_bloque"
        app_label = APP_LABEL


class HorariosActividad(models.Model):
    id_horario = models.BigAutoField(primary_key=True)
    actividades_id_actividad = models.ForeignKey(
        Actividades, models.DO_NOTHING, db_column="actividades_id_actividad"
    )
    horario_bloque = models.ForeignKey(
        HorariosBloque, models.DO_NOTHING, db_column="horario_bloque_id",
        null=True, blank=True
    )
    dia_semana = models.SmallIntegerField()

    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    profesor = models.CharField(max_length=150, blank=True, null=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "horarios_actividad"
        app_label = APP_LABEL


# ==========================================
# MODELOS DE PARTICIPACIONES
# ==========================================

class RolesParticipacion(models.Model):
    id_rol_participacion = models.BigAutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = "roles_participacion"
        app_label = APP_LABEL


class EstadosParticipacion(models.Model):
    id_estado_participacion = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = "estados_participacion"
        app_label = APP_LABEL


class Participaciones(models.Model):
    id_participacion = models.BigAutoField(primary_key=True)
    participantes_id_participante = models.ForeignKey(
        Participantes,
        models.DO_NOTHING,
        db_column="participantes_id_participante"
    )
    actividades_id_actividad = models.ForeignKey(
        Actividades,
        models.DO_NOTHING,
        db_column="actividades_id_actividad"
    )
    fecha_inscripcion = models.DateTimeField(blank=True, null=True)
    fecha_finalizacion = models.DateTimeField(blank=True, null=True)
    
    roles_participacion_id_rol_participacion = models.ForeignKey(
        RolesParticipacion,
        models.DO_NOTHING,
        db_column="roles_participacion_id_rol_participacion",
        blank=True,
        null=True
    )
    estados_participacion_id_estado_participacion = models.ForeignKey(
        EstadosParticipacion,
        models.DO_NOTHING,
        db_column="estados_participacion_id_estado_participacion",
        blank=True,
        null=True
    )

    class Meta:
        managed = True
        db_table = "participaciones"
        app_label = APP_LABEL


# ==========================================
# ✅ MODELO CORREGIDO: HorariosParticipante
# Ahora coincide con el modelo de producción
# ==========================================


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
        managed = True
        db_table = 'horarios_participante'
        unique_together = (('participantes_id_participante', 'fecha_inicio', 'fecha_fin'),)
        app_label = APP_LABEL
# ==========================================
# MODELOS DE CALIFICACIONES
# ==========================================

class Partidos(models.Model):
    """Modelo para partidos deportivos (necesario para HorariosParticipante)"""
    id_partido = models.BigAutoField(primary_key=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(blank=True, null=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)
    estado = models.CharField(max_length=20)
    
    class Meta:
        managed = True
        db_table = "partidos"
        app_label = APP_LABEL


class CalificacionesActividad(models.Model):
    id_calificacion = models.BigAutoField(primary_key=True)
    actividades_id_actividad = models.ForeignKey(
        Actividades, models.DO_NOTHING, db_column="actividades_id_actividad"
    )
    participantes_id_participante = models.ForeignKey(
        Participantes, models.DO_NOTHING, db_column="participantes_id_participante"
    )
    estrellas = models.SmallIntegerField(null=True, blank=True, default=0)

    class Meta:
        managed = True
        db_table = "calificaciones_actividad"
        unique_together = (("actividades_id_actividad", "participantes_id_participante"),)
        app_label = APP_LABEL