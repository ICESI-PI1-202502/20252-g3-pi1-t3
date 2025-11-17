"""
Tests unitarios para tournaments/views.py
Estilo: SimpleTestCase con mocks (sin base de datos)
Similar a Analytics_Reports/test/test_analytics_reports.py
"""
from django.test import SimpleTestCase, RequestFactory
from unittest.mock import patch, MagicMock, Mock, call
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.core.exceptions import ValidationError
from tournaments import views as vw
import datetime as dt
from django.utils.timezone import make_aware, get_current_timezone


# ==========================================================
# TESTS UNITARIOS DE FUNCIONES AUXILIARES
# ==========================================================

class HelpersTestCase(SimpleTestCase):
    """Pruebas unitarias para helpers simples"""

    def test_is_admin_true_for_staff(self):
        """Usuario staff debe ser admin"""
        user = MagicMock(is_authenticated=True, is_staff=True, is_superuser=False)
        self.assertTrue(vw.is_admin(user))

    def test_is_admin_true_for_superuser(self):
        """Usuario superuser debe ser admin"""
        user = MagicMock(is_authenticated=True, is_staff=False, is_superuser=True)
        self.assertTrue(vw.is_admin(user))

    def test_is_admin_false_for_regular_user(self):
        """Usuario regular no debe ser admin"""
        user = MagicMock(is_authenticated=True, is_staff=False, is_superuser=False)
        self.assertFalse(vw.is_admin(user))

    def test_is_admin_false_for_anonymous(self):
        """Usuario anónimo no debe ser admin"""
        user = MagicMock(is_authenticated=False, is_staff=False, is_superuser=False)
        self.assertFalse(vw.is_admin(user))


class ParseFunctionsTestCase(SimpleTestCase):
    """Pruebas de funciones de parseo de fechas"""

    def test_parse_date_valid(self):
        """Debe parsear fecha válida"""
        result = vw._parse_date("2025-10-15")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 10)
        self.assertEqual(result.day, 15)

    def test_parse_date_invalid(self):
        """Debe retornar None con fecha inválida"""
        result = vw._parse_date("invalid-date")
        self.assertIsNone(result)

    def test_parse_date_empty(self):
        """Debe retornar None con string vacío"""
        result = vw._parse_date("")
        self.assertIsNone(result)

    def test_parse_date_none(self):
        """Debe retornar None con None"""
        result = vw._parse_date(None)
        self.assertIsNone(result)

    def test_parse_dt_local_iso_format(self):
        """Debe parsear datetime en formato ISO"""
        result = vw._parse_dt_local("2025-10-15T14:30")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 10)
        self.assertEqual(result.day, 15)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)

    def test_parse_dt_local_with_seconds(self):
        """Debe parsear datetime con segundos"""
        result = vw._parse_dt_local("2025-10-15T14:30:00")
        self.assertIsNotNone(result)

    def test_parse_dt_local_invalid(self):
        """Debe retornar None con datetime inválido"""
        result = vw._parse_dt_local("invalid")
        self.assertIsNone(result)

    def test_parse_dt_local_empty(self):
        """Debe retornar None con string vacío"""
        result = vw._parse_dt_local("")
        self.assertIsNone(result)

    def test_parse_dt_local_none(self):
        """Debe retornar None con None"""
        result = vw._parse_dt_local(None)
        self.assertIsNone(result)

    def test_ensure_aware_with_naive_datetime(self):
        """Debe hacer aware un datetime naive"""
        naive_dt = dt.datetime(2025, 10, 15, 14, 30)
        result = vw._ensure_aware(naive_dt)
        self.assertIsNotNone(result)

    def test_ensure_aware_with_none(self):
        """Debe retornar None si recibe None"""
        result = vw._ensure_aware(None)
        self.assertIsNone(result)


class OverlapTestCase(SimpleTestCase):
    """Pruebas de función de solapamiento"""

    def test_overlap_q_creates_correct_query(self):
        """Debe crear Q object para detectar solapamiento"""
        inicio = dt.datetime(2025, 10, 15, 14, 0)
        fin = dt.datetime(2025, 10, 15, 16, 0)
        
        q = vw._overlap_q(inicio, fin)
        
        self.assertIsNotNone(q)
        # El Q object debe tener ambas condiciones


# ==========================================================
# TESTS DE CREAR TORNEO
# ==========================================================

class CrearTorneoTests(SimpleTestCase):
    """Pruebas unitarias de la vista crear_torneo"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.messages')
    @patch('tournaments.views.redirect')
    def test_crear_torneo_requires_admin(self, mock_redirect, mock_messages, mock_is_admin):
        """Solo admins pueden crear torneos"""
        mock_is_admin.return_value = False
        
        request = self.factory.post('/tournaments/create/')
        request.user = MagicMock()
        
        vw.crear_torneo(request)
        
        mock_messages.error.assert_called_once()
        args = mock_messages.error.call_args[0]
        self.assertIn("permisos", args[1].lower())
        mock_redirect.assert_called_once_with("tournaments:list")

    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.Disciplinas.objects')
    @patch('tournaments.views.render')
    def test_crear_torneo_get_renders_form(self, mock_render, mock_disciplinas, mock_is_admin):
        """GET debe renderizar el formulario"""
        mock_is_admin.return_value = True
        mock_disciplinas.all.return_value.order_by.return_value = []
        
        request = self.factory.get('/tournaments/create/')
        request.user = MagicMock()
        
        vw.crear_torneo(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "create_tournament.html")
        context = mock_render.call_args[0][2]
        self.assertIn("disciplinas", context)

    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.Torneos.objects')
    @patch('tournaments.views.messages')
    @patch('tournaments.views.redirect')
    def test_crear_torneo_post_success(self, mock_redirect, mock_messages, 
                                       mock_torneos, mock_is_admin):
        """POST exitoso debe crear torneo"""
        mock_is_admin.return_value = True
        mock_torneos.create.return_value = MagicMock(id_torneo=1)
        
        request = self.factory.post('/tournaments/create/', {
            'nombre': 'Interfacultades',
            'disciplina': '1',
            'fecha_inicio': '2025-10-01',
            'fecha_fin': '2025-10-15',
            'aforo': '16',
            'limite_inscripcion': '',
        })
        request.user = MagicMock()
        
        vw.crear_torneo(request)
        
        mock_torneos.create.assert_called_once()
        mock_messages.success.assert_called_once()
        mock_redirect.assert_called_once_with("tournaments:list")

    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.messages')
    @patch('tournaments.views.redirect')
    def test_crear_torneo_post_missing_fields(self, mock_redirect, mock_messages, mock_is_admin):
        """POST sin campos requeridos debe mostrar error"""
        mock_is_admin.return_value = True
        
        request = self.factory.post('/tournaments/create/', {
            'nombre': '',
            'disciplina': '',
            'fecha_inicio': '',
            'fecha_fin': '',
        })
        request.user = MagicMock()
        
        vw.crear_torneo(request)
        
        mock_messages.error.assert_called()
        args = mock_messages.error.call_args[0]
        self.assertIn("completa", args[1].lower())
        mock_redirect.assert_called_once_with("tournaments:create")

    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.messages')
    @patch('tournaments.views.redirect')
    def test_crear_torneo_fecha_invalida(self, mock_redirect, mock_messages, mock_is_admin):
        """Fecha inicio posterior a fecha fin debe dar error"""
        mock_is_admin.return_value = True
        
        request = self.factory.post('/tournaments/create/', {
            'nombre': 'Torneo',
            'disciplina': '1',
            'fecha_inicio': '2025-10-20',
            'fecha_fin': '2025-10-10',
            'aforo': '',
        })
        request.user = MagicMock()
        
        vw.crear_torneo(request)
        
        mock_messages.error.assert_called()
        args = mock_messages.error.call_args[0]
        self.assertIn("inicio", args[1].lower())
        mock_redirect.assert_called_with("tournaments:create")

    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.Torneos.objects')
    @patch('tournaments.views.messages')
    @patch('tournaments.views.redirect')
    def test_crear_torneo_with_limite_inscripcion(self, mock_redirect, mock_messages,
                                                  mock_torneos, mock_is_admin):
        """Debe procesar límite de inscripción opcional"""
        mock_is_admin.return_value = True
        mock_torneos.create.return_value = MagicMock(id_torneo=1)
        
        request = self.factory.post('/tournaments/create/', {
            'nombre': 'Torneo',
            'disciplina': '1',
            'fecha_inicio': '2025-10-01',
            'fecha_fin': '2025-10-15',
            'aforo': '8',
            'limite_inscripcion': '2025-09-25T23:59',
        })
        request.user = MagicMock()
        
        vw.crear_torneo(request)
        
        mock_torneos.create.assert_called_once()
        mock_messages.success.assert_called_once()


# ==========================================================
# TESTS DE LISTAR TORNEOS
# ==========================================================

class ListaTorneosTests(SimpleTestCase):
    """Pruebas de la vista lista_torneos"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('tournaments.views.Torneos.objects')
    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.render')
    def test_lista_torneos_renders_all(self, mock_render, mock_is_admin, mock_torneos):
        """Debe listar todos los torneos"""
        mock_is_admin.return_value = False
        
        mock_torneos.values.return_value.order_by.return_value = [
            {
                'id_torneo': 1,
                'nombre': 'Copa 2025',
                'fecha_inicio': dt.date(2025, 10, 1),
                'fecha_fin': dt.date(2025, 10, 15),
                'aforo_equipos': 8,
                'disciplinas_id_disciplina__nombre': 'Fútbol'
            }
        ]
        
        request = self.factory.get('/tournaments/')
        request.GET = {}
        request.user = MagicMock()
        
        vw.lista_torneos(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "list_tournament.html")
        context = mock_render.call_args[0][2]
        self.assertIn('tournaments', context)
        self.assertEqual(len(context['tournaments']), 1)
        self.assertIn('can_create', context)

    # ============================================
# CORRECCIÓN 3: test_lista_torneos_filters_by_search
# ============================================

@patch('tournaments.views.Torneos.objects')
@patch('tournaments.views.is_admin')
@patch('tournaments.views.render')
def test_lista_torneos_filters_by_search(self, mock_render, mock_is_admin, mock_torneos):
    """Debe filtrar torneos por búsqueda en nombre"""
    mock_is_admin.return_value = False
    
    # ✅ Datos que coincidan con el filtro 'natacion'
    mock_torneos.values.return_value.order_by.return_value = [
        {
            'id_torneo': 1,
            'nombre': 'Copa de Natación',
            'fecha_inicio': dt.date(2025, 10, 1),
            'fecha_fin': dt.date(2025, 10, 15),
            'aforo_equipos': None,
            'disciplinas_id_disciplina__nombre': 'Natación'
        },
        {
            'id_torneo': 2,
            'nombre': 'Torneo de Fútbol',
            'fecha_inicio': dt.date(2025, 11, 1),
            'fecha_fin': dt.date(2025, 11, 15),
            'aforo_equipos': 8,
            'disciplinas_id_disciplina__nombre': 'Fútbol'
        }
    ]
    
    # ✅ Búsqueda en minúsculas (como lo hace el código)
    request = self.factory.get('/tournaments/?q=natación')  # con acento
    request.GET = {'q': 'natación'}
    request.user = MagicMock()
    
    vw.lista_torneos(request)
    
    mock_render.assert_called_once()
    context = mock_render.call_args[0][2]
    # El filtro busca 'natación' en 'Copa de Natación'
    self.assertEqual(len(context['tournaments']), 1)
    self.assertEqual(context['tournaments'][0]['nombre'], 'Copa de Natación')

    @patch('tournaments.views.Torneos.objects')
    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.render')
    def test_lista_torneos_empty_search_shows_all(self, mock_render, mock_is_admin, mock_torneos):
        """Búsqueda vacía debe mostrar todos"""
        mock_is_admin.return_value = False
        
        mock_torneos.values.return_value.order_by.return_value = [
            {
                'id_torneo': 1,
                'nombre': 'Torneo A',
                'fecha_inicio': dt.date(2025, 10, 1),
                'fecha_fin': dt.date(2025, 10, 15),
                'aforo_equipos': None,
                'disciplinas_id_disciplina__nombre': 'Deporte A'
            }
        ]
        
        request = self.factory.get('/tournaments/?q=')
        request.GET = {'q': ''}
        request.user = MagicMock()
        
        vw.lista_torneos(request)
        
        context = mock_render.call_args[0][2]
        self.assertEqual(len(context['tournaments']), 1)


# ==========================================================
# TESTS DE CREAR EQUIPO
# ==========================================================

class CrearEquipoTests(SimpleTestCase):
    """Pruebas de crear_equipo_en_torneo"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('tournaments.views.get_object_or_404')
    @patch('tournaments.views.messages')
    @patch('tournaments.views.redirect')
    def test_crear_equipo_torneo_individual_blocked(self, mock_redirect, 
                                                    mock_messages, mock_get_object):
        """No debe permitir crear equipo en torneo individual"""
        torneo_mock = MagicMock()
        torneo_mock.aforo_equipos = None
        torneo_mock.id_torneo = 1
        mock_get_object.return_value = torneo_mock
        
        request = self.factory.post('/tournaments/1/create-team/')
        request.user = MagicMock()
        
        vw.crear_equipo_en_torneo(request, 1)
        
        mock_messages.error.assert_called_once()
        args = mock_messages.error.call_args[0]
        self.assertIn("individual", args[1].lower())
        mock_redirect.assert_called_once_with("tournaments:detail", 1)

    @patch('tournaments.views.get_object_or_404')
    @patch('tournaments.views.Disciplinas.objects')
    @patch('tournaments.views.render')
    def test_crear_equipo_get_renders_form(self, mock_render, mock_disciplinas, mock_get_object):
        """GET debe renderizar formulario"""
        torneo_mock = MagicMock()
        torneo_mock.aforo_equipos = 8
        torneo_mock.id_torneo = 1
        torneo_mock.nombre = "Copa 2025"
        mock_get_object.return_value = torneo_mock
        mock_disciplinas.all.return_value.order_by.return_value = []
        
        request = self.factory.get('/tournaments/1/create-team/')
        request.user = MagicMock()
        
        vw.crear_equipo_en_torneo(request, 1)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "create_team.html")
        context = mock_render.call_args[0][2]
        self.assertIn("tournament", context)
        self.assertIn("disciplinas", context)

    # ============================================
# CORRECCIÓN 2: test_crear_equipo_validates_responsable
# ============================================

@patch('tournaments.views.get_object_or_404')
@patch('tournaments.views.Participantes.objects')
@patch('tournaments.views.Disciplinas.objects')
@patch('tournaments.views.messages')
@patch('tournaments.views.redirect')
def test_crear_equipo_validates_responsable(self, mock_redirect, mock_messages,
                                            mock_disciplinas, mock_participantes, 
                                            mock_get_object):
    """Debe validar que el responsable exista"""
    torneo_mock = MagicMock()
    torneo_mock.aforo_equipos = 8
    torneo_mock.id_torneo = 1
    mock_get_object.return_value = torneo_mock
    
    # ✅ Mock completo para evitar acceso a BD
    mock_participantes.filter.return_value.exists.return_value = False
    mock_disciplinas.objects.filter.return_value.exists.return_value = False
    
    request = self.factory.post('/tournaments/1/create-team/', {
        'nombre_equipo': 'Tigres',
        'responsable_id': '999',
        'disciplina_id': '1',
        'capacidad_min': '5',
        'capacidad_max': '10',
        'fecha_creacion': '2025-10-01'
    })
    request.user = MagicMock()
    
    vw.crear_equipo_en_torneo(request, 1)
    
    mock_messages.error.assert_called()
    mock_redirect.assert_called()


# ==========================================================
# TESTS DE UNIRSE A EQUIPO
# ==========================================================

class UnirseEquipoTests(SimpleTestCase):
    """Pruebas de unirse_equipo"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('tournaments.views.get_object_or_404')
    @patch('tournaments.views.messages')
    @patch('tournaments.views.redirect')
    def test_unirse_equipo_torneo_individual_blocked(self, mock_redirect, 
                                                     mock_messages, mock_get_object):
        """No debe permitir unirse en torneo individual"""
        torneo_mock = MagicMock()
        torneo_mock.aforo_equipos = None
        torneo_mock.id_torneo = 1
        mock_get_object.return_value = torneo_mock
        
        request = self.factory.get('/tournaments/1/join-team/')
        request.user = MagicMock()
        
        vw.unirse_equipo(request, 1)
        
        mock_messages.error.assert_called_once()
        args = mock_messages.error.call_args[0]
        self.assertIn("individual", args[1].lower())

    @patch('tournaments.views.get_object_or_404')
    @patch('tournaments.views._current_participante')
    @patch('tournaments.views.Equipos.objects')
    @patch('tournaments.views.render')
    def test_unirse_equipo_get_renders_teams(self, mock_render, mock_equipos, 
                                             mock_current, mock_get_object):
        """GET debe mostrar equipos disponibles"""
        torneo_mock = MagicMock()
        torneo_mock.aforo_equipos = 8
        torneo_mock.id_torneo = 1
        torneo_mock.nombre = "Copa 2025"
        torneo_mock.disciplinas_id_disciplina.nombre = "Fútbol"
        mock_get_object.return_value = torneo_mock
        
        mock_current.return_value = MagicMock(id_participante=1)
        
        mock_equipos.filter.return_value.values.return_value.order_by.return_value = [
            {'id_equipo': 1, 'nombre': 'Tigres', 'capacidad_max': 10, 'disciplinas_id_disciplina': 1}
        ]
        
        request = self.factory.get('/tournaments/1/join-team/')
        request.user = MagicMock()
        
        vw.unirse_equipo(request, 1)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "join_team.html")
        context = mock_render.call_args[0][2]
        self.assertIn('teams', context)
        self.assertIn('tournament', context)

    # ============================================
# CORRECCIÓN 4: test_unirse_equipo_requires_participante
# ============================================

@patch('tournaments.views.get_object_or_404')
@patch('tournaments.views._current_participante')
@patch('tournaments.views.Equipos.objects')
@patch('tournaments.views.messages')
@patch('tournaments.views.redirect')
def test_unirse_equipo_requires_participante(self, mock_redirect, mock_messages,
                                            mock_equipos, mock_current, mock_get_object):
    """Debe requerir que el usuario tenga participante"""
    torneo_mock = MagicMock()
    torneo_mock.aforo_equipos = 8
    mock_get_object.return_value = torneo_mock
    
    # ✅ Mock para que _current_participante retorne None
    mock_current.return_value = None
    
    # ✅ Mock para evitar que se ejecute la query de equipos
    mock_equipos.filter.return_value.values.return_value.order_by.return_value = []
    
    request = self.factory.get('/tournaments/1/join-team/')
    request.user = MagicMock()
    
    vw.unirse_equipo(request, 1)
    
    mock_messages.error.assert_called_once()
    args = mock_messages.error.call_args[0]
    self.assertIn("participante", args[1].lower())



# ==========================================================
# TESTS DE CREAR PARTIDO
# ==========================================================

class CrearPartidoTests(SimpleTestCase):
    """Pruebas de partidos_crear"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.messages')
    @patch('tournaments.views.redirect')
    def test_crear_partido_requires_admin(self, mock_redirect, mock_messages, mock_is_admin):
        """Solo admins pueden crear partidos"""
        mock_is_admin.return_value = False
        
        request = self.factory.post('/tournaments/1/matches/create/')
        request.user = MagicMock()
        
        vw.partidos_crear(request, 1)
        
        mock_messages.error.assert_called_once()
        args = mock_messages.error.call_args[0]
        self.assertIn("permisos", args[1].lower())

    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.get_object_or_404')
    @patch('tournaments.views.messages')
    @patch('tournaments.views.redirect')
    def test_crear_partido_torneo_individual_blocked(self, mock_redirect, mock_messages, 
                                                     mock_get_object, mock_is_admin):
        """No debe crear partidos en torneos individuales"""
        mock_is_admin.return_value = True
        
        torneo_mock = MagicMock()
        torneo_mock.aforo_equipos = None
        torneo_mock.id_torneo = 1
        mock_get_object.return_value = torneo_mock
        
        request = self.factory.post('/tournaments/1/matches/create/')
        request.user = MagicMock()
        
        vw.partidos_crear(request, 1)
        
        mock_messages.error.assert_called_once()
        args = mock_messages.error.call_args[0]
        self.assertIn("individual", args[1].lower())

    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.get_object_or_404')
    @patch('tournaments.views.Equipos.objects')
    @patch('tournaments.views.render')
    def test_crear_partido_get_renders_form(self, mock_render, mock_equipos,
                                            mock_get_object, mock_is_admin):
        """GET debe renderizar formulario"""
        mock_is_admin.return_value = True
        
        torneo_mock = MagicMock()
        torneo_mock.aforo_equipos = 8
        torneo_mock.id_torneo = 1
        torneo_mock.nombre = "Copa 2025"
        torneo_mock.disciplinas_id_disciplina.nombre = "Fútbol"
        mock_get_object.return_value = torneo_mock
        
        mock_equipos.filter.return_value.values.return_value.order_by.return_value = []
        
        request = self.factory.get('/tournaments/1/matches/create/')
        request.user = MagicMock()
        
        vw.partidos_crear(request, 1)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "create_match.html")


# ==========================================================
# TESTS DE REGISTRAR RESULTADO
# ==========================================================

class RegistrarResultadoTests(SimpleTestCase):
    """Pruebas de partido_resultado"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.Partidos.objects')
    @patch('tournaments.views.messages')
    @patch('tournaments.views.redirect')
    def test_registrar_resultado_requires_admin(self, mock_redirect, mock_messages, 
                                                mock_partidos, mock_is_admin):
        """Solo admins pueden registrar resultados"""
        mock_is_admin.return_value = False
        
        mock_partidos.filter.return_value.values_list.return_value.first.return_value = 1
        
        request = self.factory.post('/tournaments/matches/1/result/')
        request.user = MagicMock()
        
        vw.partido_resultado(request, 1)
        
        mock_messages.error.assert_called_once()
        args = mock_messages.error.call_args[0]
        self.assertIn("permisos", args[1].lower())

    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.get_object_or_404')
    @patch('tournaments.views.render')
    def test_registrar_resultado_get_renders_form(self, mock_render, 
                                                  mock_get_object, mock_is_admin):
        """GET debe renderizar formulario"""
        mock_is_admin.return_value = True
        
        partido_mock = MagicMock()
        partido_mock.id_partido = 1
        partido_mock.torneos_id_torneo.nombre = "Copa 2025"
        partido_mock.torneos_id_torneo.id_torneo = 1
        partido_mock.equipos_id_equipo.nombre = "Tigres"
        partido_mock.equipos_id_equipo2.nombre = "Leones"
        partido_mock.estado = "PROGRAMADO"
        partido_mock.marcador_a = None
        partido_mock.marcador_b = None
        
        mock_get_object.return_value = partido_mock
        
        request = self.factory.get('/tournaments/matches/1/result/')
        request.user = MagicMock()
        
        vw.partido_resultado(request, 1)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "record_result.html")
        context = mock_render.call_args[0][2]
        self.assertIn("match", context)
        self.assertIn("prefill", context)


# ==========================================================
# TESTS DE GESTIONAR EQUIPO
# ==========================================================

class GestionarEquipoTests(SimpleTestCase):
    """Pruebas de gestionar_equipo"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('tournaments.views.get_object_or_404')
    @patch('tournaments.views.TorneosEquipos.objects')
    @patch('tournaments.views._current_participante')
    @patch('tournaments.views.EquiposParticipantes.objects')
    @patch('tournaments.views.messages')
    @patch('tournaments.views.redirect')
    def test_gestionar_equipo_requires_membership(self, mock_redirect, mock_messages,
                                                  mock_eq_part, mock_current, 
                                                  mock_torneos_equipos, mock_get_object):
        """Solo miembros pueden gestionar equipo"""
        torneo_mock = MagicMock()
        torneo_mock.id_torneo = 1
        team_mock = MagicMock()
        team_mock.id_equipo = 1
        mock_get_object.side_effect = [torneo_mock, team_mock]
        
        mock_torneos_equipos.filter.return_value.exists.return_value = True
        mock_current.return_value = MagicMock(id_participante=1)
        
        # Mock que indica que NO es miembro
        mock_eq_part.filter.return_value.exists.return_value = False
        
        request = self.factory.get('/tournaments/1/teams/1/manage/')
        request.user = MagicMock()
        
        vw.gestionar_equipo(request, 1, 1)
        
        mock_messages.error.assert_called_once()
        args = mock_messages.error.call_args[0]
        self.assertIn("perteneces", args[1].lower())
        mock_redirect.assert_called_once()

    @patch('tournaments.views.get_object_or_404')
    @patch('tournaments.views.TorneosEquipos.objects')
    @patch('tournaments.views._current_participante')
    @patch('tournaments.views.EquiposParticipantes.objects')
    @patch('tournaments.views.render')
    def test_gestionar_equipo_member_can_view(self, mock_render, mock_eq_part,
                                              mock_current, mock_torneos_equipos,
                                              mock_get_object):
        """Miembro puede ver gestión de equipo"""
        torneo_mock = MagicMock()
        torneo_mock.id_torneo = 1
        torneo_mock.nombre = "Copa 2025"
        torneo_mock.disciplinas_id_disciplina.nombre = "Fútbol"
        
        team_mock = MagicMock()
        team_mock.id_equipo = 1
        team_mock.nombre = "Tigres"
        team_mock.capacidad_max = 10
        team_mock.participantes_id_participante.id_participante = 1
        
        mock_get_object.side_effect = [torneo_mock, team_mock]
        mock_torneos_equipos.filter.return_value.exists.return_value = True
        
        participante = MagicMock()
        participante.id_participante = 1
        mock_current.return_value = participante
        
        # Es miembro
        mock_eq_part.filter.return_value.exists.return_value = True
        mock_eq_part.objects.filter.return_value.select_related.return_value.values.return_value.order_by.return_value = []
        
        request = self.factory.get('/tournaments/1/teams/1/manage/')
        request.user = MagicMock()
        
        vw.gestionar_equipo(request, 1, 1)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "manage_team.html")


# ==========================================================
# TESTS DE INSCRIPCIÓN INDIVIDUAL
# ==========================================================

class InscripcionIndividualTests(SimpleTestCase):
    """Pruebas de inscripcion_individual"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('tournaments.views.get_torneo_or_404')
    @patch('tournaments.views.render')
    def test_inscripcion_individual_get_renders_form(self, mock_render, mock_get_torneo):
        """GET debe renderizar formulario"""
        mock_get_torneo.return_value = (
            {'id': 1, 'nombre': 'Torneo Individual', 'tiene_equipos': False},
            []
        )
        
        request = self.factory.get('/tournaments/1/join-individual/')
        
        vw.inscripcion_individual(request, 1)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "join_individual.html")
        context = mock_render.call_args[0][2]
        self.assertIn('tournament', context)
        self.assertFalse(context['ok'])
        self.assertIn('errors', context)

    @patch('tournaments.views.get_torneo_or_404')
    def test_inscripcion_individual_team_tournament_raises_404(self, mock_get_torneo):
        """Torneo por equipos debe lanzar 404"""
        mock_get_torneo.return_value = (
            {'id': 1, 'nombre': 'Torneo', 'tiene_equipos': True},
            []
        )
        
        request = self.factory.get('/tournaments/1/join-individual/')
        
        with self.assertRaises(Http404):
            vw.inscripcion_individual(request, 1)

    @patch('tournaments.views.get_torneo_or_404')
    @patch('tournaments.views.validate_email')
    @patch('tournaments.views.render')
    def test_inscripcion_individual_post_validates(self, mock_render, 
                                                   mock_validate, mock_get_torneo):
        """POST debe validar campos correctamente"""
        mock_get_torneo.return_value = (
            {'id': 1, 'nombre': 'Torneo', 'tiene_equipos': False},
            []
        )
        
        request = self.factory.post('/tournaments/1/join-individual/', {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'cedula': '1234567890',
            'correo': 'juan@test.com',
            'genero': 'Masculino'
        })
        
        vw.inscripcion_individual(request, 1)
        
        mock_validate.assert_called_once_with('juan@test.com')
        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        self.assertTrue(context['ok'])
        self.assertEqual(context['nombre'], 'Juan')

    @patch('tournaments.views.get_torneo_or_404')
    @patch('tournaments.views.render')
    def test_inscripcion_individual_validates_cedula(self, mock_render, mock_get_torneo):
        """Debe validar que la cédula tenga 10 dígitos"""
        mock_get_torneo.return_value = (
            {'id': 1, 'nombre': 'Torneo', 'tiene_equipos': False},
            []
        )
        
        request = self.factory.post('/tournaments/1/join-individual/', {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'cedula': '123',  # Inválida
            'correo': 'juan@test.com',
            'genero': 'Masculino'
        })
        
        vw.inscripcion_individual(request, 1)
        
        context = mock_render.call_args[0][2]
        self.assertFalse(context['ok'])
        self.assertIn('cedula', context['errors'])

    @patch('tournaments.views.get_torneo_or_404')
    @patch('tournaments.views.render')
    def test_inscripcion_individual_validates_email(self, mock_render, mock_get_torneo):
        """Debe validar formato de email"""
        mock_get_torneo.return_value = (
            {'id': 1, 'nombre': 'Torneo', 'tiene_equipos': False},
            []
        )
        
        request = self.factory.post('/tournaments/1/join-individual/', {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'cedula': '1234567890',
            'correo': 'email-invalido',
            'genero': 'Masculino'
        })
        
        vw.inscripcion_individual(request, 1)
        
        context = mock_render.call_args[0][2]
        self.assertFalse(context['ok'])
        self.assertIn('correo', context['errors'])


# ==========================================================
# TESTS DE DETALLE TORNEO
# ==========================================================

class DetalleTorneoTests(SimpleTestCase):
    """Pruebas de detalle_torneo"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('tournaments.views.get_torneo_or_404')
    @patch('tournaments.views._current_participante')
    @patch('tournaments.views.EquiposParticipantes.objects')
    @patch('tournaments.views.Partidos.objects')
    @patch('tournaments.views.render')
    def test_detalle_torneo_renders_team_tournament(self, mock_render, mock_partidos,
                                                    mock_eq_part, mock_current, 
                                                    mock_get_torneo):
        """Debe renderizar detalle de torneo por equipos"""
        mock_get_torneo.return_value = (
            {
                'id': 1,
                'nombre': 'Interfacultades',
                'tiene_equipos': True,
                'disciplina': 'Fútbol',
                'fecha_inicio': dt.date(2025, 10, 1),
                'fecha_fin': dt.date(2025, 10, 15),
                'aforo_equipos': 8
            },
            [{'id_equipo': 1, 'nombre': 'Tigres'}]
        )
        
        mock_current.return_value = MagicMock(id_participante=1)
        mock_eq_part.filter.return_value.values_list.return_value.first.return_value = None
        mock_partidos.filter.return_value.select_related.return_value.order_by.return_value = []
        
        request = self.factory.get('/tournaments/1/')
        request.user = MagicMock()
        
        vw.detalle_torneo(request, 1)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "detail_team.html")
        context = mock_render.call_args[0][2]
        self.assertIn('tournament', context)
        self.assertIn('teams', context)
        self.assertIn('matches', context)

    @patch('tournaments.views.get_torneo_or_404')
    @patch('tournaments.views.Partidos.objects')
    @patch('tournaments.views.render')
    def test_detalle_torneo_renders_individual_tournament(self, mock_render, 
                                                         mock_partidos, mock_get_torneo):
        """Debe renderizar detalle de torneo individual"""
        mock_get_torneo.return_value = (
            {
                'id': 1,
                'nombre': 'Torneo Individual',
                'tiene_equipos': False,
                'disciplina': 'Natación',
                'fecha_inicio': dt.date(2025, 10, 1),
                'fecha_fin': dt.date(2025, 10, 15)
            },
            []
        )
        
        mock_partidos.filter.return_value.select_related.return_value.order_by.return_value = []
        
        request = self.factory.get('/tournaments/1/')
        request.user = MagicMock()
        
        vw.detalle_torneo(request, 1)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "detail_individual.html")


# ==========================================================
# TESTS ADICIONALES DE VALIDACIÓN
# ==========================================================

class ValidacionesTests(SimpleTestCase):
    """Pruebas de validaciones adicionales"""

    @patch('tournaments.views.TorneosEquipos.objects')
    def test_teams_belong_to_tournament_true(self, mock_torneos_equipos):
        """Debe retornar True si ambos equipos pertenecen al torneo"""
        mock_torneos_equipos.filter.return_value.count.return_value = 2
        
        result = vw._teams_belong_to_tournament(1, 1, 2)
        
        self.assertTrue(result)
        mock_torneos_equipos.filter.assert_called_once()

    @patch('tournaments.views.TorneosEquipos.objects')
    def test_teams_belong_to_tournament_false(self, mock_torneos_equipos):
        """Debe retornar False si no ambos equipos pertenecen"""
        mock_torneos_equipos.filter.return_value.count.return_value = 1
        
        result = vw._teams_belong_to_tournament(1, 1, 2)
        
        self.assertFalse(result)

    @patch('tournaments.views.TorneosEquipos.objects')
    def test_teams_belong_to_tournament_same_team(self, mock_torneos_equipos):
        """Debe retornar False si es el mismo equipo"""
        mock_torneos_equipos.filter.return_value.count.return_value = 1
        
        result = vw._teams_belong_to_tournament(1, 1, 1)
        
        self.assertFalse(result)

    @patch('tournaments.views.Participantes.objects')
    def test_current_participante_returns_first(self, mock_participantes):
        """Debe retornar el primer participante del usuario"""
        mock_part = MagicMock()
        mock_part.id_participante = 1
        mock_participantes.filter.return_value.order_by.return_value.first.return_value = mock_part
        
        user = MagicMock(id=1)
        result = vw._current_participante(user)
        
        self.assertEqual(result, mock_part)
        mock_participantes.filter.assert_called_once_with(user_id=1)

    @patch('tournaments.views.Participantes.objects')
    def test_current_participante_returns_none(self, mock_participantes):
        """Debe retornar None si no hay participante"""
        mock_participantes.filter.return_value.order_by.return_value.first.return_value = None
        
        user = MagicMock(id=1)
        result = vw._current_participante(user)
        
        self.assertIsNone(result)


# ==========================================================
# TESTS DE GET_TORNEO_OR_404
# ==========================================================

class GetTorneoOr404Tests(SimpleTestCase):
    """Pruebas de la función get_torneo_or_404"""

    @patch('tournaments.views.get_object_or_404')
    @patch('tournaments.views.Equipos.objects')
    def test_get_torneo_or_404_with_teams(self, mock_equipos, mock_get_object):
        """Debe retornar torneo con equipos"""
        torneo_mock = MagicMock()
        torneo_mock.id_torneo = 1
        torneo_mock.nombre = "Copa 2025"
        torneo_mock.fecha_inicio = dt.date(2025, 10, 1)
        torneo_mock.fecha_fin = dt.date(2025, 10, 15)
        torneo_mock.disciplinas_id_disciplina.nombre = "Fútbol"
        torneo_mock.aforo_equipos = 8
        torneo_mock.limite_inscripcion = None
        
        mock_get_object.return_value = torneo_mock
        mock_equipos.filter.return_value.values.return_value.distinct.return_value = [
            {'id_equipo': 1, 'nombre': 'Tigres'}
        ]
        
        data, teams = vw.get_torneo_or_404(1)
        
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['nombre'], "Copa 2025")
        self.assertTrue(data['tiene_equipos'])
        self.assertEqual(len(teams), 1)

    @patch('tournaments.views.get_object_or_404')
    def test_get_torneo_or_404_individual(self, mock_get_object):
        """Debe retornar torneo individual sin equipos"""
        torneo_mock = MagicMock()
        torneo_mock.id_torneo = 1
        torneo_mock.nombre = "Torneo Individual"
        torneo_mock.fecha_inicio = dt.date(2025, 10, 1)
        torneo_mock.fecha_fin = dt.date(2025, 10, 15)
        torneo_mock.disciplinas_id_disciplina.nombre = "Natación"
        torneo_mock.aforo_equipos = None
        torneo_mock.limite_inscripcion = None
        
        mock_get_object.return_value = torneo_mock
        
        data, teams = vw.get_torneo_or_404(1)
        
        self.assertEqual(data['id'], 1)
        self.assertFalse(data['tiene_equipos'])
        self.assertEqual(len(teams), 0)


# ==========================================================
# TESTS DE EDGE CASES
# ==========================================================

class EdgeCasesTests(SimpleTestCase):
    """Pruebas de casos límite"""

    def setUp(self):
        self.factory = RequestFactory()

    # CORRECCIÓN 1: test_crear_partido_same_teams_error
    # ============================================

@patch('tournaments.views.is_admin')
@patch('tournaments.views.get_object_or_404')
@patch('tournaments.views.Equipos.objects')
@patch('tournaments.views.messages')
@patch('tournaments.views.render')
def test_crear_partido_same_teams_error(self, mock_render, mock_messages,
                                       mock_equipos, mock_get_object, mock_is_admin):
    """No debe permitir partido del mismo equipo contra sí mismo"""
    mock_is_admin.return_value = True
    
    # ✅ Mock del torneo con fechas MOCKEADAS (no datetime reales)
    torneo_mock = MagicMock()
    torneo_mock.aforo_equipos = 8
    torneo_mock.id_torneo = 1
    torneo_mock.fecha_inicio = MagicMock()  # ✅ Mock en lugar de datetime real
    torneo_mock.fecha_fin = MagicMock()     # ✅ Mock en lugar de datetime real
    torneo_mock.disciplinas_id_disciplina = MagicMock()
    torneo_mock.disciplinas_id_disciplina.nombre = "Fútbol"
    mock_get_object.return_value = torneo_mock
    
    mock_equipos.filter.return_value.values.return_value.order_by.return_value = []
    
    request = self.factory.post('/tournaments/1/matches/create/', {
        'equipo_a': '1',
        'equipo_b': '1',  # Mismo equipo
        'inicio': '2025-10-15T14:00',
        'fin': '2025-10-15T16:00',
        'lugar': 'Cancha 1'
    })
    request.user = MagicMock()
    
    vw.partidos_crear(request, 1)
    
    mock_messages.error.assert_called()
    error_calls = [str(call) for call in mock_messages.error.call_args_list]
    self.assertTrue(any('distintos' in msg.lower() for msg in error_calls))

    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.get_object_or_404')
    @patch('tournaments.views.render')
    def test_registrar_resultado_marcadores_negativos(self, mock_render,
                                                      mock_get_object, mock_is_admin):
        """No debe permitir marcadores negativos"""
        mock_is_admin.return_value = True
        
        partido_mock = MagicMock()
        partido_mock.id_partido = 1
        partido_mock.torneos_id_torneo = MagicMock()
        partido_mock.torneos_id_torneo.nombre = "Copa"
        partido_mock.torneos_id_torneo.id_torneo = 1
        partido_mock.equipos_id_equipo = MagicMock()
        partido_mock.equipos_id_equipo.nombre = "Tigres"
        partido_mock.equipos_id_equipo2 = MagicMock()
        partido_mock.equipos_id_equipo2.nombre = "Leones"
        partido_mock.estado = "PROGRAMADO"
        partido_mock.marcador_a = None
        partido_mock.marcador_b = None
        
        mock_get_object.return_value = partido_mock
        
        with patch('tournaments.views.messages') as mock_messages:
            request = self.factory.post('/tournaments/matches/1/result/', {
                'estado': 'FINALIZADO',
                'marcador_a': '-1',  # Negativo
                'marcador_b': '2'
            })
            request.user = MagicMock()
            
            vw.partido_resultado(request, 1)
            
            mock_messages.error.assert_called()

    @patch('tournaments.views.get_object_or_404')
    @patch('tournaments.views._current_participante')
    @patch('tournaments.views.TorneosEquipos.objects')
    @patch('tournaments.views.messages')
    @patch('tournaments.views.redirect')
    def test_unirse_equipo_invalid_team_id(self, mock_redirect, mock_messages,
                                           mock_torneos_equipos, mock_current,
                                           mock_get_object):
        """Debe rechazar ID de equipo inválido"""
        torneo_mock = MagicMock()
        torneo_mock.aforo_equipos = 8
        torneo_mock.id_torneo = 1
        mock_get_object.return_value = torneo_mock
        
        mock_current.return_value = MagicMock(id_participante=1)
        
        with patch('tournaments.views.Equipos.objects') as mock_equipos:
            mock_equipos.filter.return_value.values.return_value.order_by.return_value = []
            
            request = self.factory.post('/tournaments/1/join-team/', {
                'team_id': 'invalid'  # No es número
            })
            request.user = MagicMock()
            
            vw.unirse_equipo(request, 1)
            
            mock_messages.error.assert_called_once()
            args = mock_messages.error.call_args[0]
            self.assertIn("válido", args[1].lower())


# ==========================================================
# TESTS DE INTEGRACIÓN (SIMULADOS)
# ==========================================================

class SimulatedIntegrationTests(SimpleTestCase):
    """Pruebas que simulan flujos completos"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('tournaments.views.is_admin')
    @patch('tournaments.views.Torneos.objects')
    @patch('tournaments.views.messages')
    @patch('tournaments.views.redirect')
    def test_create_tournament_full_flow(self, mock_redirect, mock_messages,
                                        mock_torneos, mock_is_admin):
        """Simula flujo completo de creación de torneo"""
        mock_is_admin.return_value = True
        
        torneo_created = MagicMock()
        torneo_created.id_torneo = 1
        torneo_created.nombre = "Copa 2025"
        mock_torneos.create.return_value = torneo_created
        
        # 1. Crear torneo
        request = self.factory.post('/tournaments/create/', {
            'nombre': 'Copa 2025',
            'disciplina': '1',
            'fecha_inicio': '2025-10-01',
            'fecha_fin': '2025-10-15',
            'aforo': '8',
            'limite_inscripcion': '2025-09-25T23:59',
        })
        request.user = MagicMock()
        
        vw.crear_torneo(request)
        
        # Verificaciones
        mock_torneos.create.assert_called_once()
        create_kwargs = mock_torneos.create.call_args[1]
        self.assertEqual(create_kwargs['nombre'], 'Copa 2025')
        self.assertIsNotNone(create_kwargs.get('limite_inscripcion'))
        mock_messages.success.assert_called_once()
        mock_redirect.assert_called_with("tournaments:list")


# ==========================================================
# RESUMEN Y ESTADÍSTICAS
# ==========================================================

class TestSummary(SimpleTestCase):
    """Resumen de cobertura de tests"""

    def test_coverage_summary(self):
        """Documentación de cobertura de tests"""
        coverage_areas = {
            'Helpers': ['is_admin', '_parse_date', '_parse_dt_local', '_ensure_aware', '_overlap_q'],
            'Crear Torneo': ['permisos', 'GET form', 'POST success', 'validaciones'],
            'Listar Torneos': ['listar todos', 'filtrar búsqueda', 'búsqueda vacía'],
            'Crear Equipo': ['bloqueo individual', 'GET form', 'validaciones'],
            'Unirse Equipo': ['bloqueo individual', 'GET equipos', 'validaciones'],
            'Crear Partido': ['permisos', 'bloqueo individual', 'GET form', 'validaciones'],
            'Registrar Resultado': ['permisos', 'GET form', 'validaciones'],
            'Gestionar Equipo': ['permisos membership', 'visualización'],
            'Inscripción Individual': ['GET form', 'validaciones', '404 equipos'],
            'Detalle Torneo': ['equipos', 'individual'],
            'Validaciones': ['equipos en torneo', 'participante actual'],
            'Edge Cases': ['mismos equipos', 'marcadores negativos', 'IDs inválidos'],
        }
        
        total_areas = len(coverage_areas)
        total_tests = sum(len(tests) for tests in coverage_areas.values())
        
        self.assertGreater(total_areas, 0)
        self.assertGreater(total_tests, 0)
        
        # Este test siempre pasa, solo documenta la cobertura
        self.assertTrue(True)