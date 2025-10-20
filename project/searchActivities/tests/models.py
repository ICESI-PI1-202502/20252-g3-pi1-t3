# searchActivities/tests/models.py
from django.db import models
from django.contrib.auth.models import User, Group


##PORFAVOR CORRER LOS TEST CON python manage.py test searchActivites --keepdb
##PORFAVOR CORRER LOS TEST CON python manage.py test searchActivites --keepdb
class TiposActividad(models.Model):
    # En prod es FloatField; mantenemos Float para que coincida.
    id_tipo = models.FloatField(primary_key=True)
    nombre_tipo = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "tipos_actividad"


# --------------- Grupos / GruposActividad (mínimos) ---------------
class Grupos(models.Model):
    id_grupo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = True
        db_table = "grupos"


class GruposActividad(models.Model):
    id_grupo_actividad = models.BigAutoField(primary_key=True)
    grupos_id_grupo = models.ForeignKey(Grupos, models.DO_NOTHING, db_column="grupos_id_grupo")
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    # omitimos ImageField para evitar storage real en tests
    imagen = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "grupos_actividad"


# ---------------- ActividadesGrupos (para tener la columna act_grup_id) ----------------
class ActividadesGrupos(models.Model):
    id_actividad_grupo = models.BigAutoField(primary_key=True)
    # En prod: db_column='grp_act_id'
    grupos_actividad = models.ForeignKey(GruposActividad, models.DO_NOTHING, db_column="grp_act_id")
    actividad = models.ForeignKey("Actividades", models.DO_NOTHING, db_column="actividades_id_actividad")

    class Meta:
        managed = True
        db_table = "actividades_grupos"


# ---------------- Actividades (alineado al modelo real) ----------------
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
        TiposActividad, models.DO_NOTHING, db_column="tipos_actividad_id_tipo", blank=True, null=True
    )
    # existe también la columna id_tipo (Float) en prod
    id_tipo = models.FloatField(blank=True, null=True)

    # FK a ActividadesGrupos con db_column='act_grup_id'
    actividades_grupos_id_actividad_grupo = models.ForeignKey(
        ActividadesGrupos, models.DO_NOTHING, db_column="act_grup_id", blank=True, null=True
    )

    promedio_calificacion = models.FloatField(default=0, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "actividades"


# ---------------- Horarios (bloques + días) ----------------
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


class HorariosActividad(models.Model):
    id_horario = models.BigAutoField(primary_key=True)
    actividades_id_actividad = models.ForeignKey(
        Actividades, models.DO_NOTHING, db_column="actividades_id_actividad"
    )
    horario_bloque = models.ForeignKey(
        HorariosBloque, models.DO_NOTHING, db_column="horario_bloque_id", null=True, blank=True
    )
    dia_semana = models.SmallIntegerField()

    # Campos adicionales que existen en el modelo real (pero el view no los usa)
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    profesor = models.CharField(max_length=150, blank=True, null=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "horarios_actividad"


# ---------------- Roles / Participantes ----------------
class Roles(models.Model):
    id_rol = models.BigAutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)
    # usamos FK al Group sin constraint real
    group = models.ForeignKey(
        Group, models.DO_NOTHING, db_column="group_id", null=True, blank=True, related_name="+", db_constraint=False
    )

    class Meta:
        managed = True
        db_table = "roles"


class Participantes(models.Model):
    id_participante = models.BigAutoField(primary_key=True)

    # ¡En el modelo real existen estos campos! Inclúyelos para evitar errores SELECT *
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)

    correo = models.CharField(max_length=150, unique=True)
    semestre = models.BigIntegerField(blank=True, null=True)
    estado_activo = models.CharField(max_length=1, blank=True, null=True)
    facultad = models.CharField(max_length=80, blank=True, null=True)
    programa = models.CharField(max_length=120, blank=True, null=True)
    genero = models.CharField(max_length=20, blank=True, null=True)

    roles_id_rol = models.ForeignKey(Roles, models.DO_NOTHING, db_column="roles_id_rol")
    # Evitamos constraint real hacia auth_user
    user = models.ForeignKey(User, models.CASCADE, db_column="user", related_name="+", db_constraint=False)

    class Meta:
        managed = True
        db_table = "participantes"


# ---------------- CalificacionesActividad ----------------
class CalificacionesActividad(models.Model):
    id_calificacion = models.BigAutoField(primary_key=True)
    actividades_id_actividad = models.ForeignKey(
        Actividades, models.DO_NOTHING, db_column="actividades_id_actividad"
    )
    participantes_id_participante = models.ForeignKey(
        Participantes, models.DO_NOTHING, db_column="participantes_id_participante"
    )
    estrellas = models.SmallIntegerField(null=True, blank=True, default=0)
    comentario = models.CharField(max_length=500, blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "calificaciones_actividad"
        unique_together = (("actividades_id_actividad", "participantes_id_participante"),)
