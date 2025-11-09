# management_CADI/tests/models.py
from django.db import models
from django.contrib.auth.models import User

##PORFAVOR CORRER LOS TEST CON python manage.py test management_CADI --keepdb
class Grupos(models.Model):
    id_grupo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = True
        db_table = "grupos"
        app_label = 'tests_management_CADI'  # <-- agrega esto


class GruposActividad(models.Model):
    id_grupo_actividad = models.BigAutoField(primary_key=True, db_column="id_grupo_actividad")
    grupos_id_grupo = models.ForeignKey(Grupos, models.DO_NOTHING, db_column="grupos_id_grupo")
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    # La vista real no usa la imagen, pero el modelo productivo sí la trae en SELECT.
    # Para evitar el error "column imagen does not exist", la ponemos aquí.
    # En settings de test ya forzamos InMemoryStorage.
    imagen = models.ImageField(upload_to="dummy/", blank=True, null=True)

    class Meta:
        managed = True
        db_table = "grupos_actividad"
        app_label = 'tests_management_CADI'  # <-- agrega esto


class TiposActividad(models.Model):
    # En productivo es FloatField; mantenemos eso para que el ORM no se queje con asignaciones
    id_tipo = models.FloatField(primary_key=True)
    nombre_tipo = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "tipos_actividad"
        app_label = 'tests_management_CADI'  # <-- agrega esto

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
        app_label = 'tests_management_CADI'  # <-- agrega esto


class ActividadesGrupos(models.Model):
    id_actividad_grupo = models.BigAutoField(primary_key=True)
    # Ojo con los nombres de columna: el view usa estos db_column en queries reales
    grupos_actividad = models.ForeignKey(GruposActividad, models.DO_NOTHING, db_column="grp_act_id")
    actividad = models.ForeignKey(Actividades, models.DO_NOTHING, db_column="actividades_id_actividad")

    class Meta:
        managed = True
        db_table = "actividades_grupos"
        app_label = 'tests_management_CADI'  # <-- agrega esto


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
        app_label = 'tests_management_CADI'  # <-- agrega esto


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

    # Estos campos no los usa la vista que estamos testeando, pero no estorban:
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    profesor = models.CharField(max_length=150, blank=True, null=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "horarios_actividad"
        app_label = 'tests_management_CADI'  # <-- agrega esto


# --------------------------
# Calificaciones y usuario
# --------------------------

class Roles(models.Model):
    id_rol = models.BigAutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = "roles"
        app_label = 'tests_management_CADI'  # <-- agrega esto


class Participantes(models.Model):
    id_participante = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    correo = models.CharField(max_length=150, unique=True)

    roles_id_rol = models.ForeignKey(Roles, models.DO_NOTHING, db_column="roles_id_rol")

    # Evitar choques con universitaryWellbeing.Participantes.user
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user',
        related_name='+',       # sin reverse accessor
        db_constraint=False     # no imponemos FK real en la DB de test
    )

    class Meta:
        managed = True
        db_table = "participantes"
        app_label = 'tests_management_CADI'  # <-- agrega esto


class CalificacionesActividad(models.Model):
    id_calificacion = models.BigAutoField(primary_key=True)
    actividades_id_actividad = models.ForeignKey(
        Actividades, models.DO_NOTHING, db_column="actividades_id_actividad"
    )
    participantes_id_participante = models.ForeignKey(
        Participantes, models.DO_NOTHING, db_column="participantes_id_participante"
    )
    # la vista hace Avg('estrellas'); default 0
    estrellas = models.SmallIntegerField(null=True, blank=True, default=0)

    class Meta:
        managed = True
        db_table = "calificaciones_actividad"
        unique_together = (("actividades_id_actividad", "participantes_id_participante"),)
        app_label = 'tests_management_CADI'  # <-- agrega esto