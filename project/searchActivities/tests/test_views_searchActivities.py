from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, time, timedelta
from django.utils import timezone
from searchActivities.views import search, rateActivity, add_slot_from_search


# ===================================
# TESTS PARA search() - COBERTURA COMPLETA
# ===================================

class TestSearchView(TestCase):
    """Tests completos para la vista search"""
    
    databases = '__all__'
    
    def setUp(self):
        self.factory = RequestFactory()
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    def test_search_usuario_no_autenticado(
        self, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Usuario sin autenticar puede buscar"""
        mock_qs = self._setup_basic_mocks(
            mock_act, mock_tipos, mock_bloques, 
            mock_horarios_act, mock_calif
        )
        
        request = self.factory.get('/buscar/')
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        search(request)
        
        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        self.assertIn('actividades', context)
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    def test_search_usuario_autenticado_sin_participante(
        self, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Usuario autenticado pero sin perfil participante"""
        self._setup_basic_mocks(
            mock_act, mock_tipos, mock_bloques, 
            mock_horarios_act, mock_calif
        )
        
        mock_participantes.objects.get.side_effect = mock_participantes.DoesNotExist
        
        request = self.factory.get('/buscar/')
        request.user = MagicMock()
        request.user.is_authenticated = True
        
        search(request)
        
        mock_render.assert_called_once()
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    @patch('searchActivities.views.PG_TRIGRAM_AVAILABLE', True)
    @patch('searchActivities.views.Unaccent')
    def test_search_con_trigram_y_query(
        self, mock_unaccent, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Búsqueda con query usando trigram"""
        # Mock Unaccent para que funcione
        mock_unaccent.return_value = MagicMock()
        
        mock_qs = self._setup_basic_mocks(
            mock_act, mock_tipos, mock_bloques, 
            mock_horarios_act, mock_calif
        )
        
        request = self.factory.get('/buscar/', {'q': 'yoga'})
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        search(request)
        
        # Verificar que se usó annotate (trigram)
        self.assertTrue(mock_qs.annotate.called)
        mock_render.assert_called_once()
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    @patch('searchActivities.views.PG_TRIGRAM_AVAILABLE', False)
    def test_search_sin_trigram_con_query(
        self, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Búsqueda sin trigram (fallback a icontains)"""
        mock_qs = self._setup_basic_mocks(
            mock_act, mock_tipos, mock_bloques, 
            mock_horarios_act, mock_calif
        )
        
        request = self.factory.get('/buscar/', {'q': 'yoga'})
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        search(request)
        
        # Debe usar filter con icontains
        self.assertTrue(mock_qs.filter.called)
        mock_render.assert_called_once()
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    def test_search_filtro_por_tipo_valido(
        self, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Filtrar por tipo válido"""
        mock_qs = self._setup_basic_mocks(
            mock_act, mock_tipos, mock_bloques, 
            mock_horarios_act, mock_calif
        )
        
        request = self.factory.get('/buscar/', {'tipo': '1'})
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        search(request)
        
        mock_qs.filter.assert_called()
        mock_render.assert_called_once()
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    def test_search_filtro_por_tipo_invalido(
        self, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Tipo inválido debe ser ignorado sin error"""
        self._setup_basic_mocks(
            mock_act, mock_tipos, mock_bloques, 
            mock_horarios_act, mock_calif
        )
        
        request = self.factory.get('/buscar/', {'tipo': 'invalid'})
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        # No debe lanzar excepción
        search(request)
        mock_render.assert_called_once()
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    def test_search_only_available(
        self, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Filtrar solo actividades con horarios disponibles"""
        mock_qs = self._setup_basic_mocks(
            mock_act, mock_tipos, mock_bloques, 
            mock_horarios_act, mock_calif
        )
        
        request = self.factory.get('/buscar/', {'only': '1'})
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        search(request)
        
        # Debe filtrar por actividades con bloques
        self.assertTrue(mock_qs.filter.called)
        mock_render.assert_called_once()
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    def test_search_con_resultados_y_calificaciones(
        self, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Búsqueda con resultados y cálculo de calificaciones"""
        actividades_mock = [
            {'id_actividad': 1, 'nombre': 'Yoga', 'descripcion': 'Clase de yoga'}
        ]
        
        mock_qs = self._setup_mocks_with_activities(
            mock_act, mock_tipos, mock_bloques, mock_horarios_act, 
            mock_calif, actividades_mock
        )
        
        # Mock calificación promedio
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 4.5}
        
        request = self.factory.get('/buscar/')
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        search(request)
        
        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        self.assertEqual(len(context['actividades']), 1)
        self.assertEqual(context['actividades'][0]['rating_image'], 'rating_4_5.png')
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    def test_search_rating_images_todos_rangos(
        self, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Verificar todos los rangos de rating images"""
        actividades_mock = [{'id_actividad': i, 'nombre': f'Act{i}', 'descripcion': ''} 
                           for i in range(12)]
        
        self._setup_mocks_with_activities(
            mock_act, mock_tipos, mock_bloques, mock_horarios_act, 
            mock_calif, actividades_mock
        )
        
        # Promedios para cada rango
        promedios = [0, 0.3, 0.8, 1.3, 1.8, 2.3, 2.8, 3.3, 3.8, 4.3, 4.8, 5.0]
        expected_images = [
            'rating_0_0.png', 'rating_0_5.png', 'rating_1_0.png', 
            'rating_1_5.png', 'rating_2_0.png', 'rating_2_5.png',
            'rating_3_0.png', 'rating_3_5.png', 'rating_4_0.png',
            'rating_4_5.png', 'rating_5_0.png', 'rating_5_0.png'
        ]
        
        def side_effect_aggregate(*args, **kwargs):
            idx = mock_calif.objects.filter.call_count - 1
            return {'estrellas__avg': promedios[idx % len(promedios)]}
        
        mock_calif.objects.filter.return_value.aggregate.side_effect = side_effect_aggregate
        
        request = self.factory.get('/buscar/')
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        search(request)
        
        context = mock_render.call_args[0][2]
        for i, act in enumerate(context['actividades']):
            self.assertEqual(act['rating_image'], expected_images[i])
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    def test_search_con_horarios_y_dias(
        self, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Búsqueda con horarios y días de semana"""
        actividades_mock = [{'id_actividad': 1, 'nombre': 'Yoga', 'descripcion': ''}]
        bloques_mock = [{
            'id_horario_bloque': 1,
            'actividades_id_actividad': 1,
            'profesor': 'Juan',
            'lugar': 'Sala A',
            'hora_inicio': time(10, 0),
            'hora_fin': time(11, 0)
        }]
        dias_mock = [
            {'horario_bloque_id': 1, 'dia_semana': 0},  # Lunes
            {'horario_bloque_id': 1, 'dia_semana': 2},  # Miércoles
        ]
        
        mock_qs = self._setup_mocks_with_schedules(
            mock_act, mock_tipos, mock_bloques, mock_horarios_act,
            mock_calif, actividades_mock, bloques_mock, dias_mock
        )
        
        request = self.factory.get('/buscar/')
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        search(request)
        
        context = mock_render.call_args[0][2]
        actividad = context['actividades'][0]
        self.assertEqual(len(actividad['items_dia']), 2)
        self.assertEqual(actividad['items_dia'][0]['dia'], 'Lunes')
        self.assertEqual(actividad['items_dia'][1]['dia'], 'Miércoles')
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    def test_search_usuario_con_participante_y_calificaciones(
        self, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Usuario con participante: marcar actividades calificadas/participadas"""
        actividades_mock = [
            {'id_actividad': 1, 'nombre': 'Yoga', 'descripcion': ''},
            {'id_actividad': 2, 'nombre': 'Pilates', 'descripcion': ''}
        ]
        
        self._setup_mocks_with_activities(
            mock_act, mock_tipos, mock_bloques, mock_horarios_act,
            mock_calif, actividades_mock
        )
        
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        # Actividad 1: calificada y participada
        # Actividad 2: solo participada
        mock_calif.objects.filter.return_value.values_list.return_value = [1]
        mock_participaciones.objects.filter.return_value.values_list.return_value = [1, 2]
        
        request = self.factory.get('/buscar/')
        request.user = MagicMock()
        request.user.is_authenticated = True
        
        search(request)
        
        context = mock_render.call_args[0][2]
        self.assertTrue(context['actividades'][0]['user_has_calificado'])
        self.assertTrue(context['actividades'][0]['user_has_participacion'])
        self.assertFalse(context['actividades'][1]['user_has_calificado'])
        self.assertTrue(context['actividades'][1]['user_has_participacion'])
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    @patch('searchActivities.views.timezone')
    def test_search_deteccion_horarios_ya_agregados(
        self, mock_timezone, mock_render, mock_participantes, mock_act, 
        mock_tipos, mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Detectar horarios ya agregados al calendario del usuario"""
        actividades_mock = [{'id_actividad': 1, 'nombre': 'Yoga', 'descripcion': ''}]
        bloques_mock = [{
            'id_horario_bloque': 1,
            'actividades_id_actividad': 1,
            'profesor': 'Juan',
            'lugar': 'Sala A',
            'hora_inicio': time(10, 0),
            'hora_fin': time(11, 0)
        }]
        dias_mock = [{'horario_bloque_id': 1, 'dia_semana': 0}]  # Lunes
        
        self._setup_mocks_with_schedules(
            mock_act, mock_tipos, mock_bloques, mock_horarios_act,
            mock_calif, actividades_mock, bloques_mock, dias_mock
        )
        
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        # Mock horario del usuario que coincide exactamente
        mock_dt_inicio = MagicMock()
        mock_dt_inicio.weekday.return_value = 0  # Lunes
        mock_dt_inicio.time.return_value = time(10, 0)
        
        mock_dt_fin = MagicMock()
        mock_dt_fin.weekday.return_value = 0
        mock_dt_fin.time.return_value = time(11, 0)
        
        user_slot = {
            'fecha_inicio': mock_dt_inicio,
            'fecha_fin': mock_dt_fin,
            'actividades_id_actividad': 1  # Misma actividad
        }
        mock_horarios_part.objects.filter.return_value.values.return_value = [user_slot]
        
        # Mock timezone.localtime para retornar los objetos correctos
        def localtime_effect(dt):
            return dt
        mock_timezone.localtime.side_effect = localtime_effect
        
        mock_calif.objects.filter.return_value.values_list.return_value = []
        mock_participaciones.objects.filter.return_value.values_list.return_value = []
        
        request = self.factory.get('/buscar/')
        request.user = MagicMock()
        request.user.is_authenticated = True
        
        search(request)
        
        context = mock_render.call_args[0][2]
        # Verificar que el horario está marcado como agregado
        self.assertTrue(context['actividades'][0]['items_dia'][0]['already_added'])
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    @patch('searchActivities.views.timezone')
    def test_search_deteccion_conflictos_horarios(
        self, mock_timezone, mock_render, mock_participantes, mock_act, 
        mock_tipos, mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Detectar conflictos de horarios con actividades ya programadas"""
        actividades_mock = [{'id_actividad': 1, 'nombre': 'Yoga', 'descripcion': ''}]
        bloques_mock = [{
            'id_horario_bloque': 1,
            'actividades_id_actividad': 1,
            'profesor': 'Juan',
            'lugar': 'Sala A',
            'hora_inicio': time(10, 0),
            'hora_fin': time(11, 0)
        }]
        dias_mock = [{'horario_bloque_id': 1, 'dia_semana': 0}]  # Lunes
        
        self._setup_mocks_with_schedules(
            mock_act, mock_tipos, mock_bloques, mock_horarios_act,
            mock_calif, actividades_mock, bloques_mock, dias_mock
        )
        
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        # Mock horario que se cruza (10:30-11:30)
        mock_dt_inicio = MagicMock()
        mock_dt_inicio.weekday.return_value = 0
        mock_dt_inicio.time.return_value = time(10, 30)
        
        mock_dt_fin = MagicMock()
        mock_dt_fin.weekday.return_value = 0
        mock_dt_fin.time.return_value = time(11, 30)
        
        def localtime_side_effect(dt):
            if dt == 'inicio':
                return mock_dt_inicio
            return mock_dt_fin
        
        mock_timezone.localtime.side_effect = lambda x: mock_dt_inicio if 'inicio' in str(x) else mock_dt_fin
        
        user_slot = {
            'fecha_inicio': 'inicio',
            'fecha_fin': 'fin',
            'actividades_id_actividad': 2  # Otra actividad
        }
        mock_horarios_part.objects.filter.return_value.values.return_value = [user_slot]
        
        mock_calif.objects.filter.return_value.values_list.return_value = []
        mock_participaciones.objects.filter.return_value.values_list.return_value = []
        
        request = self.factory.get('/buscar/')
        request.user = MagicMock()
        request.user.is_authenticated = True
        
        search(request)
        
        context = mock_render.call_args[0][2]
        self.assertTrue(context['actividades'][0]['items_dia'][0]['conflict'])
    
    # Métodos helper
    def _setup_basic_mocks(self, mock_act, mock_tipos, mock_bloques, mock_horarios_act, mock_calif):
        """Setup básico de mocks"""
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs
        mock_qs.values.return_value = []
        
        mock_act.objects = mock_qs
        mock_tipos.objects.annotate.return_value.values.return_value.order_by.return_value = []
        mock_bloques.objects.filter.return_value.values.return_value = []
        mock_horarios_act.objects.filter.return_value.values.return_value = []
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 0}
        
        return mock_qs
    
    def _setup_mocks_with_activities(self, mock_act, mock_tipos, mock_bloques, 
                                     mock_horarios_act, mock_calif, actividades):
        """Setup mocks con actividades específicas"""
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs
        mock_qs.values.return_value = actividades
        
        mock_act.objects = mock_qs
        mock_tipos.objects.annotate.return_value.values.return_value.order_by.return_value = []
        mock_bloques.objects.filter.return_value.values.return_value = []
        mock_horarios_act.objects.filter.return_value.values.return_value = []
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 0}
        
        return mock_qs
    
    def _setup_mocks_with_schedules(self, mock_act, mock_tipos, mock_bloques,
                                   mock_horarios_act, mock_calif, actividades, 
                                   bloques, dias):
        """Setup mocks con horarios y días"""
        mock_qs = self._setup_mocks_with_activities(
            mock_act, mock_tipos, mock_bloques, mock_horarios_act,
            mock_calif, actividades
        )
        
        mock_bloques.objects.filter.return_value.values.return_value = bloques
        mock_horarios_act.objects.filter.return_value.values.return_value = dias
        
        return mock_qs


# ===================================
# TESTS PARA rateActivity()
# ===================================

class TestRateActivityView(TestCase):
    """Tests completos para la vista rateActivity"""
    
    databases = '__all__'
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user('testuser', 'test@test.com', 'pass')
    
     
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.render')
    def test_rate_activity_get_con_participacion(
        self, mock_render, mock_calif, mock_act, mock_participantes, 
        mock_participaciones, mock_messages
    ):
        """GET: mostrar formulario de calificación"""
        mock_actividad = MagicMock()
        mock_actividad.id_actividad = 1
        mock_act.objects.get.return_value = mock_actividad
        
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        mock_participaciones.objects.filter.return_value.exists.return_value = True
        
        mock_calificacion = MagicMock()
        mock_calificacion.estrellas = 4
        mock_calificacion.comentario = "Excelente"
        mock_calif.objects.get_or_create.return_value = (mock_calificacion, False)
        
        request = self.factory.get('/calificar/1/')
        request.user = self.user
        
        rateActivity(request, 1)
        
        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        self.assertIn('actividad', context)
        self.assertIn('calificacion', context)
        self.assertIn('stars_range', context)
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.redirect')
    def test_rate_activity_post_guardar_calificacion(
        self, mock_redirect, mock_calif, mock_act, mock_participantes, 
        mock_participaciones, mock_messages
    ):
        """POST: guardar calificación nueva"""
        mock_actividad = MagicMock()
        mock_actividad.id_actividad = 1
        mock_act.objects.get.return_value = mock_actividad
        
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        mock_participaciones.objects.filter.return_value.exists.return_value = True
        
        mock_calificacion = MagicMock()
        mock_calificacion.estrellas = 0
        mock_calificacion.comentario = ""
        mock_calif.objects.get_or_create.return_value = (mock_calificacion, True)
        
        request = self.factory.post('/calificar/1/', {
            'estrellas': '5',
            'comentario': 'Muy buena actividad'
        })
        request.user = self.user
        request.GET = {}
        
        rateActivity(request, 1)
        
        self.assertEqual(mock_calificacion.estrellas, 5)
        self.assertEqual(mock_calificacion.comentario, 'Muy buena actividad')
        mock_calificacion.save.assert_called_once()
        mock_messages.success.assert_called_once()
        mock_redirect.assert_called_once()
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.redirect')
    def test_rate_activity_post_actualizar_calificacion(
        self, mock_redirect, mock_calif, mock_act, mock_participantes, 
        mock_participaciones, mock_messages
    ):
        """POST: actualizar calificación existente"""
        mock_actividad = MagicMock()
        mock_actividad.id_actividad = 1
        mock_act.objects.get.return_value = mock_actividad
        
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        mock_participaciones.objects.filter.return_value.exists.return_value = True
        
        mock_calificacion = MagicMock()
        mock_calificacion.estrellas = 3
        mock_calificacion.comentario = "Regular"
        mock_calif.objects.get_or_create.return_value = (mock_calificacion, False)
        
        request = self.factory.post('/calificar/1/', {
            'estrellas': '5',
            'comentario': 'Mejoró mucho'
        })
        request.user = self.user
        request.GET = {}
        
        rateActivity(request, 1)
        
        self.assertEqual(mock_calificacion.estrellas, 5)
        self.assertEqual(mock_calificacion.comentario, 'Mejoró mucho')
        mock_calificacion.save.assert_called_once_with(
            update_fields=['estrellas', 'comentario']
        )
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.redirect')
    def test_rate_activity_sanitizar_estrellas_mayor_5(
        self, mock_redirect, mock_calif, mock_act, mock_participantes, 
        mock_participaciones, mock_messages
    ):
        """POST: sanitizar estrellas > 5"""
        mock_actividad = MagicMock()
        mock_act.objects.get.return_value = mock_actividad
        mock_participantes.objects.get.return_value = MagicMock()
        mock_participaciones.objects.filter.return_value.exists.return_value = True
        
        mock_calificacion = MagicMock()
        mock_calif.objects.get_or_create.return_value = (mock_calificacion, False)
        
        request = self.factory.post('/calificar/1/', {
            'estrellas': '10',
            'comentario': 'Test'
        })
        request.user = self.user
        request.GET = {}
        
        rateActivity(request, 1)
        
        self.assertEqual(mock_calificacion.estrellas, 5)
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.redirect')
    def test_rate_activity_sanitizar_estrellas_menor_0(
        self, mock_redirect, mock_calif, mock_act, mock_participantes, 
        mock_participaciones, mock_messages
    ):
        """POST: sanitizar estrellas < 0"""
        mock_actividad = MagicMock()
        mock_act.objects.get.return_value = mock_actividad
        mock_participantes.objects.get.return_value = MagicMock()
        mock_participaciones.objects.filter.return_value.exists.return_value = True
        
        mock_calificacion = MagicMock()
        mock_calif.objects.get_or_create.return_value = (mock_calificacion, False)
        
        request = self.factory.post('/calificar/1/', {
            'estrellas': '-5',
            'comentario': 'Test'
        })
        request.user = self.user
        request.GET = {}
        
        rateActivity(request, 1)
        
        self.assertEqual(mock_calificacion.estrellas, 0)
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.redirect')
    def test_rate_activity_estrellas_invalidas(
        self, mock_redirect, mock_calif, mock_act, mock_participantes, 
        mock_participaciones, mock_messages
    ):
        """POST: manejar estrellas inválidas"""
        mock_actividad = MagicMock()
        mock_act.objects.get.return_value = mock_actividad
        mock_participantes.objects.get.return_value = MagicMock()
        mock_participaciones.objects.filter.return_value.exists.return_value = True
        
        mock_calificacion = MagicMock()
        mock_calif.objects.get_or_create.return_value = (mock_calificacion, False)
        
        request = self.factory.post('/calificar/1/', {
            'estrellas': 'invalid',
            'comentario': 'Test'
        })
        request.user = self.user
        request.GET = {}
        
        rateActivity(request, 1)
        
        self.assertEqual(mock_calificacion.estrellas, 0)
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.redirect')
    def test_rate_activity_comentario_vacio(
        self, mock_redirect, mock_calif, mock_act, mock_participantes, 
        mock_participaciones, mock_messages
    ):
        """POST: comentario vacío debe guardarse"""
        mock_actividad = MagicMock()
        mock_act.objects.get.return_value = mock_actividad
        mock_participantes.objects.get.return_value = MagicMock()
        mock_participaciones.objects.filter.return_value.exists.return_value = True
        
        mock_calificacion = MagicMock()
        mock_calif.objects.get_or_create.return_value = (mock_calificacion, False)
        
        request = self.factory.post('/calificar/1/', {
            'estrellas': '4',
            'comentario': '   '  # Solo espacios
        })
        request.user = self.user
        request.GET = {}
        
        rateActivity(request, 1)
        
        self.assertEqual(mock_calificacion.comentario, '')
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.redirect')
    def test_rate_activity_redirect_con_next(
        self, mock_redirect, mock_calif, mock_act, mock_participantes, 
        mock_participaciones, mock_messages
    ):
        """POST: redirigir a next URL si está presente"""
        mock_actividad = MagicMock()
        mock_act.objects.get.return_value = mock_actividad
        mock_participantes.objects.get.return_value = MagicMock()
        mock_participaciones.objects.filter.return_value.exists.return_value = True
        
        mock_calificacion = MagicMock()
        mock_calif.objects.get_or_create.return_value = (mock_calificacion, False)
        
        request = self.factory.post('/calificar/1/?next=/mis-actividades/', {
            'estrellas': '5',
            'comentario': 'Test'
        })
        request.user = self.user
        request.GET = {'next': '/mis-actividades/'}
        
        rateActivity(request, 1)
        
        mock_redirect.assert_called_once_with('/mis-actividades/')


# ===================================
# TESTS PARA add_slot_from_search()
# ===================================

class TestAddSlotFromSearchView(TestCase):
    """Tests completos para la vista add_slot_from_search"""
    
    databases = '__all__'
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user('testuser', 'test@test.com', 'pass')
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.redirect')
    def test_add_slot_datos_incompletos(
        self, mock_redirect, mock_participantes, mock_messages
    ):
        """Solicitud con datos incompletos"""
        mock_participantes.objects.get.return_value = MagicMock()
        
        request = self.factory.post('/add-slot/', {
            'actividad_id': '1',
            # Falta bloque_id y dia_idx
        })
        request.user = self.user
        request.POST = {'actividad_id': '1'}
        request.META = {'HTTP_REFERER': '/buscar/'}
        
        add_slot_from_search(request)
        
        mock_messages.error.assert_called_once()
        self.assertIn('incompleta', mock_messages.error.call_args[0][1])
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.redirect')
    def test_add_slot_dia_invalido(
        self, mock_redirect, mock_participantes, mock_messages
    ):
        """Día inválido (no numérico)"""
        mock_participantes.objects.get.return_value = MagicMock()
        
        request = self.factory.post('/add-slot/', {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': 'invalid',
            'next': '/buscar/'
        })
        request.user = self.user
        request.POST = {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': 'invalid',
            'next': '/buscar/'
        }
        request.META = {}
        
        add_slot_from_search(request)
        
        mock_messages.error.assert_called_once()
        self.assertIn('inválido', mock_messages.error.call_args[0][1])
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.get_object_or_404')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.timezone')
    @patch('searchActivities.views.redirect')
    def test_add_slot_exitoso(
        self, mock_redirect, mock_timezone, mock_participantes, 
        mock_get_object, mock_horarios_part, mock_messages
    ):
        """Agregar slot exitosamente"""
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        mock_actividad = MagicMock()
        mock_actividad.nombre = "Yoga"
        
        mock_bloque = MagicMock()
        mock_bloque.hora_inicio = time(10, 0)
        mock_bloque.hora_fin = time(11, 0)
        
        mock_get_object.side_effect = [mock_actividad, mock_bloque]
        
        mock_now = MagicMock()
        mock_now.date.return_value = datetime(2025, 11, 18).date()
        mock_timezone.localtime.return_value = mock_now
        mock_timezone.make_aware = lambda x: x
        
        mock_filter_result = MagicMock()
        mock_filter_result.exists.return_value = False
        mock_horarios_part.objects.filter.return_value = mock_filter_result
        
        # Lanzar excepción genérica al crear
        mock_horarios_part.objects.create.side_effect = Exception("Error genérico")
        
        request = self.factory.post('/add-slot/', {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        })
        request.user = self.user
        request.POST = {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        }
        request.META = {}
        
        add_slot_from_search(request)
        
        mock_messages.error.assert_called_once()
        self.assertIn('No se pudo agregar', mock_messages.error.call_args[0][1])


# ===================================
# TESTS ADICIONALES PARA MEJORAR COBERTURA
# ===================================

class TestSearchMultipleTerms(TestCase):
    """Tests de búsqueda con múltiples términos"""
    
    databases = '__all__'
    
    def setUp(self):
        self.factory = RequestFactory()
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    @patch('searchActivities.views.PG_TRIGRAM_AVAILABLE', True)
    @patch('searchActivities.views.Unaccent')
    def test_search_multiple_terms_con_trigram(
        self, mock_unaccent, mock_render, mock_participantes, mock_act, 
        mock_tipos, mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Búsqueda con múltiples términos usando trigram"""
        mock_unaccent.return_value = MagicMock()
        
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs
        mock_qs.values.return_value = []
        
        mock_act.objects = mock_qs
        mock_tipos.objects.annotate.return_value.values.return_value.order_by.return_value = []
        mock_bloques.objects.filter.return_value.values.return_value = []
        mock_horarios_act.objects.filter.return_value.values.return_value = []
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 0}
        
        request = self.factory.get('/buscar/', {'q': 'yoga principiantes'})
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        search(request)
        
        # Debe usar filter con múltiples términos
        self.assertTrue(mock_qs.filter.called)
        mock_render.assert_called_once()
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    @patch('searchActivities.views.PG_TRIGRAM_AVAILABLE', False)
    def test_search_multiple_terms_sin_trigram(
        self, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Búsqueda con múltiples términos sin trigram"""
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs
        mock_qs.values.return_value = []
        
        mock_act.objects = mock_qs
        mock_tipos.objects.annotate.return_value.values.return_value.order_by.return_value = []
        mock_bloques.objects.filter.return_value.values.return_value = []
        mock_horarios_act.objects.filter.return_value.values.return_value = []
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 0}
        
        request = self.factory.get('/buscar/', {'q': 'yoga principiantes'})
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        search(request)
        
        # Debe aplicar filtros para cada término
        call_count = mock_qs.filter.call_count
        self.assertGreaterEqual(call_count, 2)  # Al menos 2 términos
        mock_render.assert_called_once()


class TestSearchOrderingAndContext(TestCase):
    """Tests de ordenamiento y contexto"""
    
    databases = '__all__'
    
    def setUp(self):
        self.factory = RequestFactory()
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    def test_search_context_completo(
        self, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Verificar que el contexto tiene todos los campos necesarios"""
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs
        mock_qs.values.return_value = []
        
        mock_act.objects = mock_qs
        mock_tipos.objects.annotate.return_value.values.return_value.order_by.return_value = [
            {'id_tipo': 1, 'nombre': 'Deportes'}
        ]
        mock_bloques.objects.filter.return_value.values.return_value = []
        mock_horarios_act.objects.filter.return_value.values.return_value = []
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 0}
        
        request = self.factory.get('/buscar/', {'q': 'test', 'tipo': '1', 'only': '1'})
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        search(request)
        
        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        
        # Verificar campos del contexto
        self.assertIn('q', context)
        self.assertIn('tipo_id', context)
        self.assertIn('only_available', context)
        self.assertIn('tipos', context)
        self.assertIn('actividades', context)
        self.assertIn('using_trigram', context)
        
        self.assertEqual(context['q'], 'test')
        self.assertEqual(context['tipo_id'], '1')
        self.assertTrue(context['only_available'])
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.Participaciones')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.render')
    def test_search_selected_tipo_name(
        self, mock_render, mock_participantes, mock_act, mock_tipos, 
        mock_bloques, mock_horarios_act, mock_horarios_part, 
        mock_participaciones, mock_calif
    ):
        """Verificar que se obtiene el nombre del tipo seleccionado"""
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs
        mock_qs.values.return_value = []
        
        mock_act.objects = mock_qs
        
        # Mock para obtener nombre del tipo
        mock_tipo_qs = MagicMock()
        mock_tipo_qs.filter.return_value = mock_tipo_qs
        mock_tipo_qs.annotate.return_value = mock_tipo_qs
        mock_tipo_qs.values.return_value.first.return_value = {'nombre': 'Deportes'}
        mock_tipo_qs.values.return_value.order_by.return_value = []
        
        mock_tipos.objects = mock_tipo_qs
        mock_bloques.objects.filter.return_value.values.return_value = []
        mock_horarios_act.objects.filter.return_value.values.return_value = []
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 0}
        
        request = self.factory.get('/buscar/', {'tipo': '1'})
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        search(request)
        
        context = mock_render.call_args[0][2]
        self.assertEqual(context['selected_tipo_name'], 'Deportes')


# Mover estos tests a una nueva clase con setUp correcto
class TestAddSlotEdgeCases(TestCase):
    """Tests adicionales para add_slot_from_search"""
    
    databases = '__all__'
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user('testuser', 'test@test.com', 'pass')
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.get_object_or_404')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.timezone')
    @patch('searchActivities.views.redirect')
    def test_add_slot_duplicado(
        self, mock_redirect, mock_timezone, mock_participantes, 
        mock_get_object, mock_horarios_part, mock_messages
    ):
        """Intentar agregar slot duplicado"""
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        mock_actividad = MagicMock()
        mock_bloque = MagicMock()
        mock_bloque.hora_inicio = time(10, 0)
        mock_bloque.hora_fin = time(11, 0)
        
        mock_get_object.side_effect = [mock_actividad, mock_bloque]
        
        mock_now = MagicMock()
        mock_now.date.return_value = datetime(2025, 11, 18).date()
        mock_timezone.localtime.return_value = mock_now
        mock_timezone.make_aware = lambda x: x
        
        # Ya existe
        mock_horarios_part.objects.filter.return_value.exists.return_value = True
        
        request = self.factory.post('/add-slot/', {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        })
        request.user = self.user
        request.POST = {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        }
        request.META = {}
        
        add_slot_from_search(request)
        
        mock_messages.info.assert_called_once()
        self.assertIn('ya está', mock_messages.info.call_args[0][1])
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.get_object_or_404')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.timezone')
    @patch('searchActivities.views.redirect')
    def test_add_slot_conflicto_horario(
        self, mock_redirect, mock_timezone, mock_participantes, 
        mock_get_object, mock_horarios_part, mock_messages
    ):
        """Detectar conflicto con otro horario"""
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        mock_actividad = MagicMock()
        mock_bloque = MagicMock()
        mock_bloque.hora_inicio = time(10, 0)
        mock_bloque.hora_fin = time(11, 0)
        
        mock_get_object.side_effect = [mock_actividad, mock_bloque]
        
        mock_now = MagicMock()
        mock_now.date.return_value = datetime(2025, 11, 18).date()
        mock_timezone.localtime = lambda dt=None: mock_now if dt is None else dt
        mock_timezone.make_aware = lambda x: x
        
        # No es duplicado
        mock_filter_exists = MagicMock()
        mock_filter_exists.exists.return_value = False
        
        # Pero hay conflicto
        mock_existing = MagicMock()
        mock_existing_dt_inicio = MagicMock()
        mock_existing_dt_inicio.weekday.return_value = 0  # Lunes
        mock_existing_dt_inicio.time.return_value = time(10, 30)
        mock_existing_dt_inicio.timetz.return_value.replace.return_value = time(10, 30)
        
        mock_existing_dt_fin = MagicMock()
        mock_existing_dt_fin.time.return_value = time(11, 30)
        mock_existing_dt_fin.timetz.return_value.replace.return_value = time(11, 30)
        
        mock_existing.fecha_inicio = mock_existing_dt_inicio
        mock_existing.fecha_fin = mock_existing_dt_fin
        
        def filter_side_effect(*args, **kwargs):
            if 'fecha_inicio__time' in kwargs:
                return mock_filter_exists
            return [mock_existing]
        
        mock_horarios_part.objects.filter.side_effect = filter_side_effect
        
        request = self.factory.post('/add-slot/', {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        })
        request.user = self.user
        request.POST = {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        }
        request.META = {}
        
        add_slot_from_search(request)
        
        mock_messages.error.assert_called_once()
        self.assertIn('cruza', mock_messages.error.call_args[0][1])
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.get_object_or_404')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.timezone')
    @patch('searchActivities.views.redirect')
    def test_add_slot_integrity_error(
        self, mock_redirect, mock_timezone, mock_participantes, 
        mock_get_object, mock_horarios_part, mock_messages
    ):
        """Manejar IntegrityError al insertar"""
        from django.db import IntegrityError
        
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        mock_actividad = MagicMock()
        mock_actividad.nombre = "Yoga"
        mock_bloque = MagicMock()
        mock_bloque.hora_inicio = time(10, 0)
        mock_bloque.hora_fin = time(11, 0)
        
        mock_get_object.side_effect = [mock_actividad, mock_bloque]
        
        mock_now = MagicMock()
        mock_now.date.return_value = datetime(2025, 11, 18).date()
        mock_timezone.localtime.return_value = mock_now
        mock_timezone.make_aware = lambda x: x
        
        mock_filter_result = MagicMock()
        mock_filter_result.exists.return_value = False
        mock_horarios_part.objects.filter.return_value = mock_filter_result
        
        # Lanzar IntegrityError al crear
        mock_horarios_part.objects.create.side_effect = IntegrityError
        
        request = self.factory.post('/add-slot/', {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        })
        request.user = self.user
        request.POST = {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        }
        request.META = {}
        
        add_slot_from_search(request)
        
        mock_messages.info.assert_called_once()
        
        # get_object_or_404 se llama dos veces
        mock_get_object.side_effect = [mock_actividad, mock_bloque]
        
        # Mock timezone
        mock_now = MagicMock()
        mock_now.date.return_value = datetime(2025, 11, 18).date()  # Martes
        mock_now.weekday.return_value = 1
        mock_timezone.localtime.return_value = mock_now
        mock_timezone.make_aware = lambda x: x
        
        # No existe duplicado
        mock_horarios_part.objects.filter.return_value.exists.return_value = False
        
        # No hay conflictos (lista vacía)
        mock_horarios_part.objects.filter.return_value = []
        
        request = self.factory.post('/add-slot/', {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',  # Lunes
            'next': '/buscar/'
        })
        request.user = self.user
        request.POST = {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        }
        request.META = {}
        
        add_slot_from_search(request)
        
        mock_horarios_part.objects.create.assert_called_once()
        mock_messages.success.assert_called_once()
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.get_object_or_404')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.timezone')
    @patch('searchActivities.views.redirect')
    def test_add_slot_duplicado(
        self, mock_redirect, mock_timezone, mock_participantes, 
        mock_get_object, mock_horarios_part, mock_messages
    ):
        """Intentar agregar slot duplicado"""
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        mock_actividad = MagicMock()
        mock_bloque = MagicMock()
        mock_bloque.hora_inicio = time(10, 0)
        mock_bloque.hora_fin = time(11, 0)
        
        mock_get_object.side_effect = [mock_actividad, mock_bloque]
        
        mock_now = MagicMock()
        mock_now.date.return_value = datetime(2025, 11, 18).date()
        mock_timezone.localtime.return_value = mock_now
        mock_timezone.make_aware = lambda x: x
        
        # Ya existe
        mock_horarios_part.objects.filter.return_value.exists.return_value = True
        
        request = self.factory.post('/add-slot/', {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        })
        request.user = self.user
        request.POST = {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        }
        request.META = {}
        
        add_slot_from_search(request)
        
        mock_messages.info.assert_called_once()
        self.assertIn('ya está', mock_messages.info.call_args[0][1])
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.get_object_or_404')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.timezone')
    @patch('searchActivities.views.redirect')
    def test_add_slot_conflicto_horario(
        self, mock_redirect, mock_timezone, mock_participantes, 
        mock_get_object, mock_horarios_part, mock_messages
    ):
        """Detectar conflicto con otro horario"""
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        mock_actividad = MagicMock()
        mock_bloque = MagicMock()
        mock_bloque.hora_inicio = time(10, 0)
        mock_bloque.hora_fin = time(11, 0)
        
        mock_get_object.side_effect = [mock_actividad, mock_bloque]
        
        mock_now = MagicMock()
        mock_now.date.return_value = datetime(2025, 11, 18).date()
        mock_timezone.localtime = lambda dt=None: mock_now if dt is None else dt
        mock_timezone.make_aware = lambda x: x
        
        # No es duplicado
        mock_filter_exists = MagicMock()
        mock_filter_exists.exists.return_value = False
        
        # Pero hay conflicto
        mock_existing = MagicMock()
        mock_existing_dt_inicio = MagicMock()
        mock_existing_dt_inicio.weekday.return_value = 0  # Lunes
        mock_existing_dt_inicio.time.return_value = time(10, 30)
        mock_existing_dt_inicio.timetz.return_value.replace.return_value = time(10, 30)
        
        mock_existing_dt_fin = MagicMock()
        mock_existing_dt_fin.time.return_value = time(11, 30)
        mock_existing_dt_fin.timetz.return_value.replace.return_value = time(11, 30)
        
        mock_existing.fecha_inicio = mock_existing_dt_inicio
        mock_existing.fecha_fin = mock_existing_dt_fin
        
        def filter_side_effect(*args, **kwargs):
            if 'fecha_inicio__time' in kwargs:
                return mock_filter_exists
            return [mock_existing]
        
        mock_horarios_part.objects.filter.side_effect = filter_side_effect
        
        request = self.factory.post('/add-slot/', {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        })
        request.user = self.user
        request.POST = {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        }
        request.META = {}
        
        add_slot_from_search(request)
        
        mock_messages.error.assert_called_once()
        self.assertIn('cruza', mock_messages.error.call_args[0][1])
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.get_object_or_404')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.timezone')
    @patch('searchActivities.views.redirect')
    def test_add_slot_integrity_error(
        self, mock_redirect, mock_timezone, mock_participantes, 
        mock_get_object, mock_horarios_part, mock_messages
    ):
        """Manejar IntegrityError al insertar"""
        from django.db import IntegrityError
        
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        mock_actividad = MagicMock()
        mock_actividad.nombre = "Yoga"
        mock_bloque = MagicMock()
        mock_bloque.hora_inicio = time(10, 0)
        mock_bloque.hora_fin = time(11, 0)
        
        mock_get_object.side_effect = [mock_actividad, mock_bloque]
        
        mock_now = MagicMock()
        mock_now.date.return_value = datetime(2025, 11, 18).date()
        mock_timezone.localtime.return_value = mock_now
        mock_timezone.make_aware = lambda x: x
        
        mock_filter_result = MagicMock()
        mock_filter_result.exists.return_value = False
        mock_horarios_part.objects.filter.return_value = mock_filter_result
        
        # Lanzar IntegrityError al crear
        mock_horarios_part.objects.create.side_effect = IntegrityError
        
        request = self.factory.post('/add-slot/', {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        })
        request.user = self.user
        request.POST = {
            'actividad_id': '1',
            'bloque_id': '1',
            'dia_idx': '0',
            'next': '/buscar/'
        }
        request.META = {}
        
        add_slot_from_search(request)
        
        mock_messages.info.assert_called_once()
    
    @patch('searchActivities.views.messages')
    @patch('searchActivities.views.HorariosParticipante')
    @patch('searchActivities.views.get_object_or_404')
    @patch('searchActivities.views.Participantes')
    @patch('searchActivities.views.timezone')
    @patch('searchActivities.views.redirect')
    def test_add_slot_exception_generica(
        self, mock_redirect, mock_timezone, mock_participantes, 
        mock_get_object, mock_horarios_part, mock_messages
    ):
        """Manejar excepción genérica"""
        mock_participante = MagicMock()
        mock_participantes.objects.get.return_value = mock_participante
        
        mock_actividad = MagicMock()
        mock_actividad.nombre = "Yoga"
        mock_bloque = MagicMock()
        mock_bloque.hora_inicio = time(10, 0)
        mock_bloque.hora_fin = time(11, 0)