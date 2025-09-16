# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Actividades(models.Model):
    id_actividad = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    lugar = models.CharField(max_length=150)
    horario = models.DateField()
    requiere_inscripcion = models.CharField(max_length=1, blank=True, null=True)
    id_tipo = models.ForeignKey('TiposActividad', models.DO_NOTHING, db_column='id_tipo')

    class Meta:
        managed = False
        db_table = 'actividades'


class Asistencias(models.Model):
    id_asistencia = models.FloatField(primary_key=True)
    fecha = models.DateField()
    id_estado_asistencia = models.ForeignKey('EstadosAsistencia', models.DO_NOTHING, db_column='id_estado_asistencia')
    id_participacion = models.ForeignKey('Participaciones', models.DO_NOTHING, db_column='id_participacion')

    class Meta:
        managed = False
        db_table = 'asistencias'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150, blank=True, null=True)

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
    name = models.CharField(max_length=255, blank=True, null=True)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128, blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class Citas(models.Model):
    id_cita = models.FloatField(primary_key=True)
    fecha = models.DateField()
    motivo = models.CharField(max_length=200, blank=True, null=True)
    observaciones = models.CharField(max_length=500, blank=True, null=True)
    id_estado_cita = models.ForeignKey('EstadosCita', models.DO_NOTHING, db_column='id_estado_cita')
    id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='id_participante')
    id_psicologo = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='id_psicologo', related_name='citas_id_psicologo_set')

    class Meta:
        managed = False
        db_table = 'citas'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200, blank=True, null=True)
    action_flag = models.IntegerField()
    change_message = models.TextField(blank=True, null=True)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField(blank=True, null=True)
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Equipos(models.Model):
    id_equipo = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=100)
    fecha_creacion = models.DateField()
    cantidad_personas = models.FloatField(blank=True, null=True)
    responsable = models.ForeignKey('Participantes', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'equipos'


class EquiposParticipantes(models.Model):
    pk = models.CompositePrimaryKey('id_equipo', 'id_participante')
    id_equipo = models.ForeignKey(Equipos, models.DO_NOTHING, db_column='id_equipo')
    id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='id_participante')

    class Meta:
        managed = False
        db_table = 'equipos_participantes'


class EstadosAsistencia(models.Model):
    id_estado_asistencia = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'estados_asistencia'


class EstadosCita(models.Model):
    id_estado_cita = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'estados_cita'


class EstadosParticipacion(models.Model):
    id_estado_participacion = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'estados_participacion'


class Notificaciones(models.Model):
    id_notificacion = models.FloatField(primary_key=True)
    mensaje = models.CharField(max_length=500)
    fecha = models.DateField()
    id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='id_participante')
    id_tipo = models.ForeignKey('TiposNotificacion', models.DO_NOTHING, db_column='id_tipo')

    class Meta:
        managed = False
        db_table = 'notificaciones'


class Participaciones(models.Model):
    id_participacion = models.FloatField(primary_key=True)
    fecha_inscripcion = models.DateField()
    id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='id_participante')
    id_actividad = models.ForeignKey(Actividades, models.DO_NOTHING, db_column='id_actividad')
    id_rol_participacion = models.ForeignKey('RolesParticipacion', models.DO_NOTHING, db_column='id_rol_participacion')
    estado = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'participaciones'


class Participantes(models.Model):
    id_participante = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.CharField(unique=True, max_length=150)
    semestre = models.FloatField(blank=True, null=True)
    estado_activo = models.CharField(max_length=1, blank=True, null=True)
    id_rol = models.ForeignKey('Roles', models.DO_NOTHING, db_column='id_rol')

    class Meta:
        managed = False
        db_table = 'participantes'


class Roles(models.Model):
    id_rol = models.FloatField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'roles'


class RolesParticipacion(models.Model):
    id_rol_participacion = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'roles_participacion'


class TiposActividad(models.Model):
    id_tipo = models.FloatField(primary_key=True)
    nombre_tipo = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'tipos_actividad'


class TiposNotificacion(models.Model):
    id_tipo_notificacion = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'tipos_notificacion'
