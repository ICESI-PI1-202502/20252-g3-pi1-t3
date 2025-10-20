from django.db import models
from django.contrib.auth.models import User, Group

##PORFAVOR CORRER LOS TEST CON python manage.py test social_projects --keepdb
class Roles(models.Model):
    id_rol = models.BigAutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)
    # evitar constraint real a auth_group
    group = models.ForeignKey(
        Group, models.DO_NOTHING, db_column="group_id",
        null=True, blank=True, related_name="+", db_constraint=False
    )
    class Meta:
        managed = True
        db_table = "roles"

class Participantes(models.Model):
    id_participante = models.BigAutoField(primary_key=True)
    correo = models.CharField(max_length=150, unique=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    semestre = models.BigIntegerField(blank=True, null=True)
    estado_activo = models.CharField(max_length=1, blank=True, null=True)
    facultad = models.CharField(max_length=80, blank=True, null=True)
    programa = models.CharField(max_length=120, blank=True, null=True)
    genero = models.CharField(max_length=20, blank=True, null=True)
    roles_id_rol = models.ForeignKey(Roles, models.DO_NOTHING, db_column="roles_id_rol")
    # evitar constraint real a auth_user
    user = models.ForeignKey(
        User, models.CASCADE, db_column="user", related_name="+", db_constraint=False
    )
    class Meta:
        managed = True
        db_table = "participantes"

# --- PSU ---
class ProyectosSociales(models.Model):
    id_proyecto = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=1000, blank=True, null=True)
    coordinador_id = models.BigIntegerField()  
    fecha_inicio = models.DateTimeField(blank=True, null=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    aforo = models.BigIntegerField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = "proyectos_sociales"

class EstadosParticipacion(models.Model):
    id_estado_participacion = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=30)
    class Meta:
        managed = True
        db_table = "estados_participacion"

class InscripcionesPsu(models.Model):
    id_inscripcion_psu = models.BigAutoField(primary_key=True)
    participantes_id_participante = models.ForeignKey(
        Participantes, models.DO_NOTHING, db_column="participantes_id_participante"
    )
    proyectos_sociales_id_proyecto = models.ForeignKey(
        ProyectosSociales, models.DO_NOTHING, db_column="proyectos_sociales_id_proyecto"
    )
    fecha_inscripcion = models.DateTimeField()
    estados_participacion_id_estado_participacion = models.ForeignKey(
        EstadosParticipacion, models.DO_NOTHING,
        db_column="estados_participacion_id_estado_participacion"
    )
    class Meta:
        managed = True
        db_table = "inscripciones_psu"
        unique_together = (("participantes_id_participante", "proyectos_sociales_id_proyecto"),)
