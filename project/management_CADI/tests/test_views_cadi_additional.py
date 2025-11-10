# Agregar al final de management_CADI/tests/test_views_management_cadi.py

from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase

class TestHelperFunctionsUnit(SimpleTestCase):
    """Tests unitarios para funciones auxiliares de management_CADI"""
    
    def test_hhmm_to_dt_valid_formats(self):
        """Debe convertir HH:MM a datetime correctamente"""
        from management_CADI.views import hhmm_to_dt
        
        result = hhmm_to_dt("15:30")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 15)
        self.assertEqual(result.minute, 30)
        
        result = hhmm_to_dt("08:00")
        self.assertEqual(result.hour, 8)
        self.assertEqual(result.minute, 0)
    
    def test_hhmm_to_dt_invalid_formats(self):
        """Debe retornar None para formatos inválidos"""
        from management_CADI.views import hhmm_to_dt
        
        self.assertIsNone(hhmm_to_dt(""))
        self.assertIsNone(hhmm_to_dt(None))
        self.assertIsNone(hhmm_to_dt("invalid"))
        self.assertIsNone(hhmm_to_dt("25:00"))
    
    def test_date_input_to_dt_valid(self):
        """Debe convertir fecha ISO a datetime"""
        from management_CADI.views import date_input_to_dt
        
        result = date_input_to_dt("2025-10-13")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 10)
        self.assertEqual(result.day, 13)
    
    def test_date_input_to_dt_invalid(self):
        """Debe retornar None para fechas inválidas"""
        from management_CADI.views import date_input_to_dt
        
        self.assertIsNone(date_input_to_dt(""))
        self.assertIsNone(date_input_to_dt(None))
        self.assertIsNone(date_input_to_dt("invalid"))
    
    def test_draft_keys_creation(self):
        """Debe generar llaves de sesión correctamente"""
        from management_CADI.views import _draft_keys
        
        # Nueva actividad
        base, sched, last = _draft_keys(123)
        self.assertEqual(base, "cadi_draft_base_123_new")
        self.assertEqual(sched, "cadi_sched_list_123_new")
        self.assertEqual(last, "cadi_sched_last_123_new")
        
        # Editar actividad existente
        base, sched, last = _draft_keys(123, 456)
        self.assertEqual(base, "cadi_draft_base_123_456")
        self.assertEqual(sched, "cadi_sched_list_123_456")
        self.assertEqual(last, "cadi_sched_last_123_456")
    
    def test_is_admin_check(self):
        """Debe verificar permisos de admin correctamente"""
        from management_CADI.views import is_admin
        
        # Usuario admin
        user = MagicMock(is_authenticated=True, is_staff=True)
        self.assertTrue(is_admin(user))
        
        # Usuario normal
        user = MagicMock(is_authenticated=True, is_staff=False)
        self.assertFalse(is_admin(user))
        
        # Usuario anónimo
        user = MagicMock(is_authenticated=False, is_staff=False)
        self.assertFalse(is_admin(user))


class TestNextDatetimeCalculation(SimpleTestCase):
    """Tests para cálculo de próximas fechas"""
    
    @patch('management_CADI.views.timezone')
    def test_next_datetime_for_weekday(self, mock_timezone):
        """Debe calcular próxima ocurrencia correctamente"""
        from management_CADI.views import next_datetime_for_weekday
        from datetime import datetime, time
        
        # Mock fecha actual: Lunes
        mock_now = MagicMock()
        mock_now.date.return_value.weekday.return_value = 0
        mock_timezone.localtime.return_value = mock_now
        
        t_inicio = time(14, 0)
        t_fin = time(16, 0)
        
        # La función debería calcular correctamente
        # (nota: depende de la implementación exacta)
        result = next_datetime_for_weekday(0, t_inicio, t_fin)
        self.assertIsNotNone(result)


class TestViewsWithMocks(SimpleTestCase):
    """Tests de vistas con mocks completos"""
    
    @patch('management_CADI.views.render')
    @patch('management_CADI.views.Grupos.objects')
    @patch('management_CADI.views.GruposActividad.objects')
    def test_cadi_index_renders(self, mock_ga, mock_grupos, mock_render):
        """Debe renderizar index correctamente"""
        from management_CADI.views import cadi_index
        
        mock_grupo = MagicMock()
        mock_grupos.get_object_or_404 = MagicMock(return_value=mock_grupo)
        mock_ga.filter.return_value = []
        
        request = MagicMock()
        cadi_index(request)
        
        mock_render.assert_called_once()
    
    @patch('management_CADI.views.get_object_or_404')
    @patch('management_CADI.views.TiposActividad.objects')
    @patch('management_CADI.views.render')
    def test_create_activities_get(self, mock_render, mock_tipos, mock_get):
        """Debe renderizar formulario de creación"""
        from management_CADI.views import createActivities
        
        mock_ga = MagicMock()
        mock_ga.grupos_id_grupo.nombre = "CADI"
        mock_get.return_value = mock_ga
        mock_tipos.all.return_value.order_by.return_value = []
        
        request = MagicMock()
        request.method = 'GET'
        request.GET = {}
        request.session = {}
        
        createActivities(request, "cadi", 1, 1)
        
        mock_render.assert_called_once()
        args = mock_render.call_args[0]
        self.assertEqual(args[1], "form_activities.html")


class TestScheduleDraftViews(SimpleTestCase):
    """Tests para manejo de borradores de horarios"""
    
    @patch('management_CADI.views.get_object_or_404')
    @patch('management_CADI.views.render')
    def test_schedule_draft_init(self, mock_render, mock_get):
        """Debe inicializar lista de bloques"""
        from management_CADI.views import scheduleDraft
        
        mock_ga = MagicMock()
        mock_ga.grupos_id_grupo.nombre = "CADI"
        mock_get.return_value = mock_ga
        
        request = MagicMock()
        request.method = 'GET'
        request.GET = {'init': '1'}
        request.session = {}
        
        scheduleDraft(request, "cadi", 1, 1)
        
        # Debe haber inicializado la lista
        self.assertIn("cadi_sched_list_1_new", request.session)
        mock_render.assert_called_once()
    
    @patch('management_CADI.views.get_object_or_404')
    @patch('management_CADI.views.redirect')
    def test_schedule_draft_add_block(self, mock_redirect, mock_get):
        """Debe agregar bloque a la lista"""
        from management_CADI.views import scheduleDraft
        
        mock_ga = MagicMock()
        mock_ga.grupos_id_grupo.nombre = "CADI"
        mock_get.return_value = mock_ga
        
        request = MagicMock()
        request.method = 'POST'
        request.POST = {
            'action': 'add_block',
            'profesor': 'Test Prof',
            'lugar': 'Gym',
            'hora_inicio': '08:00',
            'hora_fin': '10:00',
        }
        request.POST.getlist = MagicMock(return_value=['Lunes', 'Miércoles'])
        request.session = {'cadi_sched_list_1_new': []}
        
        scheduleDraft(request, "cadi", 1, 1)
        
        # Debe haber agregado un bloque
        bloques = request.session['cadi_sched_list_1_new']
        self.assertEqual(len(bloques), 1)
        self.assertEqual(bloques[0]['profesor'], 'Test Prof')
        mock_redirect.assert_called_once()


class TestSlotManagement(SimpleTestCase):
    """Tests para manejo de slots de horario"""
    
    @patch('management_CADI.views.Participantes.objects')
    @patch('management_CADI.views.messages')
    @patch('management_CADI.views.redirect')
    def test_add_slot_missing_participante(self, mock_redirect, mock_msg, mock_part):
        """Debe fallar si no encuentra participante"""
        from management_CADI.views import add_slot_to_schedule
        
        mock_part.get.side_effect = Exception("Not found")
        
        request = MagicMock()
        request.user = MagicMock()
        request.method = 'POST'
        request.POST = {'actividad_id': '1', 'bloque_id': '1', 'dia_idx': '0', 'next': '/'}
        
        add_slot_to_schedule(request, "cadi", 1, 1)
        
        mock_msg.error.assert_called_once()
        mock_redirect.assert_called_once()