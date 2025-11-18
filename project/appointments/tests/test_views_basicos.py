import datetime as pydt
import unittest
import copy
from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch
from django.utils.timezone import make_aware, get_current_timezone
from django.contrib.auth.models import User
from django.db import connection
from django.conf import settings
from django.test.utils import override_settings
from appointments.tests.models import (
    Roles as TRoles,
    Participantes as TParticipantes,
    AgendaPsicologos as TAgenda,
    Citas as TCitas,
    EstadosCita as TEstado,
    HorariosParticipante as THorario,
    HistorialCitas as THistorial,
)

def _ensure_roles_table():
    with connection.cursor() as cur:
        cur.execute("SELECT to_regclass('public.roles');")
        exists = cur.fetchone()[0]
    if not exists:
        from django.db import connection as conn
        with conn.schema_editor() as schema:
            schema.create_model(TRoles)

class BaseAppointmentsCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _ensure_roles_table()

TZ = get_current_timezone()

def _dtloc(y, m, d, hh, mm):
    return f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}"

def _has_url(name, *args):
    try:
        reverse(name, args=args)
        return True
    except NoReverseMatch:
        return False


_TPL = copy.deepcopy(settings.TEMPLATES)
_cps = _TPL[0]["OPTIONS"]["context_processors"]
_TPL[0]["OPTIONS"]["context_processors"] = [
    c for c in _cps
    if c != "universitaryWellbeing.context_processors.notificaciones_context"
]


@override_settings(TEMPLATES=_TPL)
class TestAppointmentsFlow(BaseAppointmentsCase):
    def setUp(self):
        self.client = Client()

        # Roles
        self.r_student = TRoles.objects.create(nombre_rol="Estudiante")
        self.r_psy     = TRoles.objects.create(nombre_rol="Psicólogo")

        # Users
        self.u_student = User.objects.create_user("stu", password="x")
        self.u_psy     = User.objects.create_user("psy", password="x", is_staff=True)

        # Participantes
        self.p_student = TParticipantes.objects.create(
            user=self.u_student, roles_id_rol=self.r_student, correo="stu@ex.com", nombre="Ana"
        )
        self.p_psy = TParticipantes.objects.create(
            user=self.u_psy, roles_id_rol=self.r_psy, correo="psy@ex.com", nombre="Dra.", apellido="Rojas"
        )

        self.client.login(username="stu", password="x")

    def test_create_with_slot_reserves_and_creates_calendar(self):
        ini = make_aware(pydt.datetime(2025, 11, 20, 9, 0), TZ)
        fin = make_aware(pydt.datetime(2025, 11, 20, 9, 45), TZ)
        slot = TAgenda.objects.create(
            participantes_id_participante=self.p_psy,
            fecha_inicio=ini, fecha_fin=fin, estado_slot="DISPONIBLE", lugar="Bienestar (2.º piso)"
        )

        url = reverse("appointments:create")
        r = self.client.post(url, {
            "profesional_id": str(self.p_psy.pk),
            "fecha": _dtloc(2025, 11, 20, 9, 10),
            "motivo": "estrés",
            "observaciones": "",
        })
        
        # Debug: ver qué error devuelve si falla
        if r.status_code == 200:
            print("\n=== DEBUG: Vista devolvió 200 en lugar de redirect ===")
            print(f"Contenido: {r.content.decode()[:500]}")
            from django.contrib import messages as msgs
            for msg in msgs.get_messages(r.wsgi_request):
                print(f"Mensaje: {msg}")
        
        self.assertIn(r.status_code, (302, 303), 
                     f"Se esperaba redirect pero se obtuvo {r.status_code}")

        cita = TCitas.objects.latest("id_cita")
        self.assertEqual(cita.agenda_psicologos_id_agenda_slot_id, slot.pk)

        self.assertTrue(TEstado.objects.filter(citas_id_cita=cita, nombre__icontains="Programada").exists())

        slot.refresh_from_db()
        self.assertEqual(slot.estado_slot, "RESERVADO")

        self.assertEqual(THorario.objects.filter(citas_id_cita=cita).count(), 2)

    def test_create_without_slot_defaults_45min(self):
        start = _dtloc(2025, 11, 22, 14, 0)
        url = reverse("appointments:create")
        r = self.client.post(url, {
            "profesional_id": str(self.p_psy.pk),
            "fecha": start,
            "motivo": "",
            "observaciones": "",
        })
        
        # Debug: ver qué error devuelve si falla
        if r.status_code == 200:
            print("\n=== DEBUG: Vista devolvió 200 en lugar de redirect ===")
            print(f"Contenido: {r.content.decode()[:500]}")
            from django.contrib import messages as msgs
            for msg in msgs.get_messages(r.wsgi_request):
                print(f"Mensaje: {msg}")
        
        self.assertIn(r.status_code, (302, 303),
                     f"Se esperaba redirect pero se obtuvo {r.status_code}")

        cita = TCitas.objects.latest("id_cita")
        h = THorario.objects.filter(citas_id_cita=cita, participantes_id_participante=self.p_student).first()
        self.assertIsNotNone(h)
        self.assertEqual(int((h.fecha_fin - h.fecha_inicio).total_seconds()), 45 * 60)

    def test_overlap_blocks_student(self):
        """Test de detección de solapamiento de horarios"""
        base_ini = make_aware(pydt.datetime(2025, 11, 25, 10, 0), TZ)
        
        # ✅ Crear horario existente SIN actividad (campo nullable)
        THorario.objects.create(
            participantes_id_participante=self.p_student,
            actividades_id_actividad=None,  # ✅ NULL permitido
            titulo="Bloqueo temporal",  # ✅ OBLIGATORIO (NOT NULL en DB)
            fecha_inicio=base_ini,
            fecha_fin=base_ini.replace(minute=45),
            fuente_manual="N",
        )

        # Intentar crear cita que solapa con el horario existente
        url = reverse("appointments:create")
        r = self.client.post(url, {
            "profesional_id": str(self.p_psy.pk),
            "fecha": _dtloc(2025, 11, 25, 10, 15),  # Solapa con 10:00-10:45
            "motivo": "",
            "observaciones": "",
        })
        
        # La vista debe rechazar (status 200 con error, no redirect)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(TCitas.objects.count(), 0)


@override_settings(TEMPLATES=_TPL)
@unittest.skipUnless(_has_url("appointments:cancel", 1), "URL appointments:cancel no disponible aún")
class TestCancelAppointment(BaseAppointmentsCase):   
    def setUp(self):
        self.client = Client()
        self.r_student = TRoles.objects.create(nombre_rol="Estudiante")
        self.r_psy     = TRoles.objects.create(nombre_rol="Psicólogo")
        self.u_student = User.objects.create_user("stu", password="x")
        self.u_psy     = User.objects.create_user("psy", password="x", is_staff=True)
        self.p_student = TParticipantes.objects.create(user=self.u_student, roles_id_rol=self.r_student, correo="s@ex.com")
        self.p_psy     = TParticipantes.objects.create(user=self.u_psy, roles_id_rol=self.r_psy, correo="p@ex.com")
        self.client.login(username="stu", password="x")

        ini = make_aware(pydt.datetime(2025, 12, 1, 9, 0), TZ)
        fin = make_aware(pydt.datetime(2025, 12, 1, 9, 45), TZ)
        self.slot = TAgenda.objects.create(
            participantes_id_participante=self.p_psy,
            fecha_inicio=ini, fecha_fin=fin, estado_slot="RESERVADO", lugar="Bienestar (2.º piso)"
        )
        self.cita = TCitas.objects.create(
            fecha=ini, participantes_id_participante=self.p_student,
            participantes_id_participante2=self.p_psy,
            agenda_psicologos_id_agenda_slot=self.slot
        )
        TEstado.objects.create(nombre="Programada", citas_id_cita=self.cita)