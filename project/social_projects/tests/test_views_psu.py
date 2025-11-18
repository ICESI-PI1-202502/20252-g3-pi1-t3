import datetime as dt
from django.test import TestCase, SimpleTestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock, Mock
from django.utils.timezone import make_aware, get_current_timezone

TZ = get_current_timezone()

# Decorador para bypassear @login_required en todas las vistas
def bypass_login_required(f):
    """Hace que @login_required no haga nada en los tests"""
    return lambda func: func

class TestViewsPSU(SimpleTestCase):
    """Tests simplificados usando mocks para evitar dependencias de BD"""
    
    def setUp(self):
        """Mock del decorador login_required y context processors para todos los tests"""
        self.login_patcher = patch('django.contrib.auth.decorators.login_required', bypass_login_required)
        self.login_patcher.start()
        
        # Mock SOLO del context processor que existe
        self.context_processor_patcher = patch('universitaryWellbeing.context_processors.notificaciones_context', 
                                                return_value={'notificaciones': [], 'notificaciones_no_leidas': 0})
        self.context_processor_patcher.start()
    
    def tearDown(self):
        """Limpiar patches"""
        self.login_patcher.stop()
        self.context_processor_patcher.stop()
    
    @patch("social_projects.views.ProyectosSociales.objects")
    @patch("social_projects.views.is_admin")
    @patch("social_projects.views.render")
    def test_lista_proyectos_ok(self, mock_render, mock_is_admin, mock_proyectos):
        """Debe renderizar la lista de proyectos"""
        from django.test import RequestFactory
        request = RequestFactory().get('/proyectos/')
        request.user = MagicMock(is_authenticated=True)
        request.GET = {}
        
        mock_is_admin.return_value = False
        mock_proyectos.all.return_value.order_by.return_value = []
        
        from social_projects.views import lista_proyectos
        lista_proyectos(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "lista.html")

    @patch("social_projects.views.ProyectosSociales.objects")
    @patch("social_projects.views.is_admin")
    @patch("social_projects.views.render")
    def test_lista_proyectos_search(self, mock_render, mock_is_admin, mock_proyectos):
        """Debe filtrar proyectos por búsqueda"""
        from django.test import RequestFactory
        request = RequestFactory().get('/proyectos/?q=Cali')
        request.user = MagicMock(is_authenticated=True)
        request.GET = {"q": "Cali"}
        
        mock_is_admin.return_value = False
        mock_qs = MagicMock()
        mock_proyectos.all.return_value.order_by.return_value = mock_qs
        mock_qs.filter.return_value = []
        
        from social_projects.views import lista_proyectos
        lista_proyectos(request)
        
        mock_qs.filter.assert_called_once()

    @patch("social_projects.views.messages")
    @patch("social_projects.views.redirect")
    @patch("social_projects.views.is_admin")
    def test_crear_proyecto_requires_admin(self, mock_is_admin, mock_redirect, mock_messages):
        """Debe rechazar usuarios no admin"""
        from django.test import RequestFactory
        request = RequestFactory().post('/proyectos/crear/')
        request.user = MagicMock(is_authenticated=True, is_staff=False)
        
        mock_is_admin.return_value = False
        
        from social_projects.views import crear_proyecto_social
        crear_proyecto_social(request)
        
        mock_messages.error.assert_called_once()
        mock_redirect.assert_called_once()

    @patch("social_projects.views.ProyectosSociales.objects")
    @patch("social_projects.views.messages")
    @patch("social_projects.views.redirect")
    @patch("social_projects.views._current_participante")
    @patch("social_projects.views.is_admin")
    @patch("social_projects.views._parse_date")
    @patch("social_projects.views.transaction")
    def test_crear_proyecto_admin_ok(self, mock_transaction, mock_parse_date, mock_is_admin, 
                                  mock_current_part, mock_redirect, mock_messages, mock_proyectos):
        """Debe permitir crear proyecto si es admin"""
        from django.test import RequestFactory
        from unittest.mock import Mock
    
        request = RequestFactory().post('/proyectos/crear/', {
        'nombre': 'Nuevo Proy',
        'descripcion': 'desc',
        'aforo': '50',
        'fecha_inicio': '2025-10-10',
        'fecha_fin': '2025-10-20',
        })
        request.user = MagicMock(is_authenticated=True, is_staff=True)
        request.POST = {
        'nombre': 'Nuevo Proy',
        'descripcion': 'desc',
        'aforo': '50',
        'fecha_inicio': '2025-10-10',
        'fecha_fin': '2025-10-20',
        }
    
        mock_is_admin.return_value = True
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_current_part.return_value = mock_participante
    
        # Mock para fechas válidas que no causen problemas de validación
        fecha_inicio_mock = MagicMock()
        fecha_fin_mock = MagicMock()
        # Asegurar que fecha_inicio < fecha_fin en la comparación
        fecha_inicio_mock.__gt__ = Mock(return_value=False)
        mock_parse_date.side_effect = [fecha_inicio_mock, fecha_fin_mock]
    
        # Mock transaction.atomic como context manager
        mock_transaction.atomic.return_value.__enter__ = Mock(return_value=None)
        mock_transaction.atomic.return_value.__exit__ = Mock(return_value=None)
    
        from social_projects.views import crear_proyecto_social
        crear_proyecto_social(request)
    
        mock_proyectos.create.assert_called_once()
        mock_messages.success.assert_called_once()

    @patch("social_projects.views.get_object_or_404")
    @patch("social_projects.views.InscripcionesPsu.objects")
    @patch("social_projects.views._current_participante")
    @patch("social_projects.views.render")
    def test_detalle_proyecto_ok(self, mock_render, mock_current_part, 
                                   mock_inscripciones, mock_get):
        """Debe renderizar detalle del proyecto"""
        from django.test import RequestFactory
        request = RequestFactory().get('/proyectos/1/')
        request.user = MagicMock(is_authenticated=True, is_staff=False, is_superuser=False)
        
        mock_proyecto = MagicMock()
        mock_proyecto.aforo = 2
        mock_get.return_value = mock_proyecto
        
        mock_participante = MagicMock()
        mock_current_part.return_value = mock_participante
        
        mock_inscripciones.filter.return_value.count.return_value = 0
        mock_inscripciones.filter.return_value.exists.return_value = False
        
        from social_projects.views import detalle_proyecto
        detalle_proyecto(request, 1)
        
        mock_render.assert_called_once()

    @patch("social_projects.views.logger")
    @patch("social_projects.views.transaction")
    @patch("social_projects.views.get_object_or_404")
    @patch("social_projects.views.InscripcionesPsu.objects")
    @patch("social_projects.views.EstadosParticipacion.objects")
    @patch("social_projects.views._current_participante")
    @patch("social_projects.views.messages")
    @patch("social_projects.views.redirect")
    @patch("social_projects.views.ProyectosSociales.objects")
    @patch("social_projects.views.timezone")
    def test_inscribirse_psu_ok(self, mock_tz, mock_proy_objects, mock_redirect, mock_messages,
                                  mock_current_part, mock_estados, mock_inscripciones, 
                                  mock_get, mock_transaction, mock_logger):
        """Debe permitir inscripción exitosa"""
        from django.test import RequestFactory
        request = RequestFactory().post('/proyectos/1/inscribirse/')
        request.user = MagicMock(id=1, is_authenticated=True)
        request.method = 'POST'
        
        mock_proyecto = MagicMock()
        mock_proyecto.pk = 1
        mock_proyecto.aforo = 2
        mock_get.return_value = mock_proyecto
        
        mock_participante = MagicMock()
        mock_current_part.return_value = mock_participante
        
        # No existe inscripción previa
        mock_inscripciones.filter.return_value.exists.return_value = False
        # Aforo disponible
        mock_inscripciones.filter.return_value.count.return_value = 0
        
        # Mock transaction.atomic como context manager
        mock_transaction.atomic.return_value.__enter__ = Mock(return_value=None)
        mock_transaction.atomic.return_value.__exit__ = Mock(return_value=None)
        
        # Mock del select_for_update
        mock_proy_objects.select_for_update.return_value.get.return_value = mock_proyecto
        
        # Mock del estado
        mock_estado = MagicMock()
        mock_estados.filter.return_value.order_by.return_value.first.return_value = mock_estado
        
        from social_projects.views import inscribirse_psu
        inscribirse_psu(request, 1)
        
        mock_inscripciones.create.assert_called_once()
        # Verificar que se llamó success (ignorando info)
        success_calls = [call for call in mock_messages.success.call_args_list]
        self.assertEqual(len(success_calls), 1)

    @patch("social_projects.views.logger")
    @patch("social_projects.views.Participantes.objects")
    @patch("social_projects.views.send_mail")
    @patch("social_projects.views.get_object_or_404")
    @patch("social_projects.views.messages")
    @patch("social_projects.views.redirect")
    def test_consultar_duda_post_ok(self, mock_redirect, mock_messages, 
                                      mock_get, mock_send_mail, mock_participantes, mock_logger):
        """Debe permitir enviar una duda válida al coordinador"""
        from django.test import RequestFactory
        request = RequestFactory().post('/proyectos/1/consultar/', {
            'mensaje': '¿Cuándo inicia el proyecto?'
        })
        request.user = MagicMock(id=1, is_authenticated=True)
        request.method = 'POST'
        request.POST = {'mensaje': '¿Cuándo inicia el proyecto?'}
        
        mock_proyecto = MagicMock()
        mock_proyecto.nombre = "Paseo por Cali"
        mock_proyecto.coordinador_id = 1
        
        mock_participante = MagicMock()
        mock_participante.nombre = "Alice"
        mock_participante.apellido = "Test"
        mock_participante.correo = "alice@test.com"
        
        mock_coordinador = MagicMock()
        mock_coordinador.correo = "coord@test.com"
        
        # get_object_or_404 para proyecto y participante
        mock_get.side_effect = [mock_proyecto, mock_participante]
        
        # Participantes.objects.get para coordinador
        mock_participantes.get.return_value = mock_coordinador
        
        from social_projects.views import consultar_duda
        consultar_duda(request, 1)
        
        mock_send_mail.assert_called_once()
        call_kwargs = mock_send_mail.call_args[1]
        self.assertIn("¿Cuándo inicia el proyecto?", call_kwargs["message"])

    @patch("social_projects.views.Participantes.objects")
    @patch("social_projects.views.get_object_or_404")
    @patch("social_projects.views.render")
    def test_consultar_duda_get_ok(self, mock_render, mock_get, mock_participantes):
        """Debe renderizar la página de consulta"""
        from django.test import RequestFactory
        request = RequestFactory().get('/proyectos/1/consultar/')
        request.user = MagicMock(id=1, is_authenticated=True)
        request.method = 'GET'
        
        mock_proyecto = MagicMock()
        mock_proyecto.nombre = "Paseo por Cali"
        mock_proyecto.coordinador_id = 1
        
        mock_participante = MagicMock()
        mock_coordinador = MagicMock()
        
        mock_get.side_effect = [mock_proyecto, mock_participante]
        mock_participantes.get.return_value = mock_coordinador
        
        from social_projects.views import consultar_duda
        consultar_duda(request, 1)
        
        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        self.assertIn("proyecto", context)

    @patch("social_projects.views.Participantes.objects")
    @patch("social_projects.views.get_object_or_404")
    @patch("social_projects.views.messages")
    @patch("social_projects.views.render")
    def test_consultar_duda_post_empty_message(self, mock_render, mock_messages, 
                                                 mock_get, mock_participantes):
        """Debe mostrar error si el mensaje está vacío"""
        from django.test import RequestFactory
        request = RequestFactory().post('/proyectos/1/consultar/', {
            'mensaje': '   '
        })
        request.user = MagicMock(id=1, is_authenticated=True)
        request.method = 'POST'
        request.POST = {'mensaje': '   '}
        
        mock_proyecto = MagicMock()
        mock_participante = MagicMock()
        mock_coordinador = MagicMock()
        
        mock_get.side_effect = [mock_proyecto, mock_participante]
        mock_participantes.get.return_value = mock_coordinador
        
        from social_projects.views import consultar_duda
        consultar_duda(request, 1)
        
        mock_messages.error.assert_called_once()

    @patch("social_projects.views.Participantes.objects")
    @patch("social_projects.views.get_object_or_404")
    @patch("social_projects.views.messages")
    @patch("social_projects.views.redirect")
    def test_consultar_duda_sin_coordinador(self, mock_redirect, mock_messages, 
                                              mock_get, mock_participantes):
        """Debe manejar el caso de proyecto sin coordinador"""
        from django.test import RequestFactory
        from universitaryWellbeing.models import Participantes
        
        request = RequestFactory().post('/proyectos/1/consultar/', {
            'mensaje': '¿Hay cupos?'
        })
        request.user = MagicMock(id=1, is_authenticated=True)
        request.method = 'POST'
        request.POST = {'mensaje': '¿Hay cupos?'}
        
        mock_proyecto = MagicMock()
        mock_proyecto.coordinador_id = 999  # ID que no existe
        
        mock_participante = MagicMock()
        
        mock_get.side_effect = [mock_proyecto, mock_participante]
        
        # Simular DoesNotExist para coordinador
        mock_participantes.get.side_effect = Participantes.DoesNotExist()
        
        from social_projects.views import consultar_duda
        consultar_duda(request, 1)
        
        mock_messages.error.assert_called()

    @patch("social_projects.views.logger")
    @patch("social_projects.views.get_object_or_404")
    @patch("social_projects.views.InscripcionesPsu.objects")
    @patch("social_projects.views._current_participante")
    @patch("social_projects.views.messages")
    @patch("social_projects.views.redirect")
    def test_inscribirse_psu_no_duplicate(self, mock_redirect, mock_messages,
                                            mock_current_part, mock_inscripciones, 
                                            mock_get, mock_logger):
        """Debe informar si ya está inscrito"""
        from django.test import RequestFactory
        request = RequestFactory().post('/proyectos/1/inscribirse/')
        request.user = MagicMock(id=1, is_authenticated=True)
        request.method = 'POST'
        
        mock_proyecto = MagicMock()
        mock_get.return_value = mock_proyecto
        
        mock_participante = MagicMock()
        mock_current_part.return_value = mock_participante
        
        # Ya existe inscripción
        mock_inscripciones.filter.return_value.exists.return_value = True
        
        from social_projects.views import inscribirse_psu
        inscribirse_psu(request, 1)
        
        # Debe llamar messages.info al menos una vez con el mensaje de "Ya estaba inscrito"
        info_calls = [str(call) for call in mock_messages.info.call_args_list]
        inscrito_call = any("Ya estaba inscrito" in str(call) for call in info_calls)
        self.assertTrue(inscrito_call)
        
        # No debe intentar crear nueva inscripción
        mock_inscripciones.create.assert_not_called()

    @patch("social_projects.views.logger")
    @patch("social_projects.views.transaction")
    @patch("social_projects.views.get_object_or_404")
    @patch("social_projects.views.InscripcionesPsu.objects")
    @patch("social_projects.views._current_participante")
    @patch("social_projects.views.messages")
    @patch("social_projects.views.redirect")
    @patch("social_projects.views.ProyectosSociales.objects")
    def test_inscribirse_psu_aforo_lleno(self, mock_proy_objects, mock_redirect,
                                          mock_messages, mock_current_part,
                                          mock_inscripciones, mock_get, 
                                          mock_transaction, mock_logger):
        """Debe rechazar inscripción si aforo está lleno"""
        from django.test import RequestFactory
        request = RequestFactory().post('/proyectos/1/inscribirse/')
        request.user = MagicMock(id=1, is_authenticated=True)
        request.method = 'POST'
        
        mock_proyecto = MagicMock()
        mock_proyecto.pk = 1
        mock_proyecto.aforo = 2
        mock_get.return_value = mock_proyecto
        
        mock_participante = MagicMock()
        mock_current_part.return_value = mock_participante
        
        # No existe inscripción previa
        mock_inscripciones.filter.return_value.exists.return_value = False
        # Aforo lleno (2 inscritos de 2)
        mock_inscripciones.filter.return_value.count.return_value = 2
        
        # Mock transaction.atomic
        mock_transaction.atomic.return_value.__enter__ = Mock(return_value=None)
        mock_transaction.atomic.return_value.__exit__ = Mock(return_value=None)
        
        # Mock del select_for_update
        mock_proy_objects.select_for_update.return_value.get.return_value = mock_proyecto
        
        from social_projects.views import inscribirse_psu
        inscribirse_psu(request, 1)
        
        # Verificar que se llamó error con mensaje de aforo
        error_calls = [str(call) for call in mock_messages.error.call_args_list]
        aforo_call = any("Aforo lleno" in str(call) or "lleno" in str(call).lower() for call in error_calls)
        self.assertTrue(aforo_call, "Debe mostrar mensaje de aforo lleno")
        
        # No debe crear inscripción
        mock_inscripciones.create.assert_not_called()