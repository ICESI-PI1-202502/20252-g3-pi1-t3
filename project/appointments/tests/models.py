from django.db import models
from django.contrib.auth.models import User, Group

# --- BASES COMUNES (Roles / Participantes) ---

class Roles(models.Model):
    id_rol = models.BigAutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)
    # Evita constraint real a auth_group en tests
    group = models.ForeignKey(
        Group, models.DO_NOTHING, db_column="group_id",
        null=True, blank=True, related_name="+", db_constraint=False
    )
    class Meta:
        managed = True
        db_table = "roles"
        app_label = "tests_appointments"


class Participantes(models.Model):
    id_participante = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    correo = models.CharField(max_length=150, unique=True, null=True)
    semestre = models.BigIntegerField(blank=True, null=True)
    estado_activo = models.CharField(max_length=1, blank=True, null=True)
    facultad = models.CharField(max_length=80, blank=True, null=True)
    programa = models.CharField(max_length=120, blank=True, null=True)
    genero = models.CharField(max_length=20, blank=True, null=True)
    roles_id_rol = models.ForeignKey(Roles, models.DO_NOTHING, db_column="roles_id_rol")
    # Evita constraint real a auth_user en tests
    user = models.ForeignKey(
        User, models.CASCADE, db_column="user", related_name="+", db_constraint=False
    )
    class Meta:
        managed = True
        db_table = "participantes"
        app_label = "tests_appointments"


# --- AGENDA DEL PROFESIONAL ---

class AgendaPsicologos(models.Model):
    id_agenda_slot = models.BigAutoField(primary_key=True)
    participantes_id_participante = models.ForeignKey(
        Participantes, models.DO_NOTHING, db_column="participantes_id_participante"
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    estado_slot = models.CharField(max_length=20)
    # Producción puede no tenerlo, pero las views lo leen si existe:
    lugar = models.CharField(max_length=150, blank=True, null=True)
    class Meta:
        managed = True
        db_table = "agenda_psicologos"
        app_label = "tests_appointments"


# --- CITA + ESTADO (OneToOne), MOTIVO, HISTORIAL ---

class Citas(models.Model):
    id_cita = models.BigAutoField(primary_key=True)
    fecha = models.DateTimeField()
    motivo = models.CharField(max_length=200, blank=True, null=True)
    observaciones = models.CharField(max_length=500, blank=True, null=True)

    # En producción es OneToOne NO NULL. En tests lo dejamos NULL para romper el ciclo.
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
    # Igual que arriba: mantener estructura pero sin forzar ciclo
    motivos_cita_id_motivo = models.OneToOneField(
        "MotivosCita", models.DO_NOTHING,
        db_column="motivos_cita_id_motivo", null=True, blank=True
    )
    class Meta:
        managed = True
        db_table = "citas"
        app_label = "tests_appointments"


class EstadosCita(models.Model):
    id_estado_cita = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=30)
    # En prod es OneToOne hacia Citas. Lo dejamos igual.
    citas_id_cita = models.OneToOneField(
        Citas, models.DO_NOTHING, db_column="citas_id_cita", related_name="+"
    )
    class Meta:
        managed = True
        db_table = "estados_cita"
        app_label = "tests_appointments"


class MotivosCita(models.Model):
    id_motivo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=80, unique=True)
    citas_id_cita = models.OneToOneField(
        Citas, models.DO_NOTHING, db_column="citas_id_cita", null=True, blank=True, related_name="+"
    )
    class Meta:
        managed = True
        db_table = "motivos_cita"
        app_label = "tests_appointments"


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
        app_label = "tests_appointments"


# --- CALENDARIO DEL PARTICIPANTE ---

class HorariosParticipante(models.Model):
    id_horario = models.BigAutoField(primary_key=True)
    participantes_id_participante = models.ForeignKey(
        Participantes, models.DO_NOTHING, db_column="participantes_id_participante"
    )
    titulo = models.CharField(max_length=150)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    fuente_manual = models.CharField(max_length=1)
    # Evitamos constraints reales a otras apps:
    actividades_id_actividad = models.ForeignKey(
        "Actividades", models.DO_NOTHING, db_column="actividades_id_actividad",
        null=True, blank=True, db_constraint=False, related_name="+"
    )
    citas_id_cita = models.ForeignKey(
        Citas, models.DO_NOTHING, db_column="citas_id_cita", null=True, blank=True
    )
    partidos_id_partido = models.ForeignKey(
        "Partidos", models.DO_NOTHING, db_column="partidos_id_partido",
        null=True, blank=True, db_constraint=False, related_name="+"
    )
    notas = models.CharField(max_length=500, blank=True, null=True)
    class Meta:
        managed = True
        db_table = "horarios_participante"
        app_label = "tests_appointments"
        unique_together = (("participantes_id_participante", "fecha_inicio", "fecha_fin"),)


# --- STUBS para apuntar FKs sin crear tablas de otras apps (no se usarán en tests) ---
class Actividades(models.Model):
    id_actividad = models.BigAutoField(primary_key=True)
    class Meta:
        managed = True
        db_table = "actividades"
        app_label = "tests_appointments"

class Partidos(models.Model):
    id_partido = models.BigAutoField(primary_key=True)
    class Meta:
        managed = True
        db_table = "partidos"
        app_label = "tests_appointments"
