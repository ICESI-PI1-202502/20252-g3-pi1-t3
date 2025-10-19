from django.db import models
from django.contrib.auth.models import User

class TiposActividad(models.Model):
    id_tipo = models.FloatField(primary_key=True)
    nombre_tipo = models.CharField(max_length=100)

    class Meta:
        managed = True
        db_table = 'tipos_actividad'

class Actividades(models.Model):
    id_actividad = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)
    fecha_inicio = models.DateTimeField(blank=True, null=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    requiere_inscripcion = models.CharField(max_length=1, blank=True, null=True)
    modalidad = models.CharField(max_length=1, blank=True, null=True)
    aforo = models.FloatField(blank=True, null=True)
    tipos_actividad = models.ForeignKey(TiposActividad, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'actividades'

class Participantes(models.Model):
    id_participante = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.CharField(unique=True, max_length=150)
    semestre = models.BigIntegerField(blank=True, null=True)
    estado_activo = models.CharField(max_length=1, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wellbeing_participantes')

    class Meta:
        managed = True
        db_table = 'participantes'

class Participaciones(models.Model):
    id_participacion = models.BigAutoField(primary_key=True)
    fecha_inscripcion = models.DateTimeField()
    participantes = models.ForeignKey(Participantes, on_delete=models.CASCADE)
    actividades = models.ForeignKey(Actividades, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'participaciones'
        unique_together = (('participantes', 'actividades'),)

class Asistencias(models.Model):
    id_asistencia = models.BigAutoField(primary_key=True)
    fecha = models.DateTimeField()
    estados_asistencia = models.ForeignKey('EstadosAsistencia', on_delete=models.CASCADE)
    participaciones = models.ForeignKey(Participaciones, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'asistencias'

class EstadosAsistencia(models.Model):
    id_estado_asistencia = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=30)

    class Meta:
        managed = True
        db_table = 'estados_asistencia'

class HistorialParticipaciones(models.Model):
    id_historial = models.BigAutoField(primary_key=True)
    participaciones = models.ForeignKey(Participaciones, on_delete=models.CASCADE)
    fecha = models.DateTimeField()
    nota = models.CharField(max_length=1000)

    class Meta:
        managed = True
        db_table = 'historial_participaciones'