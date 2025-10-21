import datetime as dt
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.timezone import make_aware, get_current_timezone
from django.test.utils import override_settings
from unittest.mock import patch


##PORFAVOR CORRER LOS TEST CON python manage.py test social_projects --keepdb
from social_projects.tests.models import (
    Roles as TRoles,
    Participantes as TParticipantes,
    ProyectosSociales as TProyectos,
    EstadosParticipacion as TEstadosPart,
    InscripcionesPsu as TInscripciones,
)


TZ = get_current_timezone()

class TestViewsPSU(TestCase):
    def setUp(self):
        self.client = Client()

        # Base mínima
        self.rol = TRoles.objects.create(nombre_rol="Estudiante")

        # Usuarios
        self.user_admin = User.objects.create_user("admin", password="x", is_staff=True, is_superuser=True)
        self.user_std = User.objects.create_user("alice", password="x")

        # Participantes
        self.part_admin = TParticipantes.objects.create(
            user=self.user_admin, roles_id_rol=self.rol, correo="admin@ex.com",
            nombre="Admin", apellido="One",
        )
        self.part_std = TParticipantes.objects.create(
            user=self.user_std, roles_id_rol=self.rol, correo="alice@ex.com",
            nombre="Alice", apellido="Test",
        )

        # Estado “pendiente”
        self.estado_pend = TEstadosPart.objects.create(nombre="pendiente")

        # Proyecto base
        self.p_ini = make_aware(dt.datetime(2025, 10, 4, 0, 0, 0), TZ)
        self.p_fin = make_aware(dt.datetime(2025, 11, 30, 0, 0, 0), TZ)
        self.proy = TProyectos.objects.create(
            nombre="Paseo por Cali",
            descripcion="Tour",
            coordinador_id=self.part_admin.id_participante,
            fecha_inicio=self.p_ini,
            fecha_fin=self.p_fin,
            aforo=2,
        )

    # --- lista_proyectos ---
    # Debe listar proyectos visibles para un estudiante autenticado.
    def test_lista_proyectos_ok(self):
        self.client.login(username="alice", password="x")
        url = reverse("social_projects:lista_proyectos")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Paseo por Cali")

    # Debe filtrar por texto (q) en el listado de proyectos.
    def test_lista_proyectos_search(self):
        self.client.login(username="alice", password="x")
        url = reverse("social_projects:lista_proyectos")
        r = self.client.get(url, {"q": "Cali"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Paseo por Cali")

    # --- crear_proyecto_social (solo admin) ---
    # Un usuario no admin no puede crear proyectos; debe redirigir y no persistir.
    def test_crear_proyecto_requires_admin(self):
        self.client.login(username="alice", password="x")
        url = reverse("social_projects:crear_proyecto")
        r = self.client.post(url, {
            "nombre": "Nuevo",
            "descripcion": "desc",
            "aforo": "10",
            "fecha_inicio": "2025-10-10",
            "fecha_fin": "2025-10-20",
        })
        # debería redirigir con error por permisos
        self.assertIn(r.status_code, (302, 303))
        self.assertFalse(TProyectos.objects.filter(nombre="Nuevo").exists())
    # Un admin sí puede crear proyectos; debe redirigir tras crear.
    def test_crear_proyecto_admin_ok(self):
        self.client.login(username="admin", password="x")
        url = reverse("social_projects:crear_proyecto")
        r = self.client.post(url, {
            "nombre": "Nuevo Proy",
            "descripcion": "desc",
            "aforo": "50",
            "fecha_inicio": "2025-10-10",
            "fecha_fin": "2025-10-20",
        })
        self.assertIn(r.status_code, (302, 303))
        self.assertTrue(TProyectos.objects.filter(nombre="Nuevo Proy").exists())

     # --- detalle_proyecto ---
    # Debe renderizar el detalle del proyecto para un estudiante autenticado.
    def test_detalle_proyecto_ok(self):
        self.client.login(username="alice", password="x")
        url = reverse("social_projects:detalle_proyecto", args=[self.proy.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Paseo por Cali")

    # --- inscribirse_psu ---
    # Debe permitir que un estudiante se inscriba si hay cupo disponible.
    def test_inscribirse_psu_ok(self):
        self.client.login(username="alice", password="x")
        url = reverse("social_projects:inscribirse_psu", args=[self.proy.pk])
        r = self.client.post(url)
        self.assertIn(r.status_code, (302, 303))
        self.assertTrue(TInscripciones.objects.filter(
            participantes_id_participante=self.part_std,
            proyectos_sociales_id_proyecto=self.proy
        ).exists())

     # No debe permitir inscripciones duplicadas del mismo participante en el mismo proyecto.
    def test_inscribirse_psu_no_duplicate(self):
        # primera
        self.client.login(username="alice", password="x")
        url = reverse("social_projects:inscribirse_psu", args=[self.proy.pk])
        self.client.post(url)
        # segunda (debe informar / no duplicar)
        r = self.client.post(url)
        self.assertIn(r.status_code, (302, 303))
        self.assertEqual(TInscripciones.objects.filter(
            participantes_id_participante=self.part_std,
            proyectos_sociales_id_proyecto=self.proy
        ).count(), 1)

    # Cuando el aforo está lleno (2), una tercera inscripción no debe crear registro.
    def test_inscribirse_psu_aforo_lleno(self):
        # Llenar aforo con 2 inscripciones previas
        u2 = User.objects.create_user("bob", password="x")
        p2 = TParticipantes.objects.create(user=u2, roles_id_rol=self.rol, correo="bob@ex.com")
        u3 = User.objects.create_user("carol", password="x")
        p3 = TParticipantes.objects.create(user=u3, roles_id_rol=self.rol, correo="carol@ex.com")
        # inscribir 2
        for p in (p2, p3):
            TInscripciones.objects.create(
                participantes_id_participante=p,
                proyectos_sociales_id_proyecto=self.proy,
                fecha_inscripcion=make_aware(dt.datetime(2025,10,5,12,0,0), TZ),
                estados_participacion_id_estado_participacion=self.estado_pend,
            )

        # intentar tercera (alice)
        self.client.login(username="alice", password="x")
        url = reverse("social_projects:inscribirse_psu", args=[self.proy.pk])
        r = self.client.post(url)
        self.assertIn(r.status_code, (302, 303))
        # sigue habiendo solo 2 registros
        self.assertEqual(TInscripciones.objects.filter(
            proyectos_sociales_id_proyecto=self.proy
        ).count(), 2)


    # Enviar duda por POST debe disparar un intento de envío de correo y redirigir al detalle.
    @patch("social_projects.views.send_mail")  # mockeamos envío real de correo
    def test_consultar_duda_post_ok(self, mock_send_mail):
        """Debe permitir enviar una duda válida al coordinador"""
        self.client.login(username="alice", password="x")
        url = reverse("social_projects:consultar_duda", args=[self.proy.pk])
        r = self.client.post(url, {"mensaje": "¿Cuándo inicia el proyecto?"})
        
        # Se espera redirección al detalle
        self.assertIn(r.status_code, (302, 303))
        # Debe haberse intentado enviar un correo
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        self.assertIn("¿Cuándo inicia el proyecto?", kwargs["message"])

    # GET de la vista de consulta renderiza la página.
    def test_consultar_duda_get_ok(self):
        """Debe renderizar la página de consulta"""
        self.client.login(username="alice", password="x")
        url = reverse("social_projects:consultar_duda", args=[self.proy.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Paseo por Cali")

    #POST con mensaje vacío debe manejar el error sin romper (quedarse o redirigir).
    def test_consultar_duda_post_empty_message(self):
        """Debe mostrar error si el mensaje está vacío"""
        self.client.login(username="alice", password="x")
        url = reverse("social_projects:consultar_duda", args=[self.proy.pk])
        r = self.client.post(url, {"mensaje": "   "})
        self.assertIn(r.status_code, (200, 302, 303))  # puede quedarse o redirigir
        # No se crea excepción ni se envía correo

    # Si el proyecto no tiene coordinador, el flujo debe manejarse (redirigir/avisar).
    def test_consultar_duda_sin_coordinador(self):
        """Debe manejar el caso de proyecto sin coordinador"""
        # Quitamos coordinador
        self.proy.coordinador_id = None
        self.proy.save()
        self.client.login(username="alice", password="x")
        url = reverse("social_projects:consultar_duda", args=[self.proy.pk])
        r = self.client.post(url, {"mensaje": "¿Hay cupos?"})
        self.assertIn(r.status_code, (302, 303))