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
        
        # Mock queryset vacío
        mock_queryset = MagicMock()
        mock_queryset.__iter__ = Mock(return_value=iter([]))
        mock_citas.select_related.return_value.filter.return_value.order_by.return_value = mock_queryset
        
        # Mock request
        request = MagicMock()
        request.user.id = 1
        request.user.is_authenticated = True
        
        my_appointments(request)
        
        mock_get.assert_called()
        mock_render.assert_called_once()
    
    @patch('appointments.views._get_professionals')  # ✅ Mock del helper
    @patch('appointments.views.get_object_or_404')
    @patch('appointments.views.now')
    @patch('appointments.views.Citas.objects')
    @patch('appointments.views.HorariosParticipante.objects')
    @patch('appointments.views.HistorialCitas.objects')
    @patch('appointments.views.EstadosCita.objects')
    @patch('appointments.views.AgendaPsicologos.objects')
    @patch('appointments.views.messages')
    @patch('appointments.views.redirect')
    @patch('appointments.views._decide_slot_or_duration')  # ✅ Mock del helper
    @patch('appointments.views._assert_no_overlap')  # ✅ Mock del helper
    def test_crear_cita(self, mock_assert_overlap, mock_decide_slot, mock_redirect, 
                       mock_messages, mock_agenda, mock_estados, mock_historial, 
                       mock_horarios, mock_citas, mock_now, mock_get, mock_get_profs):
        """Debe crear cita correctamente"""
        from appointments.views import create_appointment, SlotDecision
        from django.test import RequestFactory
        
        # Mock tiempo
        ahora = timezone.now()
        mock_now.return_value = ahora
        
        # Mock lista de profesionales
        mock_get_profs.return_value = [{"id": 2, "nombre": "Dr. Smith"}]
        
        # Mock participantes
        estudiante = MagicMock()
        estudiante.id_participante = 1
        estudiante.nombre = "Juan"
        estudiante.apellido = "Pérez"
        
        profesional = MagicMock()
        profesional.id_participante = 2
        profesional.nombre = "Dr. Smith"
        
        mock_get.side_effect = [estudiante, profesional]
        
        # Mock slot decision
        mock_slot = MagicMock()
        mock_slot.fecha_inicio = ahora + timedelta(days=1)
        mock_slot.fecha_fin = ahora + timedelta(days=1, hours=1)
        mock_slot.estado_slot = "DISPONIBLE"
        
        decision = SlotDecision(
            inicio=mock_slot.fecha_inicio,
            fin=mock_slot.fecha_fin,
            slot=mock_slot,
            lugar="Consultorio 1"
        )
        mock_decide_slot.return_value = decision
        
        # Mock que no hay overlap
        mock_assert_overlap.return_value = None
        
        # Mock cita creada
        cita_mock = MagicMock()
        cita_mock.id_cita = 1
        mock_citas.create.return_value = cita_mock
        
        # Mock estado
        estado_mock = MagicMock()
        mock_estados.create.return_value = estado_mock
        
        # Mock request POST
        request = RequestFactory().post('/appointments/create/', {
            'profesional_id': '2',
            'fecha': (ahora + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'motivo': 'Test',
            'observaciones': 'Observaciones de prueba'
        })
        request.user = MagicMock(id=1, is_authenticated=True)
        
        create_appointment(request)
        
        # Verificaciones
        mock_citas.create.assert_called_once()
        self.assertEqual(mock_horarios.create.call_count, 2)  # Estudiante + Profesional
        mock_redirect.assert_called()
    
    @patch('appointments.views.get_object_or_404')
    @patch('appointments.views.now')
    @patch('appointments.views.AgendaPsicologos.objects')
    @patch('appointments.views.HorariosParticipante.objects')
    @patch('appointments.views.HistorialCitas.objects')
    @patch('appointments.views._ensure_estado_programada')  # ✅ Mock del helper
    @patch('appointments.views._set_estado')  # ✅ Mock del helper
    @patch('appointments.views.messages')
    @patch('appointments.views.redirect')
    def test_cancelar_cita(self, mock_redirect, mock_messages, mock_set_estado,
                          mock_ensure_estado, mock_historial, mock_horarios, 
                          mock_agenda, mock_now, mock_get):
        """Debe cancelar cita y liberar slot"""
        from appointments.views import appointment_cancel
        
        ahora = timezone.now()
        mock_now.return_value = ahora
        
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
        
        # Mock queryset para update
        mock_queryset_update = MagicMock()
        mock_queryset_update.update.return_value = 1
        mock_agenda.filter.return_value = mock_queryset_update
        
        # Mock queryset para delete
        mock_queryset_delete = MagicMock()
        mock_queryset_delete.delete.return_value = (2, {'HorariosParticipante': 2})
        mock_horarios.filter.return_value = mock_queryset_delete
        
        # Mock request
        from django.test import RequestFactory
        request = RequestFactory().post('/appointments/cancel/1/')
        request.user = MagicMock(id=1, is_superuser=False, is_authenticated=True)
        
        appointment_cancel(request, id=1)
        
        # Verificaciones
        mock_set_estado.assert_called_once_with(cita_mock, "Cancelada")
        mock_agenda.filter.assert_called_once_with(pk=5)
        mock_queryset_update.update.assert_called_once_with(estado_slot="DISPONIBLE")
        mock_horarios.filter.assert_called_once()
        mock_queryset_delete.delete.assert_called_once()
        mock_historial.create.assert_called_once()
        mock_redirect.assert_called()
    
    @patch('appointments.views.get_object_or_404')
    @patch('appointments.views.Citas.objects')
    @patch('appointments.views._aware')  # ✅ Mock del helper
    @patch('appointments.views.render')
    def test_ver_agenda(self, mock_render, mock_aware, mock_citas, mock_get):
        """Debe mostrar agenda de citas (my_appointments)"""
        from appointments.views import my_appointments
        
        # Mock participante
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_get.return_value = mock_participante
        
        # Mock citas vacías
        mock_queryset = MagicMock()
        mock_queryset.__iter__ = Mock(return_value=iter([]))
        mock_citas.select_related.return_value.filter.return_value.order_by.return_value = mock_queryset
        
        # Mock _aware
        mock_aware.return_value = timezone.now()
        
        # Mock request
        from django.test import RequestFactory
        request = RequestFactory().get('/appointments/my/')
        request.user = MagicMock(id=1, is_authenticated=True)
        
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
        
        # Mock profesional
        profesional = MagicMock()
        profesional.id_participante = 1
        
        # Mock slot disponible
        mock_slot = MagicMock()
        mock_slot.fecha_inicio = timezone.now()
        mock_slot.fecha_fin = timezone.now() + timedelta(hours=1)
        mock_slot.estado_slot = "DISPONIBLE"
        mock_slot.lugar = "Consultorio 1"
        
        # ✅ Configurar correctamente el chain de métodos
        mock_queryset = MagicMock()
        mock_queryset.first.return_value = mock_slot
        
        mock_agenda.filter.return_value.filter.return_value.filter.return_value.order_by.return_value = mock_queryset
        
        decision = _decide_slot_or_duration(
            profesional=profesional,
            inicio=timezone.now()
        )
        
        self.assertIsNotNone(decision)
        self.assertIsNotNone(decision.slot)
        self.assertEqual(decision.lugar, "Consultorio 1")
    
    def test_validar_fecha_futura(self):
        """Debe validar fechas futuras (_parse_dt_local)"""
        from appointments.views import _parse_dt_local
        
        # Fecha ISO válida (futura)
        fecha_futura = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        resultado = _parse_dt_local(fecha_futura)
        
        self.assertIsNotNone(resultado)
        self.assertGreater(resultado, timezone.now())
        
        # Fecha inválida
        resultado_invalido = _parse_dt_local("fecha-invalida")
        self.assertIsNone(resultado_invalido)
    
    @patch('appointments.views.HorariosParticipante.objects')
    def test_verificar_sin_solapamientos(self, mock_horarios):
        """Debe verificar que no hay solapamientos (_assert_no_overlap)"""
        from appointments.views import _assert_no_overlap
        
        participante = MagicMock()
        participante.nombre = "Juan"
        participante.apellido = "Pérez"
        
        inicio = timezone.now()
        fin = inicio + timedelta(hours=1)
        
        # ✅ Caso sin conflicto
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        mock_horarios.filter.return_value.filter.return_value = mock_queryset
        
        # No debe lanzar excepción
        try:
            _assert_no_overlap(participante=participante, inicio=inicio, fin=fin)
        except Exception as e:
            self.fail(f"No debería lanzar excepción cuando no hay conflicto: {e}")
    
    @patch('appointments.views.HorariosParticipante.objects')
    def test_detectar_solapamiento(self, mock_horarios):
        """Debe detectar solapamientos (_assert_no_overlap)"""
        from appointments.views import _assert_no_overlap
        from django.core.exceptions import ValidationError
        
        participante = MagicMock()
        participante.nombre = "Juan"
        participante.apellido = "Pérez"
        
        inicio = timezone.now()
        fin = inicio + timedelta(hours=1)
        
        # ✅ Caso con conflicto
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_horarios.filter.return_value.filter.return_value = mock_queryset
        
        # Debe lanzar ValidationError
        with self.assertRaises(ValidationError) as context:
            _assert_no_overlap(participante=participante, inicio=inicio, fin=fin)
        
        self.assertIn("Conflicto de horario", str(context.exception))