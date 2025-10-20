from django.db import models
from django.contrib.auth.models import User, Group


##PORFAVOR CORRER LOS TEST CON python manage.py test tournaments --keepdb
class Disciplinas(models.Model):
    id_disciplina = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=80, unique=True)
    class Meta:
        managed = True
        db_table = "disciplinas"

class EstadosTorneo(models.Model):
    id_estado_torneo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)
    class Meta:
        managed = True
        db_table = "estados_torneo"

class Roles(models.Model):
    id_rol = models.BigAutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)
    group = models.ForeignKey(
        Group,
        models.DO_NOTHING,
        db_column="group_id",
        null=True,
        blank=True,
        related_name="+",
        db_constraint=False,   # ← evita crear la FK a auth_group
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
    # Evita choque con universitaryWellbeing.Participantes.user
    user = models.ForeignKey(
        User,
        models.CASCADE,
        db_column="user",
        related_name="+",
        db_constraint=False,   # ← evita crear la FK a auth_user
    )
    class Meta:
        managed = True
        db_table = "participantes"

class Equipos(models.Model):
    id_equipo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField()
    cantidad_personas = models.BigIntegerField(blank=True, null=True)
    participantes_id_participante = models.ForeignKey(
        Participantes, models.DO_NOTHING, db_column="participantes_id_participante"
    )
    disciplinas_id_disciplina = models.ForeignKey(
        Disciplinas, models.DO_NOTHING, db_column="disciplinas_id_disciplina",
        blank=True, null=True
    )
    capacidad_min = models.IntegerField(blank=True, null=True)
    capacidad_max = models.IntegerField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = "equipos"

class Torneos(models.Model):
    id_torneo = models.BigAutoField(primary_key=True, db_column="id_torneo")
    nombre = models.CharField(max_length=150)
    disciplinas_id_disciplina = models.ForeignKey(
        Disciplinas, models.DO_NOTHING, db_column="disciplinas_id_disciplina"
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    estados_torneo_id_estado_torneo = models.ForeignKey(
        EstadosTorneo, models.DO_NOTHING, db_column="estados_torneo_id_estado_torneo"
    )
    reglas_elegibilidad = models.CharField(max_length=1000, blank=True, null=True)
    aforo_equipos = models.BigIntegerField(blank=True, null=True)
    limite_inscripcion = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = "torneos"

class TorneosEquipos(models.Model):
    id = models.BigAutoField(primary_key=True)
    torneos_id_torneo = models.ForeignKey(Torneos, models.DO_NOTHING, db_column="torneos_id_torneo")
    equipos_id_equipo = models.ForeignKey(Equipos, models.DO_NOTHING, db_column="equipos_id_equipo")
    class Meta:
        managed = True
        db_table = "torneos_equipos"

class EquiposParticipantes(models.Model):
    id = models.BigAutoField(primary_key=True)
    equipos_id_equipo = models.ForeignKey(Equipos, models.DO_NOTHING, db_column="equipos_id_equipo")
    participantes_id_participante = models.ForeignKey(
        Participantes, models.DO_NOTHING, db_column="participantes_id_participante"
    )
    id_participante1 = models.BigIntegerField()
    class Meta:
        managed = True
        db_table = "equipos_participantes"


class Partidos(models.Model):
    id_partido = models.BigAutoField(primary_key=True)
    torneos_id_torneo = models.ForeignKey(
        Torneos, models.DO_NOTHING, db_column="torneos_id_torneo"
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(blank=True, null=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)
    equipos_id_equipo = models.ForeignKey(
        Equipos, models.DO_NOTHING, db_column="equipos_id_equipo", related_name="+"
    )
    equipos_id_equipo2 = models.ForeignKey(
        Equipos, models.DO_NOTHING, db_column="equipos_id_equipo2", related_name="+"
    )
    marcador_a = models.IntegerField(blank=True, null=True)
    marcador_b = models.IntegerField(blank=True, null=True)
    estado = models.CharField(max_length=20)

    class Meta:
        managed = True
        db_table = "partidos"

