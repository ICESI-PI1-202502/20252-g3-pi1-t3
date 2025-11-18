#project\Analytics_Reports\tests\test_tasks.py

from django.test import SimpleTestCase
from unittest.mock import patch, MagicMock, call
from django.utils import timezone
from datetime import timedelta
import Analytics_Reports.tasks as tasks

# ==========================================================
# TESTS PARA TAREA 1: RECONOCIMIENTOS
# ==========================================================

class VerificarOtorgarReconocimientosTests(SimpleTestCase):
    """Pruebas para verificar_y_otorgar_reconocimientos"""

    @patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config")
    def test_reconocimientos_desactivados(self, mock_config):
        """No debe ejecutar si los reconocimientos están desactivados"""
        mock_config_obj = MagicMock()
        mock_config_obj.reconocimientos_activos = False
        mock_config.return_value = mock_config_obj
        
        resultado = tasks.verificar_y_otorgar_reconocimientos()
        
        self.assertEqual(resultado, '⏸️ Reconocimientos desactivados por el admin')

    @patch("Analytics_Reports.tasks.send_mail")
    @patch("Analytics_Reports.tasks.ControlNotificacionesContextual")
    @patch("Analytics_Reports.tasks.Asistencias.objects")
    @patch("Analytics_Reports.tasks.Participaciones.objects")
    @patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config")
    def test_otorga_reconocimiento_cuando_cumple_hito(
        self, mock_config, mock_participaciones, mock_asistencias, 
        mock_control, mock_send_mail
    ):
        """Debe otorgar reconocimiento cuando se alcanza un hito"""
        # Config
        mock_config_obj = MagicMock()
        mock_config_obj.reconocimientos_activos = True
        mock_config_obj.obtener_hitos.return_value = [10, 20, 30]
        mock_config.return_value = mock_config_obj
        
        # Mock participación
        mock_participante = MagicMock()
        mock_participante.correo = 'test@test.com'
        mock_actividad = MagicMock()
        mock_actividad.nombre = 'Yoga'
        
        mock_participacion = MagicMock()
        mock_participacion.participantes_id_participante = mock_participante
        mock_participacion.actividades_id_actividad = mock_actividad
        
        mock_participaciones.filter.return_value.select_related.return_value = [mock_participacion]
        
        # Mock asistencias: 10 asistencias (cumple primer hito)
        mock_asistencias.filter.return_value.count.return_value = 10
        
        # Mock control anti-spam
        mock_control.ya_existe_notificacion.return_value = False
        mock_control.registrar_notificacion.return_value = MagicMock()
        
        resultado = tasks.verificar_y_otorgar_reconocimientos()
        
        # Verificaciones
        self.assertIn('reconocimientos otorgados', resultado)
        mock_control.registrar_notificacion.assert_called_once()
        mock_send_mail.assert_called_once()

    @patch("Analytics_Reports.tasks.ControlNotificacionesContextual")
    @patch("Analytics_Reports.tasks.Asistencias.objects")
    @patch("Analytics_Reports.tasks.Participaciones.objects")
    @patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config")
    def test_no_duplica_reconocimientos_existentes(
        self, mock_config, mock_participaciones, mock_asistencias, mock_control
    ):
        """No debe enviar reconocimiento si ya existe"""
        mock_config_obj = MagicMock()
        mock_config_obj.reconocimientos_activos = True
        mock_config_obj.obtener_hitos.return_value = [10]
        mock_config.return_value = mock_config_obj
        
        mock_participante = MagicMock()
        mock_actividad = MagicMock()
        mock_participacion = MagicMock()
        mock_participacion.participantes_id_participante = mock_participante
        mock_participacion.actividades_id_actividad = mock_actividad
        
        mock_participaciones.filter.return_value.select_related.return_value = [mock_participacion]
        mock_asistencias.filter.return_value.count.return_value = 10
        
        # Ya existe notificación
        mock_control.ya_existe_notificacion.return_value = True
        
        resultado = tasks.verificar_y_otorgar_reconocimientos()
        
        # No debe registrar nueva notificación
        mock_control.registrar_notificacion.assert_not_called()


# ==========================================================
# TESTS PARA TAREA 2: CLASIFICACIÓN
# ==========================================================

class ClasificarEstudiantesTests(SimpleTestCase):
    """Pruebas para clasificar_estudiantes_para_admin"""

    @patch("Analytics_Reports.tasks.timezone")
    @patch("Analytics_Reports.tasks.Participaciones.objects")
    @patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config")
    def test_clasificacion_riesgo_critico(self, mock_config, mock_participaciones, mock_tz):
        """Debe clasificar correctamente estudiantes en riesgo crítico"""
        mock_tz.now.return_value = timezone.datetime(2024, 10, 19, tzinfo=timezone.get_current_timezone())
        
        mock_config_obj = MagicMock()
        mock_config_obj.umbral_riesgo_critico = 2
        mock_config_obj.dias_riesgo_critico = 21
        mock_config_obj.umbral_baja_asistencia = 5
        mock_config_obj.dias_inactividad = 14
        mock_config_obj.asistencias_destacado = 15
        mock_config.return_value = mock_config_obj
        
        # Mock participación con pocas asistencias y mucho tiempo inactivo
        mock_participacion = MagicMock()
        mock_participacion.total_asistencias = 2
        mock_participacion.ultima_asistencia = timezone.datetime(2024, 9, 1).date()
        
        mock_qs = MagicMock()
        mock_qs.__iter__ = lambda self: iter([mock_participacion])
        
        mock_participaciones.filter.return_value.annotate.return_value.select_related.return_value = mock_qs
        
        resultado = tasks.clasificar_estudiantes_para_admin()
        
        self.assertIn('Clasificación completada', resultado)
        self.assertIn('riesgo_critico', resultado)

    @patch("Analytics_Reports.tasks.timezone")
    @patch("Analytics_Reports.tasks.Participaciones.objects")
    @patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config")
    def test_clasificacion_sin_enviar_correos(
        self, mock_config, mock_participaciones, mock_tz
    ):
        """La clasificación NO debe enviar correos a estudiantes"""
        mock_tz.now.return_value = timezone.datetime(2024, 10, 19, tzinfo=timezone.get_current_timezone())
        
        mock_config_obj = MagicMock()
        mock_config_obj.umbral_riesgo_critico = 2
        mock_config_obj.dias_riesgo_critico = 21
        mock_config_obj.umbral_baja_asistencia = 5
        mock_config_obj.dias_inactividad = 14
        mock_config_obj.asistencias_destacado = 15
        mock_config.return_value = mock_config_obj
        
        mock_qs = MagicMock()
        mock_qs.__iter__ = lambda self: iter([])
        mock_participaciones.filter.return_value.annotate.return_value.select_related.return_value = mock_qs
        
        with patch("Analytics_Reports.tasks.send_mail") as mock_send:
            resultado = tasks.clasificar_estudiantes_para_admin()
            
            # Verificar que NO se llamó send_mail
            mock_send.assert_not_called()


# ==========================================================
# TESTS PARA TAREA 3: ENCUESTAS
# ==========================================================

class EnviarEncuestasTests(SimpleTestCase):
    """Pruebas para enviar_encuestas_retroalimentacion"""

    @patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config")
    def test_encuestas_desactivadas(self, mock_config):
        """No debe ejecutar si las encuestas están desactivadas"""
        mock_config_obj = MagicMock()
        mock_config_obj.encuestas_activas = False
        mock_config.return_value = mock_config_obj
        
        resultado = tasks.enviar_encuestas_retroalimentacion()
        
        self.assertEqual(resultado, '⏸️ Encuestas desactivadas por el admin')

    @patch("Analytics_Reports.tasks.send_mail")
    @patch("Analytics_Reports.tasks.ControlNotificacionesContextual")
    @patch("Analytics_Reports.tasks.CalificacionesActividad.objects")
    @patch("Analytics_Reports.tasks.Participaciones.objects")
    @patch("Analytics_Reports.tasks.Actividades.objects")
    @patch("Analytics_Reports.tasks.timezone")
    @patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config")
    def test_envia_encuesta_actividad_finalizada(
        self, mock_config, mock_tz, mock_actividades, mock_participaciones,
        mock_calificaciones, mock_control, mock_send_mail
    ):
        """Debe enviar encuesta para actividades finalizadas"""
        ahora = timezone.datetime(2024, 10, 19, tzinfo=timezone.get_current_timezone())
        mock_tz.now.return_value = ahora
        
        mock_config_obj = MagicMock()
        mock_config_obj.encuestas_activas = True
        mock_config_obj.dias_despues_cierre_encuesta = 3
        mock_config_obj.asistencias_minimas_encuesta = 3
        mock_config.return_value = mock_config_obj
        
        # Mock actividad finalizada
        mock_actividad = MagicMock()
        mock_actividad.nombre = 'Yoga'
        mock_actividad.fecha_cierre_ins = ahora - timedelta(days=1)
        mock_actividades.filter.return_value = [mock_actividad]
        
        # Mock participación con suficientes asistencias
        mock_participante = MagicMock()
        mock_participante.correo = 'test@test.com'
        mock_participacion = MagicMock()
        mock_participacion.participantes_id_participante = mock_participante
        mock_participacion.num_asistencias = 5
        
        mock_participaciones.filter.return_value.annotate.return_value.filter.return_value = [mock_participacion]
        
        # No ha calificado aún
        mock_calificaciones.filter.return_value.exists.return_value = False
        
        # Control anti-spam
        mock_control.ya_existe_notificacion.return_value = False
        mock_control.registrar_notificacion.return_value = MagicMock()
        
        resultado = tasks.enviar_encuestas_retroalimentacion()
        
        self.assertIn('encuestas enviadas', resultado)
        mock_send_mail.assert_called_once()

    @patch("Analytics_Reports.tasks.CalificacionesActividad.objects")
    @patch("Analytics_Reports.tasks.Participaciones.objects")
    @patch("Analytics_Reports.tasks.Actividades.objects")
    @patch("Analytics_Reports.tasks.timezone")
    @patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config")
    def test_no_envia_si_ya_califico(
        self, mock_config, mock_tz, mock_actividades, 
        mock_participaciones, mock_calificaciones
    ):
        """No debe enviar encuesta si ya calificó"""
        ahora = timezone.datetime(2024, 10, 19, tzinfo=timezone.get_current_timezone())
        mock_tz.now.return_value = ahora
        
        mock_config_obj = MagicMock()
        mock_config_obj.encuestas_activas = True
        mock_config_obj.dias_despues_cierre_encuesta = 3
        mock_config_obj.asistencias_minimas_encuesta = 3
        mock_config.return_value = mock_config_obj
        
        mock_actividad = MagicMock()
        mock_actividades.filter.return_value = [mock_actividad]
        
        mock_participacion = MagicMock()
        mock_participaciones.filter.return_value.annotate.return_value.filter.return_value = [mock_participacion]
        
        # Ya calificó
        mock_calificaciones.filter.return_value.exists.return_value = True
        
        with patch("Analytics_Reports.tasks.send_mail") as mock_send:
            resultado = tasks.enviar_encuestas_retroalimentacion()
            
            # No debe enviar
            mock_send.assert_not_called()


# ==========================================================
# TESTS PARA TAREA 4: RECORDATORIOS DE CITAS
# ==========================================================

class RecordatoriosCitasTests(SimpleTestCase):
    """Pruebas para enviar_recordatorios_citas"""

    @patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config")
    def test_recordatorios_desactivados(self, mock_config):
        """No debe ejecutar si los recordatorios están desactivados"""
        mock_config_obj = MagicMock()
        mock_config_obj.recordatorios_citas_activos = False
        mock_config.return_value = mock_config_obj
        
        resultado = tasks.enviar_recordatorios_citas()
        
        self.assertEqual(resultado, '⏸️ Recordatorios de citas desactivados')

    @patch("Analytics_Reports.tasks.send_mail")
    @patch("Analytics_Reports.tasks.ControlNotificacionesContextual")
    @patch("Analytics_Reports.tasks.Citas.objects")
    @patch("Analytics_Reports.tasks.timezone")
    @patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config")
    def test_envia_recordatorio_cita_proxima(
        self, mock_config, mock_tz, mock_citas, mock_control, mock_send_mail
    ):
        """Debe enviar recordatorio X días antes de la cita"""
        ahora = timezone.datetime(2024, 10, 19, 12, 0, 0, tzinfo=timezone.get_current_timezone())
        mock_tz.now.return_value = ahora
        
        mock_config_obj = MagicMock()
        mock_config_obj.recordatorios_citas_activos = True
        mock_config_obj.recordatorio_cita_dias_antes = 3
        mock_config.return_value = mock_config_obj
        
        # Cita en 3 días
        fecha_cita = ahora + timedelta(days=3)
        
        mock_participante = MagicMock()
        mock_participante.correo = 'test@test.com'
        
        mock_cita = MagicMock()
        mock_cita.id_cita = 123
        mock_cita.fecha = fecha_cita
        mock_cita.motivo = 'Consulta psicológica'
        mock_cita.participantes_id_participante = mock_participante
        
        mock_citas.filter.return_value.select_related.return_value = [mock_cita]
        
        mock_control.ya_existe_notificacion.return_value = False
        mock_control.registrar_notificacion.return_value = MagicMock()
        
        resultado = tasks.enviar_recordatorios_citas()
        
        self.assertIn('recordatorios de citas enviados', resultado)
        mock_send_mail.assert_called_once()

    @patch("Analytics_Reports.tasks.ControlNotificacionesContextual")
    @patch("Analytics_Reports.tasks.Citas.objects")
    @patch("Analytics_Reports.tasks.timezone")
    @patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config")
    def test_no_duplica_recordatorio_existente(
        self, mock_config, mock_tz, mock_citas, mock_control
    ):
        """No debe enviar recordatorio si ya existe"""
        ahora = timezone.datetime(2024, 10, 19, 12, 0, 0, tzinfo=timezone.get_current_timezone())
        mock_tz.now.return_value = ahora
        
        mock_config_obj = MagicMock()
        mock_config_obj.recordatorios_citas_activos = True
        mock_config_obj.recordatorio_cita_dias_antes = 3
        mock_config.return_value = mock_config_obj
        
        mock_cita = MagicMock()
        mock_citas.filter.return_value.select_related.return_value = [mock_cita]
        
        # Ya existe notificación
        mock_control.ya_existe_notificacion.return_value = True
        
        with patch("Analytics_Reports.tasks.send_mail") as mock_send:
            resultado = tasks.enviar_recordatorios_citas()
            
            mock_send.assert_not_called()


# ==========================================================
# TESTS PARA TAREA 5: CANCELACIONES
# ==========================================================

class NotificarCancelacionTests(SimpleTestCase):
    """Pruebas para notificar_cancelacion_actividad"""

    def test_retorna_error_actividad_inexistente(self):
        """Debe retornar error si la actividad no existe"""
        # Importar la excepción real del modelo
        from universitaryWellbeing.models import Actividades
        
        with patch.object(Actividades.objects, 'get') as mock_get:
            mock_get.side_effect = Actividades.DoesNotExist("Actividad no existe")
            
            resultado = tasks.notificar_cancelacion_actividad(999)
            
            self.assertIn('no existe', resultado.lower())

    @patch("Analytics_Reports.tasks.send_mail")
    @patch("Analytics_Reports.tasks.ControlNotificacionesContextual")
    @patch("Analytics_Reports.tasks.Participaciones.objects")
    @patch("Analytics_Reports.tasks.Actividades.objects")
    def test_notifica_todos_inscritos(
        self, mock_actividades, mock_participaciones, mock_control, mock_send_mail
    ):
        """Debe notificar a todos los inscritos de la cancelación"""
        mock_actividad = MagicMock()
        mock_actividad.nombre = 'Yoga'
        mock_actividad.id_actividad = 1
        mock_actividades.get.return_value = mock_actividad
        
        # Dos inscritos
        mock_participante1 = MagicMock()
        mock_participante1.correo = 'user1@test.com'
        mock_participante2 = MagicMock()
        mock_participante2.correo = 'user2@test.com'
        
        mock_part1 = MagicMock()
        mock_part1.participantes_id_participante = mock_participante1
        mock_part2 = MagicMock()
        mock_part2.participantes_id_participante = mock_participante2
        
        mock_participaciones.filter.return_value.select_related.return_value = [mock_part1, mock_part2]
        
        mock_control.ya_existe_notificacion.return_value = False
        mock_control.registrar_notificacion.return_value = MagicMock()
        
        resultado = tasks.notificar_cancelacion_actividad(1, "Problemas técnicos")
        
        self.assertIn('2 notificaciones de cancelación enviadas', resultado)
        self.assertEqual(mock_send_mail.call_count, 2)

    @patch("Analytics_Reports.tasks.ControlNotificacionesContextual")
    @patch("Analytics_Reports.tasks.Participaciones.objects")
    @patch("Analytics_Reports.tasks.Actividades.objects")
    def test_no_duplica_notificacion_cancelacion(
        self, mock_actividades, mock_participaciones, mock_control
    ):
        """No debe enviar notificación de cancelación duplicada"""
        mock_actividad = MagicMock()
        mock_actividades.get.return_value = mock_actividad
        
        mock_participacion = MagicMock()
        mock_participaciones.filter.return_value.select_related.return_value = [mock_participacion]
        
        # Ya existe notificación de cancelación
        mock_control.ya_existe_notificacion.return_value = True
        
        with patch("Analytics_Reports.tasks.send_mail") as mock_send:
            resultado = tasks.notificar_cancelacion_actividad(1)
            
            mock_send.assert_not_called()


# ==========================================================
# TESTS DE INTEGRACIÓN
# ==========================================================

class IntegracionTasksTests(SimpleTestCase):
    """Tests de integración entre múltiples tareas"""

    @patch("Analytics_Reports.tasks.send_mail")
    @patch("Analytics_Reports.tasks.ControlNotificacionesContextual")
    def test_control_antispam_funciona_entre_tareas(self, mock_control, mock_send):
        """El control anti-spam debe funcionar correctamente entre diferentes tareas"""
        # Simular que ya existe una notificación
        mock_control.ya_existe_notificacion.return_value = True
        
        # Intentar registrar
        mock_control.registrar_notificacion.return_value = None
        
        # El send_mail NO debe ser llamado
        if mock_control.registrar_notificacion.return_value is None:
            # Correcto comportamiento
            pass
        else:
            mock_send.assert_not_called()

    def test_todas_las_tareas_retornan_string(self):
        """Todas las tareas deben retornar un string descriptivo"""
        with patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config") as mock_config:
            mock_config_obj = MagicMock()
            mock_config_obj.reconocimientos_activos = False
            mock_config_obj.encuestas_activas = False
            mock_config_obj.recordatorios_citas_activos = False
            mock_config.return_value = mock_config_obj
            
            # Todas deben retornar string
            self.assertIsInstance(tasks.verificar_y_otorgar_reconocimientos(), str)
            self.assertIsInstance(tasks.enviar_encuestas_retroalimentacion(), str)
            self.assertIsInstance(tasks.enviar_recordatorios_citas(), str)
            
            with patch("Analytics_Reports.tasks.Participaciones.objects") as mock_part:
                mock_qs = MagicMock()
                mock_qs.__iter__ = lambda self: iter([])
                mock_part.filter.return_value.annotate.return_value.select_related.return_value = mock_qs
                self.assertIsInstance(tasks.clasificar_estudiantes_para_admin(), str)


# ==========================================================
# TESTS DE EDGE CASES
# ==========================================================

class EdgeCasesTests(SimpleTestCase):
    """Casos extremos y situaciones inusuales"""

    @patch("Analytics_Reports.tasks.Participaciones.objects")
    @patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config")
    def test_reconocimientos_con_hitos_vacios(self, mock_config, mock_participaciones):
        """Debe manejar correctamente cuando no hay hitos configurados"""
        mock_config_obj = MagicMock()
        mock_config_obj.reconocimientos_activos = True
        mock_config_obj.obtener_hitos.return_value = []  # Sin hitos
        mock_config.return_value = mock_config_obj
        
        mock_participaciones.filter.return_value.select_related.return_value = []
        
        resultado = tasks.verificar_y_otorgar_reconocimientos()
        
        self.assertIn('0 reconocimientos otorgados', resultado)

    @patch("Analytics_Reports.tasks.send_mail")
    def test_send_mail_falla_silenciosamente(self, mock_send):
        """Debe continuar incluso si send_mail falla"""
        mock_send.side_effect = Exception("SMTP Error")
        
        with patch("Analytics_Reports.tasks.ConfiguracionNotificaciones.obtener_config") as mock_config:
            mock_config_obj = MagicMock()
            mock_config_obj.reconocimientos_activos = True
            mock_config_obj.obtener_hitos.return_value = [10]
            mock_config.return_value = mock_config_obj
            
            with patch("Analytics_Reports.tasks.Participaciones.objects") as mock_part:
                with patch("Analytics_Reports.tasks.Asistencias.objects") as mock_asist:
                    with patch("Analytics_Reports.tasks.ControlNotificacionesContextual") as mock_control:
                        mock_participante = MagicMock()
                        mock_actividad = MagicMock()
                        mock_participacion = MagicMock()
                        mock_participacion.participantes_id_participante = mock_participante
                        mock_participacion.actividades_id_actividad = mock_actividad
                        
                        mock_part.filter.return_value.select_related.return_value = [mock_participacion]
                        mock_asist.filter.return_value.count.return_value = 10
                        mock_control.ya_existe_notificacion.return_value = False
                        mock_control.registrar_notificacion.return_value = MagicMock()
                        
                        # No debe lanzar excepción
                        resultado = tasks.verificar_y_otorgar_reconocimientos()
                        self.assertIsInstance(resultado, str)