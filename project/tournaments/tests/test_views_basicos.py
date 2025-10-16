import datetime as dt
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

# Importa SOLO los modelos de prueba
from tournaments.tests.models import (
    Disciplinas as TDisciplinas,
    EstadosTorneo as TEstadosTorneo,
    Participantes as TParticipantes,
    Roles as TRoles,
    Torneos as TTorneos,
    Equipos as TEquipos,
    TorneosEquipos as TTorneosEquipos,
    EquiposParticipantes as TEquiposParticipantes,
)

class TestViewsBasicos(TestCase):
    def setUp(self):
        self.client = Client()
        # Base mínima para FKs
        self.estado = TEstadosTorneo.objects.create(id_estado_torneo=1, nombre="Activo")
        self.disc = TDisciplinas.objects.create(nombre="Fútbol")
        self.rol = TRoles.objects.create(nombre_rol="Jugador")

    # --- 1) CREAR TORNEO ---
    def test_crear_torneo(self):
        url = reverse("tournaments:create")
        resp = self.client.post(url, {
            "nombre": "Interfacultades",
            "disciplina": str(self.disc.pk),
            "fecha_inicio": "2025-10-01",
            "fecha_fin": "2025-10-15",
            "aforo": "16",
            "limite_inscripcion": "",
        })
        self.assertIn(resp.status_code, (302, 303))
        self.assertTrue(TTorneos.objects.filter(nombre="Interfacultades").exists())

    # --- 2) CREAR EQUIPO EN TORNEO ---
    def test_crear_equipo_en_torneo(self):
        torneo = TTorneos.objects.create(
            nombre="Copa Uni",
            disciplinas_id_disciplina=self.disc,
            fecha_inicio=dt.datetime(2025, 10, 1, 0, 0, 0),
            fecha_fin=dt.datetime(2025, 10, 15, 0, 0, 0),
            estados_torneo_id_estado_torneo=self.estado,
            aforo_equipos=8,
        )
        # Responsable
        u = User.objects.create_user("leader", password="x")
        responsable = TParticipantes.objects.create(
            user=u, roles_id_rol=self.rol, correo="leader@ex.com",
            nombre="Ana", apellido="Líder", genero="Femenino",
        )

        url = reverse("tournaments:create_team", args=[torneo.pk])
        resp = self.client.post(url, {
            "nombre_equipo": "Tigres",
            "responsable_id": str(responsable.pk),
            "disciplina_id": str(self.disc.pk),
            "capacidad_min": "5",
            "capacidad_max": "8",
            "fecha_creacion": "2025-10-02",
        })
        self.assertIn(resp.status_code, (302, 303))

        # Asserts sobre las tablas de prueba (mismo db_table que las reales)
        equipo = TEquipos.objects.get(nombre="Tigres")
        self.assertTrue(TTorneosEquipos.objects.filter(
            torneos_id_torneo=torneo, equipos_id_equipo=equipo
        ).exists())
        self.assertTrue(TEquiposParticipantes.objects.filter(
            equipos_id_equipo=equipo, participantes_id_participante=responsable
        ).exists())

    # --- 3) UNIRSE A UN EQUIPO ---
    def test_unirse_a_equipo(self):
        # Usuario que se unirá
        u_join = User.objects.create_user("luis", password="x")
        participante = TParticipantes.objects.create(
            user=u_join, roles_id_rol=self.rol, correo="luis@ex.com",
            nombre="Luis", apellido="Test", genero="Masculino",
        )
        self.client.login(username="luis", password="x")

        torneo = TTorneos.objects.create(
            nombre="Copa",
            disciplinas_id_disciplina=self.disc,
            fecha_inicio=dt.datetime(2025, 10, 1),
            fecha_fin=dt.datetime(2025, 10, 15),
            estados_torneo_id_estado_torneo=self.estado,
            aforo_equipos=8,
        )
        # Equipo existente del torneo (con líder cualquiera)
        u_leader = User.objects.create_user("leader2", password="x")
        responsable = TParticipantes.objects.create(
            user=u_leader, roles_id_rol=self.rol, correo="leader2@ex.com",
            nombre="Ana", apellido="Líder", genero="Femenino",
        )
        equipo = TEquipos.objects.create(
            nombre="Leones",
            fecha_creacion=dt.datetime(2025, 10, 1),
            participantes_id_participante=responsable,
            disciplinas_id_disciplina=self.disc,
            capacidad_min=5,
            capacidad_max=10,
        )
        TTorneosEquipos.objects.create(torneos_id_torneo=torneo, equipos_id_equipo=equipo)

        url = reverse("tournaments:join_team", args=[torneo.pk])
        resp = self.client.post(url, {"team_id": str(equipo.pk)})
        self.assertIn(resp.status_code, (302, 303))
        self.assertTrue(TEquiposParticipantes.objects.filter(
            equipos_id_equipo=equipo, participantes_id_participante=participante
        ).exists())
