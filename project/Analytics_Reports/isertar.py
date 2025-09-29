from universitaryWellbeing.models import (
    Roles, TiposActividad, EstadosParticipacion, RolesParticipacion, EstadosAsistencia,
    Participantes, Actividades, Participaciones
)
from datetime import date

def insertar_datos_iniciales():
    # 1️⃣ Roles
    for nombre in ['Estudiante', 'Coordinador']:
        Roles.objects.get_or_create(nombre_rol=nombre)

    # 2️⃣ Tipos de Actividad
    for nombre in ['Taller', 'Conferencia']:
        TiposActividad.objects.get_or_create(nombre_tipo=nombre)

    # 3️⃣ Estados de Participación
    for nombre in ['Activo', 'Inactivo']:
        EstadosParticipacion.objects.get_or_create(nombre=nombre)

    # 4️⃣ Roles de Participación
    for nombre in ['Participante', 'Organizador']:
        RolesParticipacion.objects.get_or_create(nombre=nombre)

    # 5️⃣ Estados de Asistencia
    for nombre in ['Presente', 'Ausente', 'Tardío']:
        EstadosAsistencia.objects.get_or_create(nombre=nombre)

    # 6️⃣ Participantes
    rol_estudiante = Roles.objects.get(nombre_rol='Estudiante')

    participantes_data = [
        {'nombre': 'Juan', 'apellido': 'Pérez', 'correo': 'juan.perez@academia.com',
         'semestre': 5, 'estado_activo': 'S', 'roles_id_rol': rol_estudiante,
         'facultad': 'Ingeniería', 'programa': 'Ingeniería de Sistemas', 'genero': 'Masculino'},
        {'nombre': 'María', 'apellido': 'Gómez', 'correo': 'maria.gomez@academia.com',
         'semestre': 3, 'estado_activo': 'S', 'roles_id_rol': rol_estudiante,
         'facultad': 'Ciencias', 'programa': 'Biología', 'genero': 'Femenino'},
    ]

    for p in participantes_data:
        Participantes.objects.get_or_create(correo=p['correo'], defaults=p)

    # 7️⃣ Actividades
    tipo_taller = TiposActividad.objects.get(nombre_tipo='Taller')

    actividades_data = [
        {'nombre': 'Taller de Programación', 'descripcion': 'Taller práctico de Python',
         'lugar': 'Aula 101', 'fecha_inicio': date(2025, 10, 1), 'fecha_fin': date(2025, 10, 2),
         'requiere_inscripcion': 'S', 'modalidad': 'P', 'aforo': 30,
         'fecha_apertura_ins': date(2025, 9, 20), 'fecha_cierre_ins': date(2025, 9, 30),
         'tipos_actividad_id_tipo': tipo_taller},
        {'nombre': 'Conferencia de Bienestar', 'descripcion': 'Charla sobre salud mental',
         'lugar': 'Auditorio Principal', 'fecha_inicio': date(2025, 10, 5), 'fecha_fin': date(2025, 10, 5),
         'requiere_inscripcion': 'N', 'modalidad': 'P', 'aforo': 100, 'tipos_actividad_id_tipo': None},
    ]

    for a in actividades_data:
        Actividades.objects.get_or_create(nombre=a['nombre'], defaults=a)

    # 8️⃣ Participaciones
    participante1 = Participantes.objects.get(correo='juan.perez@academia.com')
    participante2 = Participantes.objects.get(correo='maria.gomez@academia.com')
    actividad1 = Actividades.objects.get(nombre='Taller de Programación')
    actividad2 = Actividades.objects.get(nombre='Conferencia de Bienestar')
    rol_participante = RolesParticipacion.objects.get(nombre='Participante')
    estado_activo = EstadosParticipacion.objects.get(nombre='Activo')

    for p in [
        (participante1, actividad1, date(2025, 9, 25)),
        (participante2, actividad1, date(2025, 9, 25)),
        (participante1, actividad2, date(2025, 10, 1))
    ]:
        Participaciones.objects.get_or_create(
            participantes_id_participante=p[0],
            actividades_id_actividad=p[1],
            defaults={
                'fecha_inscripcion': p[2],
                'roles_participacion_id_rol_participacion': rol_participante,
                'estados_participacion_id_estado_participacion': estado_activo
            }
        )

    print("✅ Datos iniciales insertados correctamente.")
