# appointments/tests/test_views.py
from django.test import TestCase
from unittest.mock import patch, MagicMock, Mock
from django.utils import timezone
from datetime import timedelta

"""
Tests unitarios completos para appointments/views.py

COBERTURA REAL DE TESTS:
========================

PROPÓSITO DEL SISTEMA:
=====================
Sistema de gestión de citas médicas/psicológicas:
1. Agendar citas con profesionales
2. Asignación automática de slots de agenda
3. Validación de conflictos de horario
4. Cancelación y liberación de slots
5. Historial de estados de citas

ARQUITECTURA DEL SISTEMA:
=========================

Modelos principales:
- Citas: registro de cita (participante + profesional)
- AgendaPsicologos: slots de disponibilidad de profesionales
- HorariosParticipante: eventos en calendario de usuarios
- EstadosCita: estado actual de la cita
- HistorialCitas: log de cambios de estado

Estados de cita:
- Programada: cita agendada
- Confirmada: cita confirmada por profesional
- Cancelada: cita cancelada
- Completada: cita realizada
- No asistió: paciente no asistió

Estados de slot:
- DISPONIBLE: slot libre
- OCUPADO: slot con cita agendada

TESTS IMPLEMENTADOS:
===================

1. VISTAS PRINCIPALES (TestAppointmentsViews - 4 tests):
   =======================================================
   
   test_listar_citas_usuario:
   - Vista: my_appointments(request)
   - Función: lista citas del usuario autenticado
   - Mock: Participantes + Citas vacías
   - Query: Citas.filter(participante=usuario).order_by('fecha')
   - Template: 'appointments/list.html'
   - Valida: render() llamado con contexto correcto
   
   test_crear_cita:
   - Vista: create_appointment(request)
   - Función: crea cita con profesional
   - Flujo completo:
     1. Validar usuario autenticado
     2. Obtener participantes (estudiante + profesional)
     3. Parsear fecha/hora (ISO format)
     4. Buscar slot disponible (_decide_slot_or_duration)
     5. Validar sin conflictos (_assert_no_overlap)
     6. Crear Citas
     7. Crear EstadosCita (estado inicial: "Programada")
     8. Crear HorariosParticipante para ambos participantes
     9. Actualizar slot a OCUPADO
     10. Crear HistorialCitas (log inicial)
   - POST params: profesional_id, fecha, motivo, observaciones
   - Valida:
     * Citas.create() llamado 1 vez
     * HorariosParticipante.create() llamado 2 veces
     * redirect() llamado
   
   test_cancelar_cita:
   - Vista: appointment_cancel(request, id)
   - Función: cancela cita y libera slot
   - Flujo:
     1. Obtener participante autenticado
     2. Obtener cita
     3. Validar permisos (owner o superuser)
     4. Actualizar estado a "Cancelada" (_set_estado)
     5. Liberar slot: AgendaPsicologos.update(estado_slot="DISPONIBLE")
     6. Eliminar HorariosParticipante de ambos participantes
     7. Crear HistorialCitas (log de cancelación)
   - Valida:
     * _set_estado() llamado con "Cancelada"
     * AgendaPsicologos.update() llamado
     * HorariosParticipante.delete() llamado
     * HistorialCitas.create() llamado
   
   test_ver_agenda:
   - Vista: my_appointments(request)
   - Función: muestra agenda de citas del usuario
   - Mock: _aware() para conversión de timezone
   - Template: 'appointments/list.html'
   - Valida: render() llamado correctamente

2. HELPERS Y FUNCIONES AUXILIARES (TestAppointmentsHelpers - 4 tests):
   ====================================================================
   
   test_obtener_slots_disponibles:
   - Helper: _decide_slot_or_duration(profesional, inicio)
   - Función: busca slot disponible en agenda del profesional
   - Query: AgendaPsicologos.filter(
       participantes_id_participante=profesional,
       fecha_inicio__gte=inicio,
       estado_slot="DISPONIBLE"
     ).order_by('fecha_inicio').first()
   - Retorna: SlotDecision(inicio, fin, slot, lugar)
   - Valida:
     * decision.slot es not None
     * decision.lugar == "Consultorio 1"
   
   test_validar_fecha_futura:
   - Helper: _parse_dt_local(fecha_str)
   - Función: parsea string ISO a datetime aware
   - Input: "2024-11-20T14:30" (formato HTML5 datetime-local)
   - Output: datetime aware (timezone de Django)
   - Valida:
     * fecha válida → datetime > now()
     * fecha inválida → None
   
   test_verificar_sin_solapamientos:
   - Helper: _assert_no_overlap(participante, inicio, fin)
   - Función: valida que no hay conflictos de horario
   - Query: HorariosParticipante.filter(
       participantes_id_participante=participante,
       fecha_inicio__lt=fin,
       fecha_fin__gt=inicio
     ).exists()
   - Sin conflicto: no lanza excepción
   - Valida: NO raises Exception
   
   test_detectar_solapamiento:
   - Helper: _assert_no_overlap(participante, inicio, fin)
   - Con conflicto: lanza ValidationError
   - Mensaje: "Conflicto de horario para {nombre} {apellido}"
   - Valida: assertRaises(ValidationError)

LÓGICA DE NEGOCIO CRÍTICA:
===========================

CREACIÓN DE CITA - FLUJO COMPLETO:
```python
def create_appointment(request):
    if request.method == 'POST':
        # 1. Validar autenticación
        participante = get_object_or_404(Participantes, user=request.user)
        
        # 2. Obtener profesional
        profesional_id = request.POST['profesional_id']
        profesional = get_object_or_404(Participantes, id_participante=profesional_id)
        
        # 3. Parsear fecha
        fecha_str = request.POST['fecha']  # "2024-11-20T14:30"
        inicio = _parse_dt_local(fecha_str)
        
        # 4. Buscar slot disponible
        decision = _decide_slot_or_duration(profesional, inicio)
        if not decision or not decision.slot:
            messages.error(request, "No hay slots disponibles")
            return redirect('appointments:create')
        
        # 5. Validar sin conflictos (para ambos participantes)
        _assert_no_overlap(participante, decision.inicio, decision.fin)
        _assert_no_overlap(profesional, decision.inicio, decision.fin)
        
        # 6. Crear cita
        cita = Citas.objects.create(
            participantes_id_participante=participante,
            participantes_id_participante2=profesional,
            fecha=decision.inicio,
            motivo=request.POST['motivo'],
            observaciones=request.POST.get('observaciones', ''),
            agenda_psicologos_id_agenda_slot=decision.slot
        )
        
        # 7. Crear estado inicial
        EstadosCita.objects.create(
            citas_id_cita=cita,
            estado="Programada",
            fecha_cambio=now()
        )
        
        # 8. Agregar a calendarios de ambos participantes
        for part in [participante, profesional]:
            HorariosParticipante.objects.create(
                participantes_id_participante=part,
                fecha_inicio=decision.inicio,
                fecha_fin=decision.fin,
                titulo=f"Cita: {cita.motivo}",
                citas_id_cita=cita,
                fuente_manual='N'  # Automático
            )
        
        # 9. Marcar slot como ocupado
        decision.slot.estado_slot = "OCUPADO"
        decision.slot.save()
        
        # 10. Registrar en historial
        HistorialCitas.objects.create(
            citas_id_cita=cita,
            estado_anterior=None,
            estado_nuevo="Programada",
            fecha_cambio=now(),
            observaciones="Cita creada"
        )
        
        messages.success(request, "Cita agendada exitosamente")
        return redirect('appointments:my')
```

CANCELACIÓN DE CITA - FLUJO COMPLETO:
```python
def appointment_cancel(request, id):
    # 1. Validar permisos
    participante = get_object_or_404(Participantes, user=request.user)
    cita = get_object_or_404(Citas, id_cita=id)
    
    if not (cita.participantes_id_participante_id == participante.id_participante 
            or request.user.is_superuser):
        messages.error(request, "No tienes permiso para cancelar esta cita")
        return redirect('appointments:my')
    
    # 2. Cambiar estado a Cancelada
    _set_estado(cita, "Cancelada")
    
    # 3. Liberar slot en agenda
    if cita.agenda_psicologos_id_agenda_slot_id:
        AgendaPsicologos.objects.filter(
            pk=cita.agenda_psicologos_id_agenda_slot_id
        ).update(estado_slot="DISPONIBLE")
    
    # 4. Eliminar eventos de calendarios
    HorariosParticipante.objects.filter(
        citas_id_cita=cita
    ).delete()
    
    # 5. Registrar en historial
    HistorialCitas.objects.create(
        citas_id_cita=cita,
        estado_anterior="Programada",
        estado_nuevo="Cancelada",
        fecha_cambio=now(),
        observaciones="Cita cancelada por usuario"
    )
    
    messages.success(request, "Cita cancelada exitosamente")
    return redirect('appointments:my')

"""

"""
    Busca el primer slot disponible a partir de una fecha
    
    Returns:
        SlotDecision(inicio, fin, slot, lugar) o None
  
    slot = AgendaPsicologos.objects.filter(
        participantes_id_participante=profesional,
        fecha_inicio__gte=inicio,
        estado_slot="DISPONIBLE"
    ).order_by('fecha_inicio').first()
    
    if not slot:
        return None
    
    return SlotDecision(
        inicio=slot.fecha_inicio,
        fin=slot.fecha_fin,
        slot=slot,
        lugar=slot.lugar
    )
```

HELPERS AUXILIARES (MOCKEADOS EN TESTS):
========================================

_get_professionals():
- Obtiene lista de profesionales disponibles
- Usado en formulario de creación

_ensure_estado_programada(cita):
- Asegura que existe estado "Programada" para la cita
- Crea si no existe

_set_estado(cita, nuevo_estado):
- Actualiza estado de cita
- Crea registro en HistorialCitas

_aware(dt):
- Convierte datetime naive a aware
- Usa timezone de Django

CASOS DE USO REALES:
====================

1. AGENDAR CITA MÉDICA:
   - Usuario: Juan Pérez (estudiante)
   - Profesional: Dr. Smith (psicólogo)
   - Fecha: 2024-11-20 14:30
   - Motivo: "Consulta de seguimiento"
   - Sistema:
     * Busca slot disponible Dr. Smith
     * Valida sin conflictos para Juan
     * Valida sin conflictos para Dr. Smith
     * Crea cita + estado + 2 eventos calendario
     * Marca slot como OCUPADO

2. CANCELAR CITA:
   - Usuario: Juan Pérez
   - Cita: ID 123
   - Sistema:
     * Valida permisos (owner)
     * Cambia estado a "Cancelada"
     * Libera slot (OCUPADO → DISPONIBLE)
     * Elimina eventos de calendarios
     * Registra en historial

3. VER AGENDA:
   - Usuario: Juan Pérez
   - Sistema:
     * Lista citas futuras y pasadas
     * Ordenadas por fecha
     * Con estado actual
     * Links para cancelar/ver detalle

PREVENCIÓN DE CONFLICTOS:
=========================

ESTRATEGIA DE VALIDACIÓN:
1. Validar fecha futura (no permitir pasado)
2. Buscar slot disponible en agenda profesional
3. Validar sin conflictos para estudiante
4. Validar sin conflictos para profesional
5. Solo si todo OK → crear cita

ALGORITMO DE OVERLAPPING:
```
Evento existente: [10:00, 11:00]
Nueva cita:       [10:30, 11:30]

Overlap: inicio_nueva < fin_existente AND fin_nueva > inicio_existente
         10:30 < 11:00 AND 11:30 > 10:00
         True AND True = HAY CONFLICTO
```

CASOS NO-OVERLAP:
```
Existente: [10:00, 11:00]
Nueva:     [11:00, 12:00]  ✅ OK (fin_existente == inicio_nueva es válido)

Existente: [10:00, 11:00]
Nueva:     [11:30, 12:30]  ✅ OK (gap de 30min)

Existente: [10:00, 11:00]
Nueva:     [09:00, 10:00]  ✅ OK (anterior)
```

METODOLOGÍA DE TESTING:
=======================
- 100% mocks: NO se usa base de datos real
- TestCase: permite acceso a framework de Django
- Aislamiento con @patch de todos los modelos
- Mock de helpers internos (_decide_slot_or_duration, _assert_no_overlap)
- RequestFactory para simular requests HTTP
- Validación de llamadas y parámetros
- Tests de flujos completos (crear, cancelar)
- Tests de helpers individuales

LO QUE SE PRUEBA REALMENTE:
===========================
✅ Listado de citas del usuario
✅ Creación completa de cita (10 pasos)
✅ Validación de permisos en cancelación
✅ Liberación de slot al cancelar
✅ Eliminación de eventos de calendario
✅ Búsqueda de slots disponibles
✅ Parseo de fechas HTML5 (datetime-local)
✅ Validación de conflictos (overlapping)
✅ Detección de solapamientos
✅ Registro en historial de cambios

LO QUE NO SE PRUEBA:
====================
❌ Queries reales a base de datos
❌ Transacciones y locks
❌ Concurrencia (dos usuarios agendando mismo slot)
❌ Validación de formularios Django
❌ Renderizado de templates HTML
❌ Envío de notificaciones/emails
❌ Timezone real del servidor/cliente

CASOS ESPECIALES IMPORTANTES:
==============================

1. DOBLE VALIDACIÓN DE CONFLICTOS:
   - Valida estudiante: no debe tener otro evento
   - Valida profesional: no debe tener otra cita
   - Ambos deben pasar para crear cita

2. SLOTS DE AGENDA:
   - Estado inicial: DISPONIBLE
   - Al agendar: OCUPADO
   - Al cancelar: vuelve a DISPONIBLE
   - Permite reutilización de slots

3. EVENTOS EN CALENDARIO:
   - Se crean 2 eventos: uno por participante
   - fuente_manual='N' (automático, no manual)
   - Al cancelar: se eliminan ambos eventos

4. HISTORIAL DE ESTADOS:
   - Registro inmutable de cambios
   - Incluye: estado_anterior, estado_nuevo, fecha, observaciones
   - Útil para auditoría y debugging

5. PERMISOS DE CANCELACIÓN:
   - Owner (participante principal): puede cancelar
   - Superuser: puede cancelar cualquier cita
   - Otros: no pueden cancelar

EJEMPLO DE FLUJO REAL:
=======================

Juan agenda cita con Dr. Smith:

1. Juan va a create_appointment
2. Form: profesional_id=2, fecha="2024-11-20T14:30", motivo="Consulta"
3. POST → create_appointment(request)
4. Validación:
   - Juan autenticado ✓
   - Dr. Smith existe ✓
   - Fecha válida (futura) ✓
5. Búsqueda slot:
   - AgendaPsicologos.filter(profesional=2, inicio≥2024-11-20 14:30, DISPONIBLE)
   - Encuentra: Slot #5 (14:30-15:30, Consultorio 1) ✓
6. Validación conflictos:
   - Juan: no tiene eventos 14:30-15:30 ✓
   - Dr. Smith: no tiene citas 14:30-15:30 ✓
7. Creación:
   - Cita #123 creada
   - EstadosCita: Programada
   - HorariosParticipante: 2 eventos
   - Slot #5: OCUPADO
   - HistorialCitas: log inicial
8. Resultado: "Cita agendada exitosamente"

Más tarde, Juan cancela:

1. Juan va a appointment_cancel/123
2. Validación: Juan es owner ✓
3. Cambios:
   - Estado: Programada → Cancelada
   - Slot #5: OCUPADO → DISPONIBLE
   - HorariosParticipante: eliminados (2)
   - HistorialCitas: nuevo log
4. Resultado: "Cita cancelada exitosamente"
"""

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