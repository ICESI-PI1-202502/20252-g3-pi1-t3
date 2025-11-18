# management_CADI/tests/models.py
from django.db import models
from django.contrib.auth.models import User, Group
from django_resized import ResizedImageField
from django.utils.text import slugify

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

class Disciplinas(models.Model):
    id_disciplina = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=80)
    class Meta:
        managed = True
        db_table = 'disciplinas'

class EstadosTorneo(models.Model):

    id_estado_torneo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=30)
    class Meta:
        managed = True
        db_table = 'estados_torneo'

class Torneos(models.Model):
    id_torneo = models.BigAutoField(db_column="id_torneo", primary_key=True) 
    nombre = models.CharField(max_length=150)
    disciplinas_id_disciplina = models.ForeignKey(Disciplinas, models.DO_NOTHING, db_column='disciplinas_id_disciplina')
    fecha_inicio = models.DateTimeField()
    fecha_fin    = models.DateTimeField()
    estados_torneo_id_estado_torneo = models.ForeignKey(EstadosTorneo,models.DO_NOTHING,db_column='estados_torneo_id_estado_torneo'
)
    reglas_elegibilidad = models.CharField(max_length=1000, blank=True, null=True)
    aforo_equipos = models.BigIntegerField(null=True, blank=True)
    limite_inscripcion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'torneos'

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
    
    #  AGREGAR: Campo group_id para compatibilidad con appointments
    group = models.ForeignKey(
        Group, models.DO_NOTHING, db_column="group_id",
        null=True, blank=True, related_name="+", db_constraint=False
    )

    class Meta:
        managed = True
        db_table = "roles"
        app_label = 'management_cadi_tests'


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
        app_label = 'management_cadi_tests'

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
        app_label = 'management_cadi_tests'


class EstadosCita(models.Model):
    id_estado_cita = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=30)
    citas_id_cita = models.OneToOneField(
        Citas, models.DO_NOTHING, db_column="citas_id_cita", related_name="+"
    )
    
    class Meta:
        managed = True
        db_table = "estados_cita"
        app_label = 'management_cadi_tests'


class MotivosCita(models.Model):
    id_motivo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=80, unique=True)
    citas_id_cita = models.OneToOneField(
        Citas, models.DO_NOTHING, db_column="citas_id_cita", null=True, blank=True, related_name="+"
    )
    
    class Meta:
        managed = True
        db_table = "motivos_cita"
        app_label = 'management_cadi_tests'


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
        app_label = 'management_cadi_tests'
 
        
class Equipos(models.Model):
    id_equipo = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField()
    cantidad_personas = models.BigIntegerField(blank=True, null=True)
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    disciplinas_id_disciplina = models.ForeignKey(Disciplinas, models.DO_NOTHING, db_column='disciplinas_id_disciplina', blank=True, null=True)
    capacidad_min = models.IntegerField(blank=True, null=True)
    capacidad_max = models.IntegerField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'equipos'

class EquiposParticipantes(models.Model):
    id = models.BigAutoField(primary_key=True) 
    equipos_id_equipo = models.ForeignKey('Equipos', models.DO_NOTHING, db_column='equipos_id_equipo')
    participantes_id_participante = models.ForeignKey('Participantes', models.DO_NOTHING, db_column='participantes_id_participante')
    id_participante1 = models.BigIntegerField()  
    class Meta:
        managed = True
        db_table = 'equipos_participantes'

class Partidos(models.Model):

    id_partido = models.BigAutoField(primary_key=True)
    torneos_id_torneo = models.ForeignKey('Torneos', models.DO_NOTHING, db_column='torneos_id_torneo')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(blank=True, null=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)
    equipos_id_equipo = models.ForeignKey(Equipos, models.DO_NOTHING, db_column='equipos_id_equipo')
    equipos_id_equipo2 = models.ForeignKey(Equipos, models.DO_NOTHING, db_column='equipos_id_equipo2', related_name='partidos_equipos_id_equipo2_set')
    marcador_a = models.IntegerField(blank=True, null=True)
    marcador_b = models.IntegerField(blank=True, null=True)
    estado = models.CharField(max_length=20)
    class Meta:
        managed = True
        db_table = 'partidos'

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

class Noticias(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='id')
    titulo = models.CharField(max_length=200, db_column='titulo')
    enunciado = models.CharField(max_length=300, db_column='enunciado', default='No description available')
    autor = models.CharField(max_length=100, default='Administración Bienestar Universitario')
    descripcion = models.TextField(db_column='descripcion')
    imagen = ResizedImageField(
        size=[800, 450],           # Tamaño máximo [ancho, alto]
        crop=None,                 # None = No cortar, mantener proporción
        quality=85,                # Calidad JPEG (0-100)
        keep_meta=False,           # Eliminar metadatos EXIF
        force_format='JPEG',       # Convertir a JPEG
        upload_to='noticias/'
    )
    fecha_publicacion = models.DateField(auto_now_add=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    def save(self, *args, **kwargs):

        from django.conf import settings

    # Evitar procesamiento de imagen SOLO en tests
        if settings.TESTING:
            if self.imagen and not hasattr(self.imagen, 'file'):
                self.imagen = None

    # Slug autogenerado si no existe
        if not self.slug:
            self.slug = slugify(self.titulo)

        super().save(*args, **kwargs)


    def __str__(self):
        return self.titulo
    class Meta:
        managed = False
        db_table = "noticias"
        ordering = ['-fecha_publicacion']
        app_label = 'management_cadi_tests'