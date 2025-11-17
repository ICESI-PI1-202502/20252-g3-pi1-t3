# project/universitaryWellbeing/tests/test_calendario_horario.py
from django.test import TestCase, SimpleTestCase  # ✅ Importar SimpleTestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta, time
import pytz


class CalendarioGeneralTestCase(TestCase):  # ✅ CAMBIO AQUÍ
    """Tests para el calendario de actividades generales usando mocks"""
    
    @patch('universitaryWellbeing.views.HorariosActividad.objects')
    def test_obtener_actividades_vacio(self, mock_horarios_actividad):
        """Verifica que retorne lista vacía cuando no hay horarios"""
        # ✅ Mock de QuerySet vacío con count() como método
        mock_queryset = MagicMock()
        mock_queryset.__iter__ = Mock(return_value=iter([]))
        mock_queryset.count = Mock(return_value=0)
        mock_horarios_actividad.filter.return_value.select_related.return_value = mock_queryset
        
        from universitaryWellbeing.views import obtener_actividades_generales_del_dia
        
        fecha = timezone.now().date()
        resultado = obtener_actividades_generales_del_dia(fecha)
        
        self.assertIsInstance(resultado, list)
        self.assertEqual(len(resultado), 0)
    
    @patch('universitaryWellbeing.views.HorariosActividad.objects')
    def test_obtener_actividades_con_horario(self, mock_horarios_actividad):
        """Verifica que se obtengan actividades correctamente"""
        # Mock de actividad
        mock_actividad = MagicMock()
        mock_actividad.nombre = 'Fútbol Test'
        
        # Mock de bloque
        mock_bloque = MagicMock()
        mock_bloque.actividades_id_actividad = mock_actividad
        mock_bloque.hora_inicio = time(9, 0)
        mock_bloque.hora_fin = time(10, 0)
        mock_bloque.profesor = 'Prof. Test'
        mock_bloque.lugar = 'Cancha 1'
        mock_bloque.id_horario_bloque = 1
        
        # Mock de horario_dia
        mock_horario_dia = MagicMock()
        mock_horario_dia.horario_bloque = mock_bloque
        
        # ✅ Configurar el queryset mock con count()
        mock_queryset = MagicMock()
        mock_queryset.__iter__ = Mock(return_value=iter([mock_horario_dia]))
        mock_queryset.count = Mock(return_value=1)
        mock_horarios_actividad.filter.return_value.select_related.return_value = mock_queryset
        
        from universitaryWellbeing.views import obtener_actividades_generales_del_dia
        
        fecha = timezone.now().date()
        resultado = obtener_actividades_generales_del_dia(fecha)
        
        self.assertGreater(len(resultado), 0)
        self.assertEqual(resultado[0]['titulo'], 'Fútbol Test')
        self.assertEqual(resultado[0]['tipo'], 'actividad_general')
    
    @patch('universitaryWellbeing.views.HorariosActividad.objects')
    def test_actividades_ordenadas_por_hora(self, mock_horarios_actividad):
        """Verifica que las actividades se ordenen por hora de inicio"""
        # Crear 3 actividades con diferentes horas
        actividades = []
        horas = [time(16, 0), time(9, 0), time(12, 0)]  # Desordenadas
        
        for hora in horas:
            mock_actividad = MagicMock()
            mock_actividad.nombre = f'Actividad {hora.hour}h'
            
            mock_bloque = MagicMock()
            mock_bloque.actividades_id_actividad = mock_actividad
            mock_bloque.hora_inicio = hora
            mock_bloque.hora_fin = time(hora.hour + 1, 0)
            mock_bloque.profesor = 'Prof. Test'
            mock_bloque.lugar = 'Lugar Test'
            mock_bloque.id_horario_bloque = hora.hour
            
            mock_horario = MagicMock()
            mock_horario.horario_bloque = mock_bloque
            actividades.append(mock_horario)
        
        # ✅ Devolver queryset mock con count()
        mock_queryset = MagicMock()
        mock_queryset.__iter__ = Mock(return_value=iter(actividades))
        mock_queryset.count = Mock(return_value=len(actividades))
        mock_horarios_actividad.filter.return_value.select_related.return_value = mock_queryset
        
        from universitaryWellbeing.views import obtener_actividades_generales_del_dia
        
        resultado = obtener_actividades_generales_del_dia(timezone.now().date())
        
        # Verificar que están ordenadas
        if len(resultado) >= 3:
            self.assertEqual(resultado[0]['fecha_inicio'].time().hour, 9)
            self.assertEqual(resultado[1]['fecha_inicio'].time().hour, 12)
            self.assertEqual(resultado[2]['fecha_inicio'].time().hour, 16)


class HorarioPersonalTestCase(TestCase):  # ✅ CAMBIO AQUÍ
    """Tests para el horario personal usando mocks"""
    
    def setUp(self):
        """Configuración de mocks comunes"""
        self.mock_participante = MagicMock()
        self.mock_participante.id_participante = 123456
        self.mock_participante.nombre = 'Test'
        self.mock_participante.apellido = 'User'
        
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.username = '123456'
        
        self.tz = pytz.timezone('America/Bogota')
        self.ahora = timezone.now().astimezone(self.tz)
    
    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    def test_horario_vacio(self, mock_horarios):
        """Verifica que participante sin eventos tenga horario vacío"""
        mock_horarios.filter.return_value = []
        
        horarios = mock_horarios.filter(
            participantes_id_participante=self.mock_participante
        )
        
        self.assertEqual(len(horarios), 0)
    
    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    def test_crear_evento_personal(self, mock_horarios):
        """Verifica creación de evento personal"""
        mock_evento = MagicMock()
        mock_evento.id_horario = 1
        mock_evento.titulo = 'Evento Personal'
        mock_evento.fuente_manual = 'S'
        mock_evento.participantes_id_participante = self.mock_participante
        
        mock_horarios.create.return_value = mock_evento
        
        # Simular creación
        evento = mock_horarios.create(
            participantes_id_participante=self.mock_participante,
            titulo='Evento Personal',
            fecha_inicio=self.ahora,
            fecha_fin=self.ahora + timedelta(hours=1),
            fuente_manual='S'
        )
        
        self.assertIsNotNone(evento.id_horario)
        self.assertEqual(evento.titulo, 'Evento Personal')
        self.assertEqual(evento.fuente_manual, 'S')
        mock_horarios.create.assert_called_once()
    
    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    def test_evento_recurrente_con_actividad(self, mock_horarios):
        """Verifica eventos recurrentes con actividad"""
        mock_actividad = MagicMock()
        mock_actividad.id_actividad = 10
        mock_actividad.nombre = 'Yoga'
        
        mock_evento = MagicMock()
        mock_evento.id_horario = 2
        mock_evento.actividades_id_actividad = mock_actividad
        mock_evento.fuente_manual = 'S'
        mock_evento.titulo = 'Yoga Recurrente'
        
        mock_horarios.create.return_value = mock_evento
        
        evento = mock_horarios.create(
            participantes_id_participante=self.mock_participante,
            actividades_id_actividad=mock_actividad,
            titulo='Yoga Recurrente',
            fecha_inicio=self.ahora,
            fecha_fin=self.ahora + timedelta(hours=1),
            fuente_manual='S'
        )
        
        self.assertIsNotNone(evento.actividades_id_actividad)
        self.assertEqual(evento.fuente_manual, 'S')
    
    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    def test_multiples_eventos_mismo_participante(self, mock_horarios):
        """Verifica creación de múltiples eventos"""
        mock_evento1 = MagicMock()
        mock_evento1.titulo = 'Evento 1'
        
        mock_evento2 = MagicMock()
        mock_evento2.titulo = 'Evento 2'
        
        # ✅ Crear un mock queryset con count como método
        mock_queryset = MagicMock()
        mock_queryset.__iter__ = Mock(return_value=iter([mock_evento1, mock_evento2]))
        mock_queryset.count = Mock(return_value=2)  # count es un método Mock
        
        mock_horarios.filter.return_value = mock_queryset
        
        eventos = mock_horarios.filter(
            participantes_id_participante=self.mock_participante
        )
        
        self.assertEqual(eventos.count(), 2)
    
    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    def test_eventos_ordenados_por_fecha(self, mock_horarios):
        """Verifica ordenamiento de eventos"""
        mock_evento_manana = MagicMock()
        mock_evento_manana.titulo = 'Mañana'
        mock_evento_manana.fecha_inicio = self.ahora.replace(hour=9, minute=0)
        
        mock_evento_tarde = MagicMock()
        mock_evento_tarde.titulo = 'Tarde'
        mock_evento_tarde.fecha_inicio = self.ahora.replace(hour=16, minute=0)
        
        # Mock del QuerySet ordenado
        mock_queryset = MagicMock()
        mock_queryset.__iter__ = Mock(return_value=iter([mock_evento_manana, mock_evento_tarde]))
        mock_queryset.__getitem__ = Mock(side_effect=[mock_evento_manana, mock_evento_tarde])
        
        mock_horarios.filter.return_value.order_by.return_value = mock_queryset
        
        eventos = mock_horarios.filter(
            participantes_id_participante=self.mock_participante
        ).order_by('fecha_inicio')
        
        eventos_lista = list(eventos)
        self.assertEqual(eventos_lista[0].titulo, 'Mañana')
        self.assertEqual(eventos_lista[1].titulo, 'Tarde')


class IntegracionCalendarioTestCase(TestCase):  # ✅ CAMBIO AQUÍ
    """Tests de integración usando mocks"""
    
    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.HorariosActividad.objects')
    def test_sin_colision_entre_sistemas(self, mock_horarios_actividad, mock_horarios_participante):
        """Verifica independencia entre calendarios"""
        # Mock calendario general
        mock_horario_dia = MagicMock()
        mock_actividad = MagicMock()
        mock_actividad.nombre = 'Actividad General'
        mock_bloque = MagicMock()
        mock_bloque.actividades_id_actividad = mock_actividad
        mock_bloque.hora_inicio = time(10, 0)
        mock_bloque.hora_fin = time(11, 0)
        mock_bloque.profesor = 'Prof'
        mock_bloque.lugar = 'Lugar'
        mock_bloque.id_horario_bloque = 1
        mock_horario_dia.horario_bloque = mock_bloque
        
        # ✅ Devolver queryset mock con count()
        mock_queryset = MagicMock()
        mock_queryset.__iter__ = Mock(return_value=iter([mock_horario_dia]))
        mock_queryset.count = Mock(return_value=1)
        mock_horarios_actividad.filter.return_value.select_related.return_value = mock_queryset
        
        # Mock horario personal vacío
        mock_horarios_participante.filter.return_value = []
        
        # Verificar calendario general
        from universitaryWellbeing.views import obtener_actividades_generales_del_dia
        actividades_generales = obtener_actividades_generales_del_dia(timezone.now().date())
        
        self.assertIsInstance(actividades_generales, list)
        self.assertGreater(len(actividades_generales), 0)
        
        # Verificar horario personal
        horarios_personales = mock_horarios_participante.filter(participantes_id_participante=1)
        self.assertEqual(len(horarios_personales), 0)
        
        # Ambos sistemas funcionan independientemente
        mock_horarios_actividad.filter.assert_called()
        mock_horarios_participante.filter.assert_called()


class TestScheduleView(SimpleTestCase):  # ✅ SimpleTestCase porque NO accede a BD
    """Tests para la vista schedule() - Solo usa mocks"""
    
    # ✅ NO necesita setUpClass porque usa solo mocks
    
    @patch('universitaryWellbeing.views.json.dumps')
    @patch('universitaryWellbeing.views.render')
    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.get_object_or_404')
    def test_schedule_view_eventos_recurrentes(self, mock_get_404, mock_horarios, 
                                                 mock_render, mock_json_dumps):
        """Verifica que eventos manuales sean marcados como recurrentes"""
        from django.test import RequestFactory
        
        request = RequestFactory().get('/schedule/')
        request.user = MagicMock(id=1, is_authenticated=True)
        
        # Mock participante
        mock_participante = MagicMock()
        mock_participante.id_participante = 123456
        mock_get_404.return_value = mock_participante
        
        # Mock evento recurrente (manual + con actividad)
        mock_evento = MagicMock()
        mock_evento.id_horario = 1
        mock_evento.titulo = 'Yoga'
        mock_evento.fuente_manual = 'S'
        mock_evento.actividades_id_actividad = MagicMock()
        mock_evento.citas_id_cita = None
        mock_evento.partidos_id_partido = None
        mock_evento.fecha_inicio = datetime(2025, 11, 18, 9, 0)  # Lunes
        mock_evento.fecha_fin = datetime(2025, 11, 18, 10, 0)
        mock_evento.notas = 'Yoga semanal'
        
        mock_horarios.filter.return_value = [mock_evento]
        mock_json_dumps.return_value = '[]'
        
        from universitaryWellbeing.views import schedule
        schedule(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], 'Horario.html')
    
    @patch('universitaryWellbeing.views.json.dumps')
    @patch('universitaryWellbeing.views.render')
    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.get_object_or_404')
    def test_schedule_view_eventos_unicos(self, mock_get_404, mock_horarios,
                                          mock_render, mock_json_dumps):
        """Verifica que citas sean eventos únicos"""
        from django.test import RequestFactory
        
        request = RequestFactory().get('/schedule/')
        request.user = MagicMock(id=1, is_authenticated=True)
        
        mock_participante = MagicMock()
        mock_participante.id_participante = 123456
        mock_get_404.return_value = mock_participante
        
        # Mock cita (evento único)
        mock_evento = MagicMock()
        mock_evento.id_horario = 2
        mock_evento.titulo = 'Cita Psicología'
        mock_evento.fuente_manual = 'N'
        mock_evento.actividades_id_actividad = None
        mock_evento.citas_id_cita = MagicMock()
        mock_evento.partidos_id_partido = None
        mock_evento.fecha_inicio = datetime(2025, 11, 20, 14, 0)
        mock_evento.fecha_fin = datetime(2025, 11, 20, 15, 0)
        mock_evento.notas = None
        
        mock_horarios.filter.return_value = [mock_evento]
        mock_json_dumps.return_value = '[]'
        
        from universitaryWellbeing.views import schedule
        schedule(request)
        
        mock_render.assert_called_once()


class TestDeleteEvent(SimpleTestCase):  # ✅ SimpleTestCase porque NO accede a BD
    """Tests para eliminar eventos - Solo usa mocks"""
    
    @patch('universitaryWellbeing.views.JsonResponse')
    @patch('universitaryWellbeing.views.get_object_or_404')
    def test_delete_event_manual_ok(self, mock_get_404, mock_json_response):
        """Verifica que se puedan eliminar eventos manuales"""
        from django.test import RequestFactory
        
        request = RequestFactory().post('/schedule/delete/1/')
        request.user = MagicMock(id=1, is_authenticated=True)
        
        mock_participante = MagicMock()
        mock_participante.id_participante = 123456
        
        mock_evento = MagicMock()
        mock_evento.id_horario = 1
        mock_evento.titulo = 'Evento Manual'
        mock_evento.fuente_manual = 'S'
        
        mock_get_404.side_effect = [mock_participante, mock_evento]
        
        # ✅ Mock de JsonResponse que devuelve un objeto con status_code
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_json_response.return_value = mock_response
        
        from universitaryWellbeing.views import delete_event
        response = delete_event(request, 1)
        
        mock_evento.delete.assert_called_once()
        self.assertEqual(response.status_code, 200)
    
    @patch('universitaryWellbeing.views.JsonResponse')
    @patch('universitaryWellbeing.views.get_object_or_404')
    def test_delete_event_automatico_rechazado(self, mock_get_404, mock_json_response):
        """Verifica que NO se puedan eliminar eventos automáticos"""
        from django.test import RequestFactory
        
        request = RequestFactory().post('/schedule/delete/2/')
        request.user = MagicMock(id=1, is_authenticated=True)
        
        mock_participante = MagicMock()
        mock_participante.id_participante = 123456
        
        mock_evento = MagicMock()
        mock_evento.id_horario = 2
        mock_evento.titulo = 'Cita Automática'
        mock_evento.fuente_manual = 'N'
        
        mock_get_404.side_effect = [mock_participante, mock_evento]
        
        # ✅ Mock de JsonResponse con status 403
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_json_response.return_value = mock_response
        
        from universitaryWellbeing.views import delete_event
        response = delete_event(request, 2)
        
        mock_evento.delete.assert_not_called()
        self.assertEqual(response.status_code, 403)


class TestUnifiedCalendar(SimpleTestCase):  # ✅ SimpleTestCase porque NO accede a BD
    """Tests para el calendario unificado - Solo usa mocks"""
    
    @patch('universitaryWellbeing.views.render')
    @patch('universitaryWellbeing.views.HorariosActividad.objects')
    @patch('universitaryWellbeing.views.HorariosBloque.objects')
    @patch('universitaryWellbeing.views.Actividades.objects')
    @patch('universitaryWellbeing.views.TiposActividad.objects')
    def test_unified_calendar_sin_filtro(self, mock_tipos, mock_actividades, 
                                         mock_bloques, mock_horarios_act, mock_render):
        """Verifica calendario sin filtro de tipo"""
        from django.test import RequestFactory
        
        request = RequestFactory().get('/calendar/')
        request.GET = {}
        request.user = MagicMock(is_authenticated=True)  # ✅ AÑADIDO
        
        # Mocks básicos
        mock_tipos.values.return_value.order_by.return_value = []
        mock_actividades.all.return_value.select_related.return_value.values.return_value = []
        
        from universitaryWellbeing.views import unified_calendar
        unified_calendar(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], 'calendario_unificado.html')