# management_CADI/tests/models.py
from django.db import models
from django.contrib.auth.models import User

##PORFAVOR CORRER LOS TEST CON python manage.py test management_CADI --keepdb

# ==========================================
# MODELOS BASE
# ==========================================

class Grupos(models.Model):
    id_grupo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = True
        db_table = "grupos"
        app_label = 'management_cadi_tests'


class GruposActividad(models.Model):
    id_grupo_actividad = models.BigAutoField(primary_key=True, db_column="id_grupo_actividad")
    grupos_id_grupo = models.ForeignKey(Grupos, models.DO_NOTHING, db_column="grupos_id_grupo")
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    imagen = models.ImageField(upload_to="dummy/", blank=True, null=True)

    class Meta:
        managed = True
        db_table = "grupos_actividad"
        app_label = 'management_cadi_tests'


class TiposActividad(models.Model):
    id_tipo = models.FloatField(primary_key=True)
    nombre_tipo = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "tipos_actividad"
        app_label = 'management_cadi_tests'


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
        app_label = 'management_cadi_tests'


class ActividadesGrupos(models.Model):
    id_actividad_grupo = models.BigAutoField(primary_key=True)
    grupos_actividad = models.ForeignKey(GruposActividad, models.DO_NOTHING, db_column="grp_act_id")
    actividad = models.ForeignKey(Actividades, models.DO_NOTHING, db_column="actividades_id_actividad")

    class Meta:
        managed = True
        db_table = "actividades_grupos"
        app_label = 'management_cadi_tests'


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
        app_label = 'management_cadi_tests'


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
        app_label = 'management_cadi_tests'


# ==========================================
# MODELOS DE USUARIOS Y ROLES
# ==========================================

class Roles(models.Model):
    id_rol = models.BigAutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = "roles"
        app_label = 'management_cadi_tests'


class TiposParticipante(models.Model):
    id_tipo_participante = models.BigAutoField(primary_key=True)
    nombre_tipo = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "tipos_participante"
        app_label = 'management_cadi_tests'


class Participantes(models.Model):
    id_participante = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100, blank=True, null=True, default='')
    apellido = models.CharField(max_length=100, blank=True, null=True, default='')
    correo = models.CharField(max_length=150, unique=True)
    
    # Campos adicionales
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
        app_label = 'management_cadi_tests'


# ==========================================
# MODELOS DE PARTICIPACIONES
# ==========================================

class RolesParticipacion(models.Model):
    id_rol_participacion = models.BigAutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = "roles_participacion"
        app_label = 'management_cadi_tests'


class EstadosParticipacion(models.Model):
    id_estado_participacion = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = "estados_participacion"
        app_label = 'management_cadi_tests'


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
        app_label = 'management_cadi_tests'


# ==========================================
# MODELOS DE HORARIOS DE PARTICIPANTES
# ==========================================

class HorariosParticipante(models.Model):
    id_horario_participante = models.BigAutoField(primary_key=True)
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
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "horarios_participante"
        app_label = 'management_cadi_tests'


# ==========================================
# MODELOS DE CALIFICACIONES
# ==========================================

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
        app_label = 'management_cadi_tests'