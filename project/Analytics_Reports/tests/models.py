#project\Analytics_Reports\tests\models.py
from django.db import models
from django.contrib.auth.models import User

# Modelos de prueba para tests
class Roles(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)

    class Meta:
        app_label = 'analytics_reports_tests'
        db_table = 'roles'
        managed = True

class TiposActividad(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    nombre_tipo = models.CharField(max_length=100)

    class Meta:
        app_label = 'analytics_reports_tests'
        db_table = 'tipos_actividad'
        managed = True

class Participantes(models.Model):
    id_participante = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    semestre = models.IntegerField(null=True, blank=True)
    facultad = models.CharField(max_length=100, null=True, blank=True)
    genero = models.CharField(max_length=20, null=True, blank=True)
    estado_activo = models.CharField(max_length=1, default='S')
    roles_id_rol = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column='roles_id_rol')
 
    class Meta:
        app_label = 'analytics_reports_tests'
        db_table = 'participantes'
        managed = True

class Actividades(models.Model):
    id_actividad = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    tipos_actividad_id_tipo = models.ForeignKey(TiposActividad, on_delete=models.CASCADE, db_column='tipos_actividad_id_tipo')
    responsable = models.ForeignKey(Participantes, on_delete=models.SET_NULL, null=True, blank=True, related_name='actividades_responsable')

    class Meta:
        app_label = 'analytics_reports_tests'
        db_table = 'actividades'
        managed = True

class RolesParticipacion(models.Model):
    id_rol_participacion = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)

    class Meta:
        app_label = 'analytics_reports_tests'
        db_table = 'roles_participacion'
        managed = True

class EstadosParticipacion(models.Model):
    id_estado_participacion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        app_label = 'analytics_reports_tests'
        db_table = 'estados_participacion'
        managed = True

class Participaciones(models.Model):
    id_participacion = models.AutoField(primary_key=True)
    fecha_inscripcion = models.DateField()
    fecha_finalizacion = models.DateField(null=True, blank=True)
    participantes_id_participante = models.ForeignKey(Participantes, on_delete=models.CASCADE, db_column='participantes_id_participante')
    actividades_id_actividad = models.ForeignKey(Actividades, on_delete=models.CASCADE, db_column='actividades_id_actividad')
    roles_participacion_id_rol_participacion = models.ForeignKey(RolesParticipacion, on_delete=models.CASCADE, db_column='roles_participacion_id_rol_participacion')
    estados_participacion_id_estado_participacion = models.ForeignKey(EstadosParticipacion, on_delete=models.CASCADE, db_column='estados_participacion_id_estado_participacion')

    class Meta:
        app_label = 'analytics_reports_tests'
        db_table = 'participaciones'
        managed = True

class EstadosAsistencia(models.Model):
    id_estado_asistencia = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        app_label = 'analytics_reports_tests'
        db_table = 'estados_asistencia'
        managed = True

class Asistencias(models.Model):
    id_asistencia = models.AutoField(primary_key=True)
    fecha = models.DateField()
    estados_asistencia_id_estado_asistencia = models.ForeignKey(EstadosAsistencia, on_delete=models.CASCADE, db_column='estados_asistencia_id_estado_asistencia')
    participaciones_id_participacion = models.ForeignKey(Participaciones, on_delete=models.CASCADE, db_column='participaciones_id_participacion')

    class Meta:
        app_label = 'analytics_reports_tests'
        db_table = 'asistencias'
        managed = True

class ConfiguracionNotificaciones(models.Model):
    id = models.AutoField(primary_key=True)
    asistencias_reconocimiento = models.IntegerField(default=10)
    margen_proximo_reconocimiento = models.IntegerField(default=2)
    asistencias_destacado = models.IntegerField(default=15)
    umbral_baja_asistencia = models.IntegerField(default=5)
    umbral_riesgo_critico = models.IntegerField(default=2)
    dias_inactividad = models.IntegerField(default=14)
    dias_riesgo_critico = models.IntegerField(default=21)
    asistencias_minimas_encuesta = models.IntegerField(default=3)
    dias_despues_cierre_encuesta = models.IntegerField(default=3)
    envio_automatico = models.BooleanField(default=False)
    frecuencia_envio = models.CharField(max_length=20, default='semanal')

    class Meta:
        app_label = 'analytics_reports_tests'
        db_table = 'configuracion_notificaciones'
        managed = True

    @classmethod
    def obtener_config(cls):
        config, _ = cls.objects.get_or_create(id=1)
        return config