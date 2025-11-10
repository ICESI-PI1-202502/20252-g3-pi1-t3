# appointments/tests/test_views.py
from django.test import TestCase
from unittest.mock import patch, MagicMock, Mock
from django.utils import timezone
from datetime import timedelta

class TestAppointmentsViews(TestCase):
    """Tests para vistas de citas"""
    
    databases = '__all__'
    
    @patch('appointments.views.get_object_or_404')
    @patch('appointments.views.Citas.objects')
    @patch('appointments.views.render')
    def test_listar_citas_usuario(self, mock_render, mock_citas, mock_get):
        """Debe listar citas del usuario (my_appointments)"""
        from appointments.views import my_appointments
        
        # Mock participante
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_get.return_value = mock_participante
        
        # Mock queryset
        mock_queryset = MagicMock()
        mock_citas.objects.select_related.return_value.filter.return_value.order_by.return_value = []
        
        # Mock request
        request = MagicMock()
        request.user.id = 1
        request.user.is_authenticated = True
        
        my_appointments(request)
        
        mock_get.assert_called()
        mock_render.assert_called_once()
    
    @patch('appointments.views.get_object_or_404')
    @patch('appointments.views.now')
    @patch('appointments.views.Citas.objects')
    @patch('appointments.views.HorariosParticipante.objects')
    @patch('appointments.views.HistorialCitas.objects')
    @patch('appointments.views.EstadosCita.objects')
    @patch('appointments.views.AgendaPsicologos.objects')
    @patch('appointments.views.messages')
    @patch('appointments.views.redirect')
    def test_crear_cita(self, mock_redirect, mock_messages, mock_agenda, 
                       mock_estados, mock_historial, mock_horarios, 
                       mock_citas, mock_now, mock_get):
        """Debe crear cita correctamente"""
        from appointments.views import create_appointment
        
        # Mock tiempo
        mock_now.return_value = timezone.now()
        
        # Mock participantes
        estudiante = MagicMock()
        estudiante.id_participante = 1
        estudiante.nombre = "Juan"
        estudiante.apellido = "Pérez"
        
        profesional = MagicMock()
        profesional.id_participante = 2
        profesional.nombre = "Dr. Smith"
        
        mock_get.side_effect = [estudiante, profesional]
        
        # Mock slot
        mock_slot = MagicMock()
        mock_slot.fecha_inicio = timezone.now() + timedelta(days=1)
        mock_slot.fecha_fin = timezone.now() + timedelta(days=1, hours=1)
        mock_slot.estado_slot = "DISPONIBLE"
        mock_agenda.objects.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = mock_slot
        
        # Mock cita creada
        cita_mock = MagicMock()
        cita_mock.id_cita = 1
        mock_citas.objects.create.return_value = cita_mock
        
        # Mock estado
        estado_mock = MagicMock()
        mock_estados.objects.create.return_value = estado_mock
        
        # Mock request POST
        request = MagicMock()
        request.method = 'POST'
        request.user.id = 1
        fecha_futura = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        request.POST = {
            'profesional_id': '2',
            'fecha': fecha_futura,
            'motivo': 'Test',
            'observaciones': 'Observaciones de prueba'
        }
        
        create_appointment(request)
        
        mock_citas.objects.create.assert_called_once()
        mock_redirect.assert_called()
    
    @patch('appointments.views.get_object_or_404')
    @patch('appointments.views.now')
    @patch('appointments.views.AgendaPsicologos.objects')
    @patch('appointments.views.HorariosParticipante.objects')
    @patch('appointments.views.HistorialCitas.objects')
    @patch('appointments.views.messages')
    @patch('appointments.views.redirect')
    def test_cancelar_cita(self, mock_redirect, mock_messages, mock_historial, 
                          mock_horarios, mock_agenda, mock_now, mock_get):
        """Debe cancelar cita y liberar slot"""
        from appointments.views import appointment_cancel
        
        mock_now.return_value = timezone.now()
        
        # Mock participante
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        
        # Mock cita
        cita_mock = MagicMock()
        cita_mock.id_cita = 1
        cita_mock.participantes_id_participante_id = 1
        cita_mock.participantes_id_participante2_id = 2
        cita_mock.agenda_psicologos_id_agenda_slot_id = 5
        
        mock_get.side_effect = [mock_participante, cita_mock]
        
        # Mock para liberar slot
        mock_agenda.objects.filter.return_value.update.return_value = 1
        
        # Mock request
        request = MagicMock()
        request.user.id = 1
        request.user.is_superuser = False
        
        appointment_cancel(request, id=1)
        
        # Verificar que se liberó el slot
        mock_agenda.objects.filter.assert_called_with(pk=5)
        mock_horarios.objects.filter.return_value.delete.assert_called_once()
        mock_historial.objects.create.assert_called_once()
        mock_redirect.assert_called()
    
    @patch('appointments.views.get_object_or_404')
    @patch('appointments.views.Citas.objects')
    @patch('appointments.views.render')
    def test_ver_agenda(self, mock_render, mock_citas, mock_get):
        """Debe mostrar agenda de citas (my_appointments)"""
        from appointments.views import my_appointments
        
        # Mock participante
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_get.return_value = mock_participante
        
        # Mock citas
        mock_citas.objects.select_related.return_value.filter.return_value.order_by.return_value = []
        
        # Mock request
        request = MagicMock()
        request.user.id = 1
        
        my_appointments(request)
        
        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        self.assertEqual(args[1], 'appointments/list.html')


class TestAppointmentsHelpers(TestCase):
    """Tests para helpers de citas"""
    
    @patch('appointments.views.AgendaPsicologos.objects')
    def test_obtener_slots_disponibles(self, mock_agenda):
        """Debe obtener slots disponibles (_decide_slot_or_duration)"""
        from appointments.views import _decide_slot_or_duration
        from datetime import datetime
        
        # Mock profesional
        profesional = MagicMock()
        profesional.id_participante = 1
        
        # Mock slot disponible
        mock_slot = MagicMock()
        mock_slot.fecha_inicio = timezone.now()
        mock_slot.fecha_fin = timezone.now() + timedelta(hours=1)
        mock_slot.estado_slot = "DISPONIBLE"
        mock_slot.lugar = "Consultorio 1"
        
        mock_agenda.objects.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = mock_slot
        
        decision = _decide_slot_or_duration(
            profesional=profesional,
            inicio=timezone.now()
        )
        
        self.assertIsNotNone(decision)
        self.assertEqual(decision.slot, mock_slot)
    
    def test_validar_fecha_futura(self):
        """Debe validar fechas futuras (_parse_dt_local)"""
        from appointments.views import _parse_dt_local
        from datetime import datetime
        
        # Fecha ISO válida (futura)
        fecha_futura = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        resultado = _parse_dt_local(fecha_futura)
        
        self.assertIsNotNone(resultado)
        self.assertGreater(resultado, timezone.now())
        
        # Fecha inválida
        resultado_invalido = _parse_dt_local("fecha-invalida")
        self.assertIsNone(resultado_invalido)
    
    @patch('appointments.views.HorariosParticipante.objects')
    def test_contar_citas_pendientes(self, mock_horarios):
        """Debe verificar solapamientos (_assert_no_overlap)"""
        from appointments.views import _assert_no_overlap
        from django.core.exceptions import ValidationError
        
        participante = MagicMock()
        participante.nombre = "Juan"
        participante.apellido = "Pérez"
        
        inicio = timezone.now()
        fin = inicio + timedelta(hours=1)
        
        # Caso sin conflicto
        mock_horarios.objects.filter.return_value.filter.return_value.exists.return_value = False
        
        try:
            _assert_no_overlap(participante=participante, inicio=inicio, fin=fin)
        except ValidationError:
            self.fail("No debería lanzar ValidationError cuando no hay conflicto")
        
        # Caso con conflicto
        mock_horarios.objects.filter.return_value.filter.return_value.exists.return_value = True
        
        with self.assertRaises(ValidationError):
            _assert_no_overlap(participante=participante, inicio=inicio, fin=fin)