"""
Tests unitarios para universitaryWellbeing/views.py
Cobertura completa: Login, Register, Preferences, Schedule, Home, Profile
Estilo: SimpleTestCase con mocks (siguiendo patrón Analytics_Reports)
"""
from django.test import SimpleTestCase, TestCase, RequestFactory
from unittest.mock import patch, MagicMock, Mock, call
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from universitaryWellbeing import views as vw
from universitaryWellbeing.forms import UserLoginForm, UserRegisterForm
import json
import datetime as dt


# ==========================================================
# TESTS DE HELPERS Y UTILIDADES
# ==========================================================

class HelpersTestCase(SimpleTestCase):
    """Pruebas de funciones auxiliares"""

    @patch('universitaryWellbeing.views.Group.objects')
    def test_is_role_admin_with_group(self, mock_groups):
        """Usuario en grupo admin debe ser admin"""
        user = MagicMock()
        user.is_superuser = False
        user.groups.filter.return_value.exists.return_value = True
        
        result = vw.is_role_admin(user)
        
        self.assertTrue(result)
        user.groups.filter.assert_called_once_with(name="admin")

    def test_is_role_admin_superuser(self):
        """Superuser debe ser admin"""
        user = MagicMock()
        user.is_superuser = True
        user.groups.filter.return_value.exists.return_value = False
        
        result = vw.is_role_admin(user)
        
        self.assertTrue(result)

    @patch('universitaryWellbeing.views.Group.objects')
    def test_is_role_admin_regular_user(self, mock_groups):
        """Usuario regular no debe ser admin"""
        user = MagicMock()
        user.is_superuser = False
        user.groups.filter.return_value.exists.return_value = False
        
        result = vw.is_role_admin(user)
        
        self.assertFalse(result)

    def test_django_weekday_to_fc_dow(self):
        """Debe convertir correctamente días de la semana"""
        # Django: 1=Dom, 2=Lun, ..., 7=Sab
        # FullCalendar: 0=Dom, 1=Lun, ..., 6=Sab
        
        self.assertEqual(vw._django_weekday_to_fc_dow(1), 1)  # Domingo
        self.assertEqual(vw._django_weekday_to_fc_dow(2), 2)  # Lunes
        self.assertEqual(vw._django_weekday_to_fc_dow(7), 0)  # Sábado


# ==========================================================
# TESTS DE LOGIN
# ==========================================================

class UserLoginTests(SimpleTestCase):
    """Pruebas de la vista user_login"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.render')
    def test_login_get_renders_form(self, mock_render, mock_form_class):
        """GET debe renderizar formulario de login"""
        mock_form_class.return_value = MagicMock()
        
        request = self.factory.get('/login/')
        
        vw.user_login(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "login.html")
        self.assertIn("form", mock_render.call_args[0][2])

    @patch('universitaryWellbeing.views.is_role_admin')
    @patch('universitaryWellbeing.views.login')
    @patch('universitaryWellbeing.views.redirect')
    def test_login_admin_redirects_to_cadi_admin(self, mock_redirect, mock_form_class,
                                                  mock_login_func, mock_is_admin):
        """Admin debe redirigir a cadi_admin"""
        mock_is_admin.return_value = True
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.user = MagicMock()
        mock_form_class.return_value = mock_form
        
        request = self.factory.post('/login/', {'username': 'admin', 'password': 'pass'})
        
        vw.user_login(request)
        
        mock_login_func.assert_called_once()
        mock_redirect.assert_called_once_with("cadi_admin")

    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.is_role_admin')
    @patch('universitaryWellbeing.views.login')
    @patch('universitaryWellbeing.views.redirect')
    def test_login_user_without_preferences_redirects_to_preferences(
        self, mock_redirect, mock_form_class, mock_login_func, 
        mock_is_admin, mock_preferencias, mock_participantes
    ):
        """Usuario sin preferencias debe redirigir a preferences"""
        mock_is_admin.return_value = False
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.user = MagicMock()
        mock_form_class.return_value = mock_form
        
        # Usuario tiene participante pero no preferencias
        mock_participantes.get.return_value = MagicMock()
        mock_preferencias.filter.return_value.exists.return_value = False
        
        request = self.factory.post('/login/', {})
        
        vw.user_login(request)
        
        mock_redirect.assert_called_once_with("preferences")

    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.is_role_admin')
    @patch('universitaryWellbeing.views.login')
    @patch('universitaryWellbeing.views.redirect')
    def test_login_user_with_preferences_redirects_to_home(
        self, mock_redirect, mock_form_class, mock_login_func,
        mock_is_admin, mock_preferencias, mock_participantes
    ):
        """Usuario con preferencias debe redirigir a home"""
        mock_is_admin.return_value = False
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.user = MagicMock()
        mock_form_class.return_value = mock_form
        
        mock_participantes.get.return_value = MagicMock()
        mock_preferencias.filter.return_value.exists.return_value = True
        
        request = self.factory.post('/login/', {})
        
        vw.user_login(request)
        
        mock_redirect.assert_called_once_with("home")

    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    def test_login_invalid_form_shows_errors(self, mock_redirect, mock_messages, mock_form_class):
        """Formulario inválido debe mostrar errores"""
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_form.errors = {"username": ["Usuario inválido"]}
        mock_form_class.return_value = mock_form
        
        request = self.factory.post('/login/', {})
        
        vw.user_login(request)
        
        mock_messages.error.assert_called()
        mock_redirect.assert_called_once_with("login")


# ==========================================================
# TESTS DE REGISTRO
# ==========================================================

class RegisterTests(SimpleTestCase):
    """Pruebas de la vista register"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.UserRegisterForm')
    @patch('universitaryWellbeing.views.render')
    def test_register_get_renders_form(self, mock_render, mock_form_class):
        """GET debe renderizar formulario de registro"""
        mock_form_class.return_value = MagicMock()
        
        request = self.factory.get('/register/')
        
        vw.register(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "auth/register.html")
        self.assertIn("form", mock_render.call_args[0][2])

    @patch('universitaryWellbeing.views.Roles.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.User.objects')
    @patch('universitaryWellbeing.views.UserRegisterForm')
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    def test_register_creates_user_and_participante(
        self, mock_redirect, mock_messages, mock_form_class,
        mock_user_model, mock_participantes, mock_roles
    ):
        """Registro exitoso debe crear User y Participante"""
        # Mock form
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = {
            'cedula': '1234567890',
            'nombre_completo': 'Juan Pérez',
            'email': 'juan@test.com',
            'password': 'pass123'
        }
        mock_form_class.return_value = mock_form
        
        # Mock User creation
        mock_user = MagicMock()
        mock_user_model.create_user.return_value = mock_user
        
        # Mock Rol
        mock_rol = MagicMock()
        mock_rol.grupo_d = MagicMock()
        mock_roles.get.return_value = mock_rol
        
        request = self.factory.post('/register/', {})
        
        vw.register(request)
        
        # Verificaciones
        mock_user_model.create_user.assert_called_once()
        create_args = mock_user_model.create_user.call_args[1]
        self.assertEqual(create_args['username'], '1234567890')
        self.assertEqual(create_args['email'], 'juan@test.com')
        
        mock_participantes.create.assert_called_once()
        mock_messages.success.assert_called_once()
        mock_redirect.assert_called_once_with("login")

    @patch('universitaryWellbeing.views.UserRegisterForm')
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    def test_register_invalid_form_shows_errors(self, mock_redirect, mock_messages, mock_form_class):
        """Formulario inválido debe mostrar errores"""
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_form.errors = {"email": ["Email inválido"]}
        mock_form_class.return_value = mock_form
        
        request = self.factory.post('/register/', {})
        
        vw.register(request)
        
        mock_messages.error.assert_called()
        mock_redirect.assert_called_once_with("register")

    @patch('universitaryWellbeing.views.Roles.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.User.objects')
    @patch('universitaryWellbeing.views.UserRegisterForm')
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    def test_register_nombre_con_espacios(
        self, mock_redirect, mock_messages, mock_form_class,
        mock_user_model, mock_participantes, mock_roles
    ):
        """Debe separar correctamente nombre y apellido"""
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = {
            'cedula': '1234567890',
            'nombre_completo': 'Juan Carlos Pérez González',
            'email': 'juan@test.com',
            'password': 'pass123'
        }
        mock_form_class.return_value = mock_form
        
        mock_user_model.create_user.return_value = MagicMock()
        mock_roles.get.return_value = MagicMock(grupo_d=None)
        
        request = self.factory.post('/register/', {})
        
        vw.register(request)
        
        create_args = mock_user_model.create_user.call_args[1]
        self.assertEqual(create_args['first_name'], 'Juan')
        self.assertEqual(create_args['last_name'], 'Carlos Pérez González')


# ==========================================================
# TESTS DE LOGOUT
# ==========================================================

class LogoutTests(SimpleTestCase):
    """Pruebas de la vista user_logout"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.logout')
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    def test_logout_clears_session(self, mock_redirect, mock_messages, mock_logout):
        """Logout debe cerrar sesión y redirigir"""
        request = self.factory.post('/logout/')
        
        vw.user_logout(request)
        
        mock_logout.assert_called_once_with(request)
        mock_messages.success.assert_called_once()
        mock_redirect.assert_called_once_with("login")


# ==========================================================
# TESTS DE PREFERENCIAS
# ==========================================================

class PreferencesTests(SimpleTestCase):
    """Pruebas de la vista preferences"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.redirect')
    def test_preferences_redirects_if_already_exists(self, mock_redirect, mock_participantes):
        """Debe redirigir si ya tiene preferencias"""
        mock_participante = MagicMock()
        mock_participante.preferencias = MagicMock()  # hasattr será True
        mock_participantes.get.return_value = mock_participante
        
        request = self.factory.get('/preferences/')
        request.user = MagicMock()
        
        vw.preferences(request)
        
        mock_redirect.assert_called_once_with('home')

    @patch('universitaryWellbeing.views.TiposActividad.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.render')
    def test_preferences_get_renders_categories(self, mock_render, mock_participantes, mock_tipos):
        """GET debe renderizar categorías disponibles"""
        mock_participante = MagicMock(spec=['id_participante'])  # Sin 'preferencias'
        mock_participantes.get.return_value = mock_participante
        
        mock_tipos.all.return_value = [
            MagicMock(id_tipo=1, nombre_tipo="Deporte"),
            MagicMock(id_tipo=2, nombre_tipo="Cultural")
        ]
        
        request = self.factory.get('/preferences/')
        request.user = MagicMock()
        
        vw.preferences(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], 'list_preferences.html')
        context = mock_render.call_args[0][2]
        self.assertIn('categorias', context)

    @patch('universitaryWellbeing.views.PreferenciasActividades.objects')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.TiposActividad.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.redirect')
    def test_preferences_post_creates_preferencias(
        self, mock_redirect, mock_participantes, mock_tipos,
        mock_preferencias, mock_pref_actividades
    ):
        """POST debe crear preferencias del usuario"""
        mock_participante = MagicMock(spec=['id_participante'])
        mock_participantes.get.return_value = mock_participante
        
        mock_pref = MagicMock()
        mock_preferencias.create.return_value = mock_pref
        
        mock_tipo = MagicMock()
        mock_tipos.objects.get.return_value = mock_tipo
        
        request = self.factory.post('/preferences/')
        request.POST = MagicMock()
        request.POST.getlist.return_value = ['1', '2', '3']
        request.user = MagicMock()
        
        vw.preferences(request)
        
        mock_preferencias.create.assert_called_once()
        self.assertEqual(mock_pref_actividades.create.call_count, 3)
        mock_redirect.assert_called_once_with('home')


# ==========================================================
# TESTS DE HORARIO/SCHEDULE
# ==========================================================

class ScheduleTests(SimpleTestCase):
    """Pruebas de la vista schedule"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.get_object_or_404')
    @patch('universitaryWellbeing.views.render')
    def test_schedule_renders_eventos(self, mock_render, mock_get, mock_horarios):
        """Debe renderizar eventos del participante"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_get.return_value = mock_participante
        
        # Mock eventos
        evento_mock = MagicMock()
        evento_mock.id_horario = 1
        evento_mock.titulo = "Yoga"
        evento_mock.fecha_inicio = dt.datetime(2025, 11, 10, 10, 0)
        evento_mock.fecha_fin = dt.datetime(2025, 11, 10, 11, 0)
        evento_mock.actividades_id_actividad = MagicMock()
        evento_mock.citas_id_cita = None
        evento_mock.partidos_id_partido = None
        evento_mock.fuente_manual = 'N'
        evento_mock.notas = "Clase de yoga"
        
        mock_horarios.filter.return_value = [evento_mock]
        
        request = self.factory.get('/schedule/')
        request.user = MagicMock(id=1)
        
        vw.schedule(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "Horario.html")
        context = mock_render.call_args[0][2]
        self.assertIn("eventos_json", context)
        
        # Verificar que eventos_json es JSON válido
        eventos_json = json.loads(context["eventos_json"])
        self.assertEqual(len(eventos_json), 1)
        self.assertEqual(eventos_json[0]["title"], "Yoga")

    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.get_object_or_404')
    @patch('universitaryWellbeing.views.render')
    def test_schedule_evento_recurrente(self, mock_render, mock_get, mock_horarios):
        """Evento manual de actividad debe ser recurrente"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_get.return_value = mock_participante
        
        evento_mock = MagicMock()
        evento_mock.id_horario = 1
        evento_mock.titulo = "Clase semanal"
        evento_mock.fecha_inicio = dt.datetime(2025, 11, 10, 10, 0)  # Lunes
        evento_mock.fecha_fin = dt.datetime(2025, 11, 10, 11, 0)
        evento_mock.actividades_id_actividad = MagicMock()
        evento_mock.citas_id_cita = None
        evento_mock.partidos_id_partido = None
        evento_mock.fuente_manual = 'S'  # Manual = recurrente
        evento_mock.notas = None
        
        mock_horarios.filter.return_value = [evento_mock]
        
        request = self.factory.get('/schedule/')
        request.user = MagicMock(id=1)
        
        vw.schedule(request)
        
        context = mock_render.call_args[0][2]
        eventos_json = json.loads(context["eventos_json"])
        
        # Verificar que tiene daysOfWeek (recurrente)
        self.assertIn("daysOfWeek", eventos_json[0])
        self.assertTrue(eventos_json[0]["extendedProps"]["es_recurrente"])


# ==========================================================
# TESTS DE ELIMINAR EVENTO
# ==========================================================

class EliminarEventoTests(SimpleTestCase):
    """Pruebas de la vista eliminar_evento"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.get_object_or_404')
    def test_eliminar_evento_manual_success(self, mock_get):
        """Debe eliminar evento manual correctamente"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        
        mock_evento = MagicMock()
        mock_evento.titulo = "Mi evento"
        mock_evento.fuente_manual = 'S'
        
        mock_get.side_effect = [mock_participante, mock_evento]
        
        request = self.factory.post('/schedule/delete/1/')
        request.user = MagicMock(id=1)
        
        response = vw.eliminar_evento(request, 1)
        
        mock_evento.delete.assert_called_once()
        self.assertIsInstance(response, JsonResponse)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    @patch('universitaryWellbeing.views.get_object_or_404')
    def test_eliminar_evento_automatico_forbidden(self, mock_get):
        """No debe eliminar evento automático"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        
        mock_evento = MagicMock()
        mock_evento.fuente_manual = 'N'  # Automático
        
        mock_get.side_effect = [mock_participante, mock_evento]
        
        request = self.factory.post('/schedule/delete/1/')
        request.user = MagicMock(id=1)
        
        response = vw.eliminar_evento(request, 1)
        
        mock_evento.delete.assert_not_called()
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['success'])


# ==========================================================
# TESTS DE CALENDARIO UNIFICADO
# ==========================================================

class CalendarioUnificadoTests(SimpleTestCase):
    """Pruebas de la vista calendario_unificado"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.HorariosActividad.objects')
    @patch('universitaryWellbeing.views.HorariosBloque.objects')
    @patch('universitaryWellbeing.views.Actividades.objects')
    @patch('universitaryWellbeing.views.TiposActividad.objects')
    @patch('universitaryWellbeing.views.render')
    def test_calendario_unificado_renders(
        self, mock_render, mock_tipos, mock_actividades,
        mock_bloques, mock_horarios_act
    ):
        """Debe renderizar calendario con actividades"""
        # Mock tipos
        mock_tipos.values.return_value.order_by.return_value = []
        
        # Mock actividades
        mock_qs = MagicMock()
        mock_qs.select_related.return_value.values.return_value = [
            {
                'id_actividad': 1,
                'nombre': 'Yoga',
                'descripcion': 'Clase de yoga',
                'tipos_actividad_id_tipo': 1,
                'tipos_actividad_id_tipo__nombre_tipo': 'Deporte'
            }
        ]
        mock_actividades.all.return_value = mock_qs
        
        # Mock bloques
        mock_bloques.filter.return_value.values.return_value = [
            {
                'id_horario_bloque': 1,
                'actividades_id_actividad': 1,
                'profesor': 'Prof. Juan',
                'lugar': 'Gimnasio',
                'hora_inicio': dt.time(10, 0),
                'hora_fin': dt.time(11, 0)
            }
        ]
        
        # Mock días
        mock_horarios_act.filter.return_value.values.return_value = [
            {'horario_bloque_id': 1, 'dia_semana': 2}  # Lunes
        ]
        
        request = self.factory.get('/calendario/')
        request.GET = {}
        
        vw.calendario_unificado(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "calendario_unificado.html")
        context = mock_render.call_args[0][2]
        self.assertIn("eventos_json", context)

    @patch('universitaryWellbeing.views.TiposActividad.objects')
    @patch('universitaryWellbeing.views.Actividades.objects')
    @patch('universitaryWellbeing.views.render')
    def test_calendario_unificado_filtro_tipo(self, mock_render, mock_actividades, mock_tipos):
        """Debe filtrar por tipo de actividad"""
        mock_tipos.values.return_value.order_by.return_value = []
        
        mock_qs = MagicMock()
        mock_qs.select_related.return_value.values.return_value = []
        mock_qs.filter.return_value = mock_qs
        
        mock_actividades.all.return_value = mock_qs
        
        request = self.factory.get('/calendario/?tipo=1')
        request.GET = {'tipo': '1'}
        
        vw.calendario_unificado(request)
        
        # Verificar que se aplicó el filtro
        mock_qs.filter.assert_called_once()


# ==========================================================
# TESTS DE HOME USER
# ==========================================================

class HomeUserTests(SimpleTestCase):
    """Pruebas de la vista home_user"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.render')
    def test_home_user_superuser_returns_404(self, mock_render):
        """Superuser debe recibir 404"""
        request = self.factory.get('/home/')
        request.user = MagicMock()
        request.user.is_superuser = True
        
        vw.home_user(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "pageNotFound-404.html")
        self.assertEqual(mock_render.call_args[1]['status'], 404)

    @patch('universitaryWellbeing.views.get_user_calendar')
    @patch('universitaryWellbeing.views.get_user_schedule')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.Actividades.objects')
    @patch('universitaryWellbeing.views.render')
    def test_home_user_renders_with_context(
        self, mock_render, mock_actividades, mock_participantes,
        mock_schedule, mock_calendar
    ):
        """Debe renderizar home con contexto completo"""
        # Mock participante con rol
        mock_part = MagicMock()
        mock_part.roles_id_rol.nombre_rol = "Estudiante"
        mock_participantes.filter.return_value.select_related.return_value.first.return_value = mock_part
        
        mock_actividades.values.return_value = []
        mock_schedule.return_value = []
        mock_calendar.return_value = []
        
        request = self.factory.get('/home/')
        request.user = MagicMock()
        request.user.is_superuser = False
        
        vw.home_user(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "home_user.html")
        context = mock_render.call_args[0][2]
        self.assertIn("user_rol", context)
        self.assertEqual(context["user_rol"], "Estudiante")


# ==========================================================
# TESTS DE HOME ADMIN
# ==========================================================

class HomeAdminTests(SimpleTestCase):
    """Pruebas de la vista home_admin"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.render')
    def test_home_admin_renders(self, mock_render):
        """Debe renderizar home admin"""
        request = self.factory.get('/admin-home/')
        
        vw.home_admin(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "home_admin.html")


# ==========================================================
# TESTS DE FUNCIONES AUXILIARES (get_recommendations, etc.)
# ==========================================================

class HelperFunctionsTests(SimpleTestCase):
    """Pruebas de funciones auxiliares de vistas"""

    @patch('universitaryWellbeing.views.Actividades.objects')
    @patch('universitaryWellbeing.views.PreferenciasActividades.objects')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_recommendations_for_user_success(
        self, mock_participantes, mock_preferencias,
        mock_pref_actividades, mock_actividades
    ):
        """Debe retornar actividades recomendadas según preferencias"""
        mock_user = MagicMock()
        mock_participante = MagicMock()
        mock_participantes.get.return_value = mock_participante
        
        mock_pref = MagicMock()
        mock_preferencias.get.return_value = mock_pref
        
        mock_pref_actividades.filter.return_value.values_list.return_value = [1, 2, 3]
        
        mock_actividades_qs = MagicMock()
        mock_actividades.filter.return_value = mock_actividades_qs
        
        result = vw.get_recommendations_for_user(mock_user)
        
        self.assertEqual(result, mock_actividades_qs)
        mock_actividades.filter.assert_called_once()

    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_recommendations_for_user_no_participante(self, mock_participantes):
        """Debe retornar lista vacía si no existe participante"""
        mock_user = MagicMock()
        mock_participantes.get.side_effect = vw.Participantes.DoesNotExist
        
        result = vw.get_recommendations_for_user(mock_user)
        
        self.assertEqual(result, [])

    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_recommendations_for_user_no_preferencias(
        self, mock_participantes, mock_preferencias
    ):
        """Debe retornar lista vacía si no existen preferencias"""
        mock_user = MagicMock()
        mock_participante = MagicMock()
        mock_participantes.get.return_value = mock_participante
        mock_preferencias.get.side_effect = vw.Preferencias.DoesNotExist
        
        result = vw.get_recommendations_for_user(mock_user)
        
        self.assertEqual(result, [])

    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_user_schedule_success(self, mock_participantes, mock_horarios):
        """Debe retornar horarios del participante"""
        mock_user = MagicMock()
        mock_participante = MagicMock()
        mock_participantes.get.return_value = mock_participante
        
        mock_horarios_qs = MagicMock()
        mock_horarios.filter.return_value = mock_horarios_qs
        
        result = vw.get_user_schedule(mock_user)
        
        self.assertEqual(result, mock_horarios_qs)

    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_user_schedule_no_participante(self, mock_participantes):
        """Debe retornar lista vacía si no existe participante"""
        mock_user = MagicMock()
        mock_participantes.get.side_effect = vw.Participantes.DoesNotExist
        
        result = vw.get_user_schedule(mock_user)
        
        self.assertEqual(result, [])

    @patch('universitaryWellbeing.views.Citas.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_user_calendar_success(self, mock_participantes, mock_citas):
        """Debe retornar citas del participante"""
        mock_user = MagicMock()
        mock_participante = MagicMock()
        mock_participantes.get.return_value = mock_participante
        
        mock_citas_qs = MagicMock()
        mock_citas.filter.return_value = mock_citas_qs
        
        result = vw.get_user_calendar(mock_user)
        
        self.assertEqual(result, mock_citas_qs)

    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_user_calendar_no_participante(self, mock_participantes):
        """Debe retornar lista vacía si no existe participante"""
        mock_user = MagicMock()
        mock_participantes.get.side_effect = vw.Participantes.DoesNotExist
        
        result = vw.get_user_calendar(mock_user)
        
        self.assertEqual(result, [])


# ==========================================================
# TESTS DE PROFILE
# ==========================================================

class ProfileTests(SimpleTestCase):
    """Pruebas de la vista profile"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.Notificaciones.objects')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.render')
    def test_profile_renders_with_context(
        self, mock_render, mock_participantes, 
        mock_preferencias, mock_notificaciones
    ):
        """Debe renderizar perfil con contexto completo"""
        # Mock participante
        mock_part = MagicMock()
        mock_part.roles_id_rol.nombre_rol = "Estudiante"
        mock_participantes.get.return_value = mock_part
        
        # Mock preferencias y actividades
        mock_pref = MagicMock()
        mock_actividad1 = MagicMock(nombre="Yoga")
        mock_actividad2 = MagicMock(nombre="Fútbol")
        mock_pref.actividades.all.return_value = [mock_actividad1, mock_actividad2]
        mock_preferencias.get.return_value = mock_pref
        
        # Mock notificaciones
        mock_notif_qs = MagicMock()
        mock_notif_qs.order_by.return_value = mock_notif_qs
        mock_notif_qs.filter.return_value.count.return_value = 3
        mock_notificaciones.filter.return_value = mock_notif_qs
        
        request = self.factory.get('/profile/')
        request.user = MagicMock()
        
        vw.profile(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "profile.html")
        context = mock_render.call_args[0][2]
        self.assertIn("participante", context)
        self.assertIn("actividades", context)
        self.assertIn("notificaciones", context)
        self.assertEqual(context["notificaciones_no_leidas"], 3)

    @patch('universitaryWellbeing.views.Notificaciones.objects')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.render')
    def test_profile_sin_preferencias(
        self, mock_render, mock_participantes,
        mock_preferencias, mock_notificaciones
    ):
        """Debe manejar caso sin preferencias"""
        mock_part = MagicMock()
        mock_part.roles_id_rol = None
        mock_participantes.get.return_value = mock_part
        
        mock_preferencias.get.side_effect = vw.Preferencias.DoesNotExist
        
        mock_notif_qs = MagicMock()
        mock_notif_qs.order_by.return_value = mock_notif_qs
        mock_notif_qs.filter.return_value.count.return_value = 0
        mock_notificaciones.filter.return_value = mock_notif_qs
        
        request = self.factory.get('/profile/')
        request.user = MagicMock()
        
        vw.profile(request)
        
        context = mock_render.call_args[0][2]
        self.assertEqual(context["actividades"], [])
        self.assertIsNone(context["user_rol"])


# ==========================================================
# TESTS DE VER NOTIFICACIONES
# ==========================================================

class VerNotificacionesTests(SimpleTestCase):
    """Pruebas de la vista ver_notificaciones"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.Notificaciones.objects')
    @patch('universitaryWellbeing.views.render')
    def test_ver_notificaciones_renders_list(self, mock_render, mock_notificaciones):
        """Debe renderizar lista de notificaciones"""
        mock_notif1 = MagicMock()
        mock_notif1.titulo = "Nueva actividad"
        mock_notif1.mensaje = "Se agregó Yoga"
        
        mock_notif2 = MagicMock()
        mock_notif2.titulo = "Recordatorio"
        mock_notif2.mensaje = "Clase mañana"
        
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = [mock_notif1, mock_notif2]
        mock_notificaciones.filter.return_value = mock_qs
        
        request = self.factory.get('/notificaciones/')
        request.user = MagicMock()
        
        vw.ver_notificaciones(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "notificaciones/notificaciones.html")
        context = mock_render.call_args[0][2]
        self.assertIn("notificaciones", context)
        self.assertEqual(len(context["notificaciones"]), 2)

    @patch('universitaryWellbeing.views.Notificaciones.objects')
    @patch('universitaryWellbeing.views.render')
    def test_ver_notificaciones_sin_notificaciones(self, mock_render, mock_notificaciones):
        """Debe manejar caso sin notificaciones"""
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = []
        mock_notificaciones.filter.return_value = mock_qs
        
        request = self.factory.get('/notificaciones/')
        request.user = MagicMock()
        
        vw.ver_notificaciones(request)
        
        context = mock_render.call_args[0][2]
        self.assertEqual(len(context["notificaciones"]), 0)


# ==========================================================
# TESTS ADICIONALES DE EDGE CASES
# ==========================================================

class EdgeCasesTests(SimpleTestCase):
    """Pruebas de casos límite y edge cases"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.get_object_or_404')
    @patch('universitaryWellbeing.views.render')
    def test_schedule_sin_eventos(self, mock_render, mock_get, mock_horarios):
        """Debe manejar horario sin eventos"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_get.return_value = mock_participante
        
        mock_horarios.filter.return_value = []
        
        request = self.factory.get('/schedule/')
        request.user = MagicMock(id=1)
        
        vw.schedule(request)
        
        context = mock_render.call_args[0][2]
        eventos_json = json.loads(context["eventos_json"])
        self.assertEqual(len(eventos_json), 0)

    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.get_object_or_404')
    @patch('universitaryWellbeing.views.render')
    def test_schedule_evento_con_cita(self, mock_render, mock_get, mock_horarios):
        """Debe asignar color amarillo a citas"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_get.return_value = mock_participante
        
        evento_mock = MagicMock()
        evento_mock.id_horario = 1
        evento_mock.titulo = "Cita médica"
        evento_mock.fecha_inicio = dt.datetime(2025, 11, 10, 14, 0)
        evento_mock.fecha_fin = dt.datetime(2025, 11, 10, 15, 0)
        evento_mock.actividades_id_actividad = None
        evento_mock.citas_id_cita = MagicMock()
        evento_mock.partidos_id_partido = None
        evento_mock.fuente_manual = 'N'
        evento_mock.notas = None
        
        mock_horarios.filter.return_value = [evento_mock]
        
        request = self.factory.get('/schedule/')
        request.user = MagicMock(id=1)
        
        vw.schedule(request)
        
        context = mock_render.call_args[0][2]
        eventos_json = json.loads(context["eventos_json"])
        self.assertEqual(eventos_json[0]["color"], "#E4EB60")
        self.assertEqual(eventos_json[0]["extendedProps"]["tipo"], "cita")

    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.get_object_or_404')
    @patch('universitaryWellbeing.views.render')
    def test_schedule_evento_con_partido(self, mock_render, mock_get, mock_horarios):
        """Debe asignar color naranja a partidos"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_get.return_value = mock_participante
        
        evento_mock = MagicMock()
        evento_mock.id_horario = 1
        evento_mock.titulo = "Partido de fútbol"
        evento_mock.fecha_inicio = dt.datetime(2025, 11, 10, 16, 0)
        evento_mock.fecha_fin = dt.datetime(2025, 11, 10, 18, 0)
        evento_mock.actividades_id_actividad = None
        evento_mock.citas_id_cita = None
        evento_mock.partidos_id_partido = MagicMock()
        evento_mock.fuente_manual = 'N'
        evento_mock.notas = None
        
        mock_horarios.filter.return_value = [evento_mock]
        
        request = self.factory.get('/schedule/')
        request.user = MagicMock(id=1)
        
        vw.schedule(request)
        
        context = mock_render.call_args[0][2]
        eventos_json = json.loads(context["eventos_json"])
        self.assertEqual(eventos_json[0]["color"], "#E9683B")
        self.assertEqual(eventos_json[0]["extendedProps"]["tipo"], "partido")

    @patch('universitaryWellbeing.views.HorariosActividad.objects')
    @patch('universitaryWellbeing.views.HorariosBloque.objects')
    @patch('universitaryWellbeing.views.Actividades.objects')
    @patch('universitaryWellbeing.views.TiposActividad.objects')
    @patch('universitaryWellbeing.views.render')
    def test_calendario_unificado_sin_actividades(
        self, mock_render, mock_tipos, mock_actividades,
        mock_bloques, mock_horarios_act
    ):
        """Debe manejar caso sin actividades disponibles"""
        mock_tipos.values.return_value.order_by.return_value = []
        
        mock_qs = MagicMock()
        mock_qs.select_related.return_value.values.return_value = []
        mock_actividades.all.return_value = mock_qs
        
        request = self.factory.get('/calendario/')
        request.GET = {}
        
        vw.calendario_unificado(request)
        
        context = mock_render.call_args[0][2]
        eventos_json = json.loads(context["eventos_json"])
        self.assertEqual(len(eventos_json), 0)

    @patch('universitaryWellbeing.views.get_object_or_404')
    def test_eliminar_evento_exception_handling(self, mock_get):
        """Debe manejar excepciones al eliminar evento"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        
        mock_evento = MagicMock()
        mock_evento.fuente_manual = 'S'
        mock_evento.delete.side_effect = Exception("Error de base de datos")
        
        mock_get.side_effect = [mock_participante, mock_evento]
        
        request = self.factory.post('/schedule/delete/1/')
        request.user = MagicMock(id=1)
        
        response = vw.eliminar_evento(request, 1)
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn("Error al eliminar", data['message'])