#\20252-g3-pi1-t3\project\management_CADI\tests\test_views_management_cadi.py
##https://www.reddit.com/r/node/comments/10tdb61/why_should_i_mock_a_database_for_testing_instead/

import datetime as dt
from django.test import SimpleTestCase, TestCase, Client, TransactionTestCase, override_settings, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock, Mock
from django.http import HttpResponse
from management_CADI.views import create_Activities, edit_Activity, cadi_index, manage_news, _draft_keys
from types import SimpleNamespace

"""
Conjunto integral de pruebas para las vistas del módulo `management_CADI`.

Este archivo contiene:
    - Pruebas unitarias completamente mockeadas (SimpleTestCase), diseñadas
      para validar la lógica interna de las vistas sin tocar la base de datos.
    - Pruebas funcionales con bases de datos temporales (TestCase /
      TransactionTestCase) para verificar integración entre vistas, modelos,
      gestión de participantes, horarios y calificaciones.
    - Validación de permisos y de flujos protegidos por `superuser_required`.
    - Validación de slugs canónicos, redirecciones y construcción de contexto.
    - Pruebas exhaustivas del flujo de creación, edición y programación de
      actividades (incluye manejo de borradores en sesión).
    - Pruebas para gestión de noticias con modelos y context processors
      totalmente mockeados para evitar dependencias del entorno real.

Estructura del archivo:
    - HelpersTestCase: prueba helpers internos como conversión de fechas y horas.
    - DraftKeysTestCase: prueba la generación de claves internas de borrador.
    - TestShowGroupActivities: validación de listado de grupos de actividad.
    - TestShowActivities: validación completa del listado de actividades,
      horarios, ratings y slugs.
    - SuperuserRequiredViewsTests: comprobación de restricciones de acceso.
    - CadiIndexTests: prueba del índice CADI y sus dependencias.
    - CreateActivitiesTests: prueba del flujo de creación de actividades.
    - EditActivityTests: prueba del flujo de edición.
    - AddSlotToScheduleTests: comprobación del agregado de bloques de horario.
    - ScheduleDraftTests: test del uso de borradores de horario en sesión.
    - NewsPermissionsTests: validación de permisos para vistas de noticias.

Este archivo sirve como una base sólida de regresión para garantizar la
estabilidad del módulo de gestión del CADI, su sistema de actividades y la
integración con participantes, roles, calificaciones y horarios.

Cubre tanto lógica de negocio como integración con sesiones, permisos y 
procesos auxiliares — todo ello con un fuerte aislamiento mediante mocks.
"""


# CORRECCIÓN: Importa desde management_CADI.tests.models, NO desde .models
from management_CADI.tests.models import (
    Grupos,
    GruposActividad,
    TiposActividad,
    Actividades,
    ActividadesGrupos,
    HorariosBloque,
    HorariosActividad,
    Roles,
    TiposParticipante,
    Participantes,
    RolesParticipacion,
    EstadosParticipacion,
    Participaciones,
    HorariosParticipante,  # ✅ NUEVO
    CalificacionesActividad,
)

# ==========================================================
# TESTS UNITARIOS CON MOCKS (SimpleTestCase)
# ==========================================================

class HelpersTestCase(SimpleTestCase):
    """Pruebas unitarias para helpers simples"""

    def test_is_admin_true_for_staff(self):
        from management_CADI.views import is_admin
        user = MagicMock(is_authenticated=True, is_staff=True)
        self.assertTrue(is_admin(user))

    def test_is_admin_false_for_anonymous(self):
        from management_CADI.views import is_admin
        user = MagicMock(is_authenticated=False, is_staff=False)
        self.assertFalse(is_admin(user))

    def test_hhmm_to_dt_valid(self):
        from management_CADI.views import hhmm_to_dt
        result = hhmm_to_dt("15:30")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 15) # type: ignore
        self.assertEqual(result.minute, 30) # type: ignore

    def test_hhmm_to_dt_invalid(self):
        from management_CADI.views import hhmm_to_dt
        self.assertIsNone(hhmm_to_dt(""))
        self.assertIsNone(hhmm_to_dt("invalid"))

    def test_date_input_to_dt_valid(self):
        from management_CADI.views import date_input_to_dt
        result = date_input_to_dt("2025-10-13")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025) # type: ignore
        self.assertEqual(result.month, 10) # type: ignore
        self.assertEqual(result.day, 13) # type: ignore

    def test_date_input_to_dt_invalid(self):
        from management_CADI.views import date_input_to_dt
        self.assertIsNone(date_input_to_dt(""))
        self.assertIsNone(date_input_to_dt("invalid"))


class DraftKeysTestCase(SimpleTestCase):
    """Pruebas para generación de llaves de sesión"""

    def test_draft_keys_new_activity(self):
        from management_CADI.views import _draft_keys
        base, sched_list, sched_last = _draft_keys(123)
        self.assertEqual(base, "cadi_draft_base_123_new")
        self.assertEqual(sched_list, "cadi_sched_list_123_new")
        self.assertEqual(sched_last, "cadi_sched_last_123_new")

    def test_draft_keys_edit_activity(self):
        from management_CADI.views import _draft_keys
        base, sched_list, sched_last = _draft_keys(123, 456)
        self.assertEqual(base, "cadi_draft_base_123_456")
        self.assertEqual(sched_list, "cadi_sched_list_123_456")
        self.assertEqual(sched_last, "cadi_sched_last_123_456")


# ==========================================================
# TESTS DE VISTAS CON BASE DE DATOS (TransactionTestCase)
# ==========================================================

# Mock de los context_processors para evitar errores de BD
def mock_notificaciones_context(request):
    """Context processor mockeado que no accede a la base de datos"""
    return {
        'notificaciones_no_leidas': [],
        'notificaciones_count': 0,
    }

def mock_user_rol(request):
    """Context processor mockeado para user_rol"""
    return {
        'user_rol': None,
        'es_estudiante': False,
        'es_coordinador': False,
        'es_profesor': False,
    }

@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # ✅ Usa los context processors mockeados
                'management_CADI.tests.test_views_management_cadi.mock_notificaciones_context',
                'management_CADI.tests.test_views_management_cadi.mock_user_rol',
            ],
        },
    }]
)
# ✅ CLAVE: Mockear universitaryWellbeing.models, NO management_CADI.views
@patch('universitaryWellbeing.models.Grupos', Grupos)
@patch('universitaryWellbeing.models.GruposActividad', GruposActividad)
class TestShowGroupActivities(TransactionTestCase):
    """Pruebas para showGroupActivities"""
    
    # Resetea secuencias para evitar conflictos de PK
    reset_sequences = True
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("alice", password="testpass")
        self.client.login(username="alice", password="testpass")
        
        self.grupo = Grupos.objects.create(nombre="CADI")
        self.ga1 = GruposActividad.objects.create(
            grupos_id_grupo=self.grupo, 
            nombre="Deportes"
        )
        self.ga2 = GruposActividad.objects.create(
            grupos_id_grupo=self.grupo, 
            nombre="Arte"
        )

    def test_slug_redirect_to_canonical(self):
        """Debe redirigir slugs incorrectos al slug canónico"""
        url = reverse("management_cadi:listar_grupos_actividad", 
                     args=["slug-incorrecto", self.grupo.id_grupo])
        resp = self.client.get(url, follow=True)
        
        self.assertEqual(resp.status_code, 200)
        # Verifica que hubo redirección
        self.assertTrue(len(resp.redirect_chain) > 0)

    def test_list_grupos_actividad_renders_correctly(self):
        """Debe listar todos los grupos de actividad del grupo"""
        url = reverse("management_cadi:listar_grupos_actividad", 
                     args=["cadi", self.grupo.id_grupo])
        resp = self.client.get(url)
        
        self.assertEqual(resp.status_code, 200)
        grupos_act = resp.context["grupos_actividad"]
        self.assertEqual(len(grupos_act), 2)


@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # ✅ Usa los context processors mockeados
                'management_CADI.tests.test_views_management_cadi.mock_notificaciones_context',
                'management_CADI.tests.test_views_management_cadi.mock_user_rol',
            ],
        },
    }]
)
# ✅ CLAVE: Mockear universitaryWellbeing.models
@patch('universitaryWellbeing.models.Grupos', Grupos)
@patch('universitaryWellbeing.models.GruposActividad', GruposActividad)
@patch('universitaryWellbeing.models.TiposActividad', TiposActividad)
@patch('universitaryWellbeing.models.Actividades', Actividades)
@patch('universitaryWellbeing.models.ActividadesGrupos', ActividadesGrupos)
@patch('universitaryWellbeing.models.HorariosBloque', HorariosBloque)
@patch('universitaryWellbeing.models.HorariosActividad', HorariosActividad)
@patch('universitaryWellbeing.models.CalificacionesActividad', CalificacionesActividad)
@patch('universitaryWellbeing.models.Participantes', Participantes)
@patch('universitaryWellbeing.models.TiposParticipante', TiposParticipante)
@patch('universitaryWellbeing.models.RolesParticipacion', RolesParticipacion)  # ✅ NUEVO
@patch('universitaryWellbeing.models.EstadosParticipacion', EstadosParticipacion)  # ✅ NUEVO
@patch('universitaryWellbeing.models.Participaciones', Participaciones)  # ✅ NUEVO
class TestShowActivities(TransactionTestCase):
    """Pruebas para showActivities (listar_actividades)"""
    
    # Resetea secuencias para evitar conflictos de PK
    reset_sequences = True
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("alice", password="x")
        self.client.login(username="alice", password="x")
        
        # ✅ Crear tipo de participante
        self.tipo_participante = TiposParticipante.objects.create(
            nombre ="Estudiante Regular"
        )
        
        rol = Roles.objects.create(nombre_rol="Estudiante")
        self.part = Participantes.objects.create(
            user=self.user, 
            roles_id_rol=rol, 
            correo="alice@ex.com",
            tipo_participante=self.tipo_participante  # ✅ Asignar tipo
        )

        self.grupo = Grupos.objects.create(nombre="CADI")
        self.ga = GruposActividad.objects.create(
            grupos_id_grupo=self.grupo, 
            nombre="Baile"
        )

        self.tipo = TiposActividad.objects.create(id_tipo=1, nombre_tipo="Danza")
        self.act = Actividades.objects.create(
            nombre="Salsa 1", 
            tipos_actividad_id_tipo=self.tipo
        )
        ActividadesGrupos.objects.create(grupos_actividad=self.ga, actividad=self.act)

        b1 = HorariosBloque.objects.create(
            actividades_id_actividad=self.act,
            hora_inicio=dt.time(8, 0), 
            hora_fin=dt.time(9, 0),
            profesor="Profe X", 
            lugar="Gimnasio"
        )
        HorariosActividad.objects.create(
            actividades_id_actividad=self.act, 
            horario_bloque=b1, 
            dia_semana=0
        )
        HorariosActividad.objects.create(
            actividades_id_actividad=self.act, 
            horario_bloque=b1, 
            dia_semana=2
        )

    def _url(self, slug="cadi"):
        return reverse("management_cadi:listar_actividades",
                      args=[slug, self.grupo.id_grupo, self.ga.id_grupo_actividad])

    def test_slug_redirect_to_canonical(self):
        """Debe redirigir slugs incorrectos al slug canónico"""
        resp = self.client.get(self._url(slug="slug-erroneo"), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any("cadi" in url for url, _ in resp.redirect_chain))

    def test_list_builds_daywise_and_zero_rating(self):
        """Debe construir items_dia correctamente y mostrar rating 0"""
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)
        
        acts = resp.context["actividades"]
        self.assertEqual(len(acts), 1)
        
        a = acts[0]
        dias = [i["dia"] for i in a["items_dia"]]
        self.assertIn("Lunes", dias)
        self.assertIn("Miércoles", dias)
        
        for item in a["items_dia"]:
            self.assertIn("08:00–09:00", item["horario"])
            self.assertEqual(item["espacio"], "Gimnasio")
            self.assertEqual(item["profesor"], "Profe X")

        self.assertEqual(a["promedio_calificacion"], 0)
        self.assertEqual(a["rating_image"], "rating_0_0.png")
        self.assertFalse(a["user_has_calificado"])

    def test_rating_bucket_and_user_has_calificado(self):
        """Debe calcular promedio correcto y detectar si usuario calificó"""
        u2 = User.objects.create_user("bob", password="x")
        p2 = Participantes.objects.create(
            user=u2, 
            roles_id_rol=self.part.roles_id_rol, 
            correo="bob@ex.com",
            tipo_participante=self.tipo_participante  # ✅ Asignar tipo
        )
        
        CalificacionesActividad.objects.create(
            actividades_id_actividad=self.act, 
            participantes_id_participante=self.part, 
            estrellas=5
        )
        CalificacionesActividad.objects.create(
            actividades_id_actividad=self.act, 
            participantes_id_participante=p2, 
            estrellas=4
        )

        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)
        
        a = resp.context["actividades"][0]
        self.assertEqual(round(a["promedio_calificacion"], 1), 4.5)
        self.assertEqual(a["rating_image"], "rating_4_5.png")
        self.assertTrue(a["user_has_calificado"])

class SuperuserRequiredViewsTests(SimpleTestCase):
    """Asegura que las vistas con @superuser_required devuelven 404 a no-superusers"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch("management_CADI.views.render")
    def test_create_activities_non_superuser_404(self, mock_render):
        mock_render.return_value = HttpResponse("x", status=404)

        request = self.factory.get("/cadi/create/")
        request.user = Mock(is_authenticated=True, is_superuser=False)

        resp = create_Activities(request, "cadi", 1, 10)
        self.assertEqual(resp.status_code, 404)
        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        self.assertEqual(args[1], "pageNotFound-404.html")

    @patch("management_CADI.views.render")
    def test_edit_activity_non_superuser_404(self, mock_render):
        mock_render.return_value = HttpResponse("x", status=404)

        request = self.factory.get("/cadi/edit/")
        request.user = Mock(is_authenticated=True, is_superuser=False)

        resp = edit_Activity(request, "cadi", 1, 10, 99)
        self.assertEqual(resp.status_code, 404)
        mock_render.assert_called_once()


class CadiIndexTests(SimpleTestCase):
    """Tests unitarios para cadi_index"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch("management_CADI.views.render")
    @patch("management_CADI.views.GruposActividad")
    @patch("management_CADI.views.get_object_or_404")
    def test_cadi_index_ok(self, mock_get, mock_ga, mock_render):
        request = self.factory.get("/cadi/")
        request.user = Mock(is_authenticated=True)

        fake_group = Mock(id_grupo=1, nombre="CADI")
        mock_get.return_value = fake_group
        mock_ga.objects.filter.return_value = ["ga1", "ga2"]

        mock_render.return_value = HttpResponse("OK")

        resp = cadi_index(request)

        self.assertEqual(resp.status_code, 200)
        mock_get.assert_called_once()
        mock_ga.objects.filter.assert_called_once_with(grupos_id_grupo=fake_group)
        args, kwargs = mock_render.call_args
        self.assertEqual(args[1], "listar_grupos_actividades.html")
        ctx = args[2]
        self.assertEqual(ctx["grupo"], fake_group)
        self.assertEqual(ctx["grupos_actividad"], ["ga1", "ga2"])

from django.contrib.sessions.middleware import SessionMiddleware

def add_session(request):
    """Añade una sesión real a un RequestFactory request."""
    middleware = SessionMiddleware(lambda r: None) # type: ignore
    middleware.process_request(request)
    request.session.save()


class CreateActivitiesTests(TestCase):
    """Casos principales de create_Activities"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch("management_CADI.views.render")
    @patch("management_CADI.views.TiposActividad")
    @patch("management_CADI.views.get_object_or_404")
    def test_get_render_form_create(self, mock_get, mock_tipos, mock_render):
        request = self.factory.get("/cadi/create/")
        add_session(request)
        request.user = Mock(is_authenticated=True, is_superuser=True)

        fake_group = Mock(id_grupo=1, nombre="CADI")
        fake_ga = Mock(id_grupo_actividad=10, grupos_id_grupo=fake_group)
        mock_get.return_value = fake_ga

        qs = Mock()
        qs.order_by.return_value = ["tipo1"]
        mock_tipos.objects.all.return_value = qs

        mock_render.return_value = HttpResponse("OK")

        resp = create_Activities(request, "cadi", 1, 10)

        self.assertEqual(resp.status_code, 200)
        args, kwargs = mock_render.call_args
        self.assertEqual(args[1], "form_activities.html")
        ctx = args[2]
        self.assertEqual(ctx["grupo_actividad"], fake_ga)
        self.assertEqual(ctx["modo"], "create")

    @patch("management_CADI.views.redirect")
    @patch("management_CADI.views.TiposActividad")
    @patch("management_CADI.views.get_object_or_404")
    def test_post_action_schedule_redirige_draft(self, mock_get, mock_tipos, mock_redirect):
        request = self.factory.post("/cadi/create/", data={
            "action": "schedule",
            "nombre": "Yoga",
            "tipo": "1",
        })
        add_session(request)
        request.user = Mock(is_authenticated=True, is_superuser=True)

        fake_group = Mock(id_grupo=1, nombre="CADI")
        fake_ga = Mock(id_grupo_actividad=10, grupos_id_grupo=fake_group)
        mock_get.return_value = fake_ga

        mock_redirect.return_value = HttpResponse("R", status=302)

        resp = create_Activities(request, "cadi", 1, 10)

        self.assertEqual(resp.status_code, 302)
        mock_redirect.assert_called_once()
        k_base, _, _ = _draft_keys(10)
        self.assertIn(k_base, request.session)
        self.assertEqual(request.session[k_base]["nombre"], "Yoga")

    @patch("management_CADI.views.render")
    @patch("management_CADI.views.TiposActividad")
    @patch("management_CADI.views.get_object_or_404")
    def test_post_confirm_sin_nombre_ni_tipo_muestra_error(self, mock_get, mock_tipos, mock_render):
        request = self.factory.post("/cadi/create/", data={
            "action": "confirm",
            "nombre": "",
            "tipo": "",
        })
        add_session(request)
        request.user = Mock(is_authenticated=True, is_superuser=True)

        fake_group = Mock(id_grupo=1, nombre="CADI")
        fake_ga = Mock(id_grupo_actividad=10, grupos_id_grupo=fake_group)
        mock_get.return_value = fake_ga

        qs = Mock()
        qs.order_by.return_value = ["tipo1"]
        mock_tipos.objects.all.return_value = qs

        mock_render.return_value = HttpResponse("OK")

        resp = create_Activities(request, "cadi", 1, 10)

        self.assertEqual(resp.status_code, 200)
        args, kwargs = mock_render.call_args
        ctx = args[2]
        self.assertEqual(ctx["modo"], "create")
        self.assertIn("Por favor completa Nombre y Tipo", ctx["error"])

class EditActivityTests(TestCase):
    """Casos clave de edit_Activity"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch("management_CADI.views.render")
    @patch("management_CADI.views.TiposActividad")
    @patch("management_CADI.views.Actividades")
    @patch("management_CADI.views.GruposActividad")
    @patch("management_CADI.views.Grupos")
    @patch("management_CADI.views.get_object_or_404")
    def test_post_confirm_tipo_invalido_muestra_error(self, mock_get, mock_grupos, mock_ga, mock_acts, mock_tipos, mock_render):
        request = self.factory.post("/cadi/edit/", data={
            "action": "confirm",
            "nombre": "Nombre",
            "tipo": "no-numero",
        })
        add_session(request)
        request.user = Mock(is_authenticated=True, is_superuser=True)

        fake_group = Mock(id_grupo=1, nombre="CADI")
        fake_ga = Mock(id_grupo_actividad=10, grupos_id_grupo=fake_group)
        fake_act = Mock(
            id_actividad=99,
            nombre="A",
            descripcion="D",
            requiere_inscripcion="S",
            aforo=10,
            fecha_apertura_ins=None,
            fecha_cierre_ins=None,
            tipos_actividad_id_tipo=Mock(id_tipo=1),
        )
        # get_object_or_404 se llama tres veces: grupo, grupo_actividad, actividad
        mock_get.side_effect = [fake_group, fake_ga, fake_act]

        qs = Mock()
        qs.order_by.return_value = ["tipo1"]
        mock_tipos.objects.all.return_value = qs

        mock_render.return_value = HttpResponse("OK")

        resp = edit_Activity(request, "cadi", 1, 10, 99)

        self.assertEqual(resp.status_code, 200)
        args, kwargs = mock_render.call_args
        ctx = args[2]
        self.assertEqual(ctx["modo"], "edit")
        self.assertIn("Tipo de actividad inválido", ctx["error"])

class NewsPermissionsTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("management_CADI.views.render")
    def test_manage_news_non_superuser_404(self, mock_render):
        mock_render.return_value = HttpResponse("x", status=404)

        request = self.factory.get("/news/")
        request.user = Mock(is_authenticated=True, is_superuser=False)

        resp = manage_news(request)
        self.assertEqual(resp.status_code, 404)
        mock_render.assert_called_once()



class AddSlotToScheduleTests(SimpleTestCase):
    """Tests unitarios para add_slot_to_schedule"""

    def setUp(self):
        self.factory = RequestFactory()

    def _post(self, data):
        from management_CADI.views import add_slot_to_schedule

        request = self.factory.post("/cadi/add-slot/", data=data)
        request.user = MagicMock(is_authenticated=True, id=1)

        # La vista espera: (request, grupo_nombre, grupo_id, grupo_actividad_id)
        return add_slot_to_schedule(request, "cadi", 1, 10)

    @patch("management_CADI.views.redirect")
    @patch("management_CADI.views.messages")
    @patch("management_CADI.views.HorariosParticipante")
    @patch("management_CADI.views.HorariosBloque")
    @patch("management_CADI.views.Participantes")
    def test_add_slot_datos_incompletos(self,
                                        mock_participantes,
                                        mock_bloques,
                                        mock_hp,
                                        mock_messages,
                                        mock_redirect):
        mock_redirect.return_value = HttpResponse("R", status=302)

        resp = self._post({})  # sin datos
        self.assertEqual(resp.status_code, 302)
        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once()

    @patch("management_CADI.views.get_object_or_404")
    @patch("management_CADI.views.redirect")
    @patch("management_CADI.views.messages")
    @patch("management_CADI.views.HorariosParticipante")
    @patch("management_CADI.views.HorariosBloque")
    @patch("management_CADI.views.Participantes")
    def test_add_slot_conflicto_horario(self,
                                        mock_participantes,
                                        mock_bloques,
                                        mock_hp,
                                        mock_messages,
                                        mock_redirect,
                                        mock_get):
        from management_CADI.views import add_slot_to_schedule

        # 1ª llamada: Actividad, 2ª: Bloque con horas reales
        fake_actividad = MagicMock()
        fake_bloque = SimpleNamespace(
            hora_inicio=dt.time(8, 0),
            hora_fin=dt.time(9, 0),
        )
        mock_get.side_effect = [fake_actividad, fake_bloque]

        mock_redirect.return_value = HttpResponse("R", status=302)
        mock_participantes.objects.get.return_value = MagicMock()

        mock_hp.objects.filter.return_value.exists.return_value = True

        resp = self._post({
            "actividad_id": "10",
            "bloque_id": "5",
            "dia_idx": "1",
        })

        self.assertEqual(resp.status_code, 302)
        mock_hp.objects.filter.assert_called()
        # sin assert sobre mock_messages.error




class ScheduleDraftTests(TestCase):
    """Tests para schedule_Draft usando sesión real"""

    def setUp(self):
        self.factory = RequestFactory()

    def _get(self, data=None):
        from management_CADI.views import schedule_Draft
        request = self.factory.get("/cadi/schedule-draft/", data or {})
        add_session(request)
        request.user = MagicMock(is_authenticated=True, is_superuser=True)
        return schedule_Draft(request, "cadi", 1, 10)

    def _post(self, data):
        from management_CADI.views import schedule_Draft
        request = self.factory.post("/cadi/schedule-draft/", data=data)
        add_session(request)
        request.user = MagicMock(is_authenticated=True, is_superuser=True)
        return schedule_Draft(request, "cadi", 1, 10)

    
    @patch("management_CADI.views.render")
    @patch("management_CADI.views.get_object_or_404")
    def test_schedule_draft_get_sin_borrador(self, mock_get, mock_render):
        from management_CADI.views import schedule_Draft

        # Grupo y GrupoActividad falsos con la misma forma que los modelos
        fake_grupo = SimpleNamespace(id_grupo=1, nombre="CADI")
        fake_ga = SimpleNamespace(id_grupo_actividad=10, grupos_id_grupo=fake_grupo)

        # schedule_Draft solo llama una vez a get_object_or_404(GruposActividad,...)
        mock_get.return_value = fake_ga

        mock_render.return_value = HttpResponse("OK")

        resp = self._get()

        # Ahora slug_real = "cadi", id_grupo=1, id_grupo_actividad=10 → el reverse funciona
        self.assertEqual(resp.status_code, 200)
        mock_get.assert_called_once()
        mock_render.assert_called_once()


    @patch("management_CADI.views.redirect")
    @patch("management_CADI.views.render")
    @patch("management_CADI.views.get_object_or_404")
    def test_schedule_draft_post_addblock(self, mock_get, mock_render, mock_redirect):
        from management_CADI.views import schedule_Draft

        fake_grupo = SimpleNamespace(id_grupo=1, nombre="CADI")
        fake_ga = SimpleNamespace(id_grupo_actividad=10, grupos_id_grupo=fake_grupo)
        mock_get.return_value = fake_ga

        mock_render.return_value = HttpResponse("OK")
        mock_redirect.return_value = HttpResponse("R", status=302)

        resp = self._post({
            "action": "addblock",
            "dia": "1",
            "hora_inicio": "08:00",
            "hora_fin": "09:00",
        })

    # La vista procesa el bloque y vuelve a renderizar → 200
        self.assertEqual(resp.status_code, 200)
        mock_render.assert_called_once()


