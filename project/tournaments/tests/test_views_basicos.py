import datetime as dt
import datetime as pydt
from django.test.utils import override_settings
from django.utils.timezone import make_aware, get_current_timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from tournaments.tests.models import Partidos as TPartidos
TZ = get_current_timezone()

##PORFAVOR CORRER LOS TEST CON python manage.py test tournaments --keepdb
##PORFAVOR CORRER LOS TEST CON python manage.py test tournaments --keepdb
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
    # login como admin antes del POST
        admin = User.objects.create_user("admin", password="x", is_staff=True, is_superuser=True)
        self.client.login(username="admin", password="x")

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


@override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
class TestMatches(TestCase):
    def setUp(self):
        self.client = Client()

        # Base mínima
        self.estado = TEstadosTorneo.objects.create(id_estado_torneo=1, nombre="Activo")
        self.disc = TDisciplinas.objects.create(nombre="Fútbol")
        self.rol = TRoles.objects.create(nombre_rol="Jugador")

        # Users
        self.admin = User.objects.create_user("admin", password="x", is_staff=True, is_superuser=True)
        self.alice = User.objects.create_user("alice", password="x")

        # Participantes
        self.p_admin = TParticipantes.objects.create(user=self.admin, roles_id_rol=self.rol, correo="admin@ex.com")
        self.p_alice = TParticipantes.objects.create(user=self.alice, roles_id_rol=self.rol, correo="alice@ex.com")

        # Torneo por equipos
        self.t_ini = make_aware(pydt.datetime(2025, 10, 1, 0, 0, 0), TZ)
        self.t_fin = make_aware(pydt.datetime(2025, 10, 31, 23, 59, 0), TZ)
        self.torneo = TTorneos.objects.create(
            nombre="Interfacultades",
            disciplinas_id_disciplina=self.disc,
            fecha_inicio=self.t_ini,
            fecha_fin=self.t_fin,
            estados_torneo_id_estado_torneo=self.estado,
            aforo_equipos=8,
        )

        # Equipos del torneo
        self.team_a = TEquipos.objects.create(
            nombre="Tigres",
            fecha_creacion=pydt.datetime(2025, 9, 20, 0, 0, 0),
            participantes_id_participante=self.p_admin,
            disciplinas_id_disciplina=self.disc,
            capacidad_min=5, capacidad_max=10,
        )
        self.team_b = TEquipos.objects.create(
            nombre="Leones",
            fecha_creacion=pydt.datetime(2025, 9, 20, 0, 0, 0),
            participantes_id_participante=self.p_admin,
            disciplinas_id_disciplina=self.disc,
            capacidad_min=5, capacidad_max=10,
        )
        TTorneosEquipos.objects.create(torneos_id_torneo=self.torneo, equipos_id_equipo=self.team_a)
        TTorneosEquipos.objects.create(torneos_id_torneo=self.torneo, equipos_id_equipo=self.team_b)

    def _dtloc(self, y, m, d, hh, mm):
        """ Formato de <input type='datetime-local'>: YYYY-MM-DDTHH:MM """
        return f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}"

    # --- crear partido ---
    def test_create_match_requires_admin(self):
        self.client.login(username="alice", password="x")
        url = reverse("tournaments:matches_create", args=[self.torneo.pk])
        r = self.client.post(url, {
            "equipo_a": str(self.team_a.pk),
            "equipo_b": str(self.team_b.pk),
            "inicio": self._dtloc(2025, 10, 10, 10, 0),
            "fin":    self._dtloc(2025, 10, 10, 11, 0),
            "lugar": "Cancha 1",
        })
        self.assertIn(r.status_code, (302, 303))
        self.assertFalse(TPartidos.objects.exists())

    def test_create_match_happy_path(self):
        self.client.login(username="admin", password="x")
        url = reverse("tournaments:matches_create", args=[self.torneo.pk])
        r = self.client.post(url, {
            "equipo_a": str(self.team_a.pk),
            "equipo_b": str(self.team_b.pk),
            "inicio": self._dtloc(2025, 10, 10, 10, 0),
            "fin":    self._dtloc(2025, 10, 10, 11, 0),
            "lugar": "Cancha 1",
        })
        self.assertIn(r.status_code, (302, 303))
        self.assertTrue(TPartidos.objects.filter(
            torneos_id_torneo=self.torneo,
            equipos_id_equipo=self.team_a,
            equipos_id_equipo2=self.team_b,
            estado="PROGRAMADO",
        ).exists())

    def test_create_match_same_team_invalid(self):
        self.client.login(username="admin", password="x")
        url = reverse("tournaments:matches_create", args=[self.torneo.pk])
        r = self.client.post(url, {
            "equipo_a": str(self.team_a.pk),
            "equipo_b": str(self.team_a.pk),
            "inicio": self._dtloc(2025, 10, 10, 10, 0),
            "fin":    self._dtloc(2025, 10, 10, 11, 0),
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(TPartidos.objects.exists())

    def test_create_match_team_not_in_tournament(self):
        self.client.login(username="admin", password="x")
        outsider = TEquipos.objects.create(
            nombre="Forasteros",
            fecha_creacion=pydt.datetime(2025, 9, 20),
            participantes_id_participante=self.p_admin,
            disciplinas_id_disciplina=self.disc,
        )
        url = reverse("tournaments:matches_create", args=[self.torneo.pk])
        r = self.client.post(url, {
            "equipo_a": str(self.team_a.pk),
            "equipo_b": str(outsider.pk),
            "inicio": self._dtloc(2025, 10, 12, 9, 0),
            "fin":    self._dtloc(2025, 10, 12, 10, 0),
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(TPartidos.objects.exists())

    def test_create_match_out_of_tournament_dates(self):
        self.client.login(username="admin", password="x")
        url = reverse("tournaments:matches_create", args=[self.torneo.pk])

        r1 = self.client.post(url, {
            "equipo_a": str(self.team_a.pk),
            "equipo_b": str(self.team_b.pk),
            "inicio": self._dtloc(2025, 9, 30, 23, 30),
            "fin":    self._dtloc(2025, 10, 1, 0, 30),
        })
        self.assertEqual(r1.status_code, 200)
        self.assertFalse(TPartidos.objects.exists())

        r2 = self.client.post(url, {
            "equipo_a": str(self.team_a.pk),
            "equipo_b": str(self.team_b.pk),
            "inicio": self._dtloc(2025, 10, 31, 23, 30),
            "fin":    self._dtloc(2025, 11, 1, 0, 30),
        })
        self.assertEqual(r2.status_code, 200)
        self.assertFalse(TPartidos.objects.exists())

    def test_create_match_overlap_blocked(self):
        self.client.login(username="admin", password="x")
        url = reverse("tournaments:matches_create", args=[self.torneo.pk])

        # válido 10:00–11:00
        self.client.post(url, {
            "equipo_a": str(self.team_a.pk),
            "equipo_b": str(self.team_b.pk),
            "inicio": self._dtloc(2025, 10, 15, 10, 0),
            "fin":    self._dtloc(2025, 10, 15, 11, 0),
        })
        self.assertEqual(TPartidos.objects.count(), 1)

        # solape 10:30–11:30
        r = self.client.post(url, {
            "equipo_a": str(self.team_a.pk),
            "equipo_b": str(self.team_b.pk),
            "inicio": self._dtloc(2025, 10, 15, 10, 30),
            "fin":    self._dtloc(2025, 10, 15, 11, 30),
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(TPartidos.objects.count(), 1)

    # --- registrar resultados ---
    def _crear_partido(self):
        return TPartidos.objects.create(
            torneos_id_torneo=self.torneo,
            equipos_id_equipo=self.team_a,
            equipos_id_equipo2=self.team_b,
            fecha_inicio=make_aware(pydt.datetime(2025, 10, 20, 9, 0, 0), TZ),
            fecha_fin=None,
            lugar="Cancha 2",
            estado="PROGRAMADO",
            marcador_a=None,
            marcador_b=None,
        )

    def test_record_result_requires_admin(self):
        partido = self._crear_partido()
        self.client.login(username="alice", password="x")
        url = reverse("tournaments:match_record", args=[partido.pk])
        r = self.client.post(url, {"estado": "FINALIZADO", "marcador_a": "1", "marcador_b": "0"})
        self.assertIn(r.status_code, (302, 303))
        partido.refresh_from_db()
        self.assertEqual(partido.estado, "PROGRAMADO")

    def test_record_result_finalize_ok(self):
        partido = self._crear_partido()
        self.client.login(username="admin", password="x")
        url = reverse("tournaments:match_record", args=[partido.pk])
        r = self.client.post(url, {"estado": "FINALIZADO", "marcador_a": "3", "marcador_b": "2"})
        self.assertIn(r.status_code, (302, 303))
        partido.refresh_from_db()
        self.assertEqual(partido.estado, "FINALIZADO")
        self.assertEqual(partido.marcador_a, 3)
        self.assertEqual(partido.marcador_b, 2)
        self.assertIsNotNone(partido.fecha_fin)

    def test_record_result_cancel_ok(self):
        partido = self._crear_partido()
        self.client.login(username="admin", password="x")
        url = reverse("tournaments:match_record", args=[partido.pk])
        r = self.client.post(url, {"estado": "CANCELADO", "marcador_a": "", "marcador_b": ""})
        self.assertIn(r.status_code, (302, 303))
        partido.refresh_from_db()
        self.assertEqual(partido.estado, "CANCELADO")
        self.assertIsNone(partido.marcador_a)
        self.assertIsNone(partido.marcador_b)

    def test_record_result_invalid_scores(self):
        partido = self._crear_partido()
        self.client.login(username="admin", password="x")
        url = reverse("tournaments:match_record", args=[partido.pk])
        r = self.client.post(url, {"estado": "FINALIZADO", "marcador_a": "-1", "marcador_b": "a"})
        self.assertEqual(r.status_code, 200)
        partido.refresh_from_db()
        self.assertEqual(partido.estado, "PROGRAMADO")
