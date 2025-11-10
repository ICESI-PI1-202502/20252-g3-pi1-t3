from django.test import SimpleTestCase, TestCase
from unittest.mock import patch, MagicMock, mock_open
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from Analytics_Reports import views as vw
import os

# ==========================================================
# TESTS UNITARIOS DE FUNCIONES AUXILIARES
# ==========================================================

class HelpersTestCase(SimpleTestCase):
    """Pruebas unitarias para helpers simples"""

    def test_is_admin_true_for_staff(self):
        user = MagicMock(is_authenticated=True, is_staff=True)
        self.assertTrue(vw.is_admin(user))

    def test_is_admin_false_for_anonymous(self):
        user = MagicMock(is_authenticated=False, is_staff=False)
        self.assertFalse(vw.is_admin(user))

    @patch("Analytics_Reports.views.os.makedirs")
    @patch("Analytics_Reports.views.open", create=True)
    @patch("Analytics_Reports.views.timezone")
    def test_log_email_creates_directory_and_logs(self, mock_tz, mock_open, mock_makedirs):
        """Debe crear el directorio y registrar el log de correo"""
        mock_tz.now.return_value = timezone.datetime(2024, 10, 19, 12, 0, 0)
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        vw.log_email(["test@correo.com"], "Asunto de prueba")
        mock_makedirs.assert_called_once_with(vw.LOG_DIR, exist_ok=True)
        mock_file.write.assert_called_once()

    @patch("Analytics_Reports.views.send_mail")
    @patch("Analytics_Reports.views.log_email")
    def test_enviar_email_empty_list_returns_early(self, mock_log, mock_send):
        """No debe enviar si la lista de destinatarios está vacía"""
        vw.enviar_email("Asunto", "Mensaje", [])
        mock_send.assert_not_called()
        mock_log.assert_not_called()


# ==========================================================
# TESTS DE ANÁLISIS DE COMPORTAMIENTO
# ==========================================================

class AnalisisComportamientoTests(SimpleTestCase):
    """Pruebas unitarias para la vista analisis_comportamiento"""

    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.TiposActividad.objects")
    @patch("Analytics_Reports.views.render")
    def test_analisis_comportamiento_filters_and_renders(self, mock_render, mock_tipos, mock_participaciones):
        """Debe aplicar filtros y renderizar el template"""
        request = MagicMock()
        request.GET = {"tipo_actividad": "2", "min_frecuencia": "5"}

        mock_qs = mock_participaciones.values.return_value.annotate.return_value.order_by.return_value
        mock_tipos.all.return_value.order_by.return_value = ["Taller", "Deporte"]

        vw.analisis_comportamiento(request)

        mock_participaciones.values.assert_called_once()
        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        self.assertIn("data", context)
        self.assertIn("tipos_actividad", context)

    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.TiposActividad.objects")
    def test_analisis_comportamiento_exports_csv(self, mock_tipos, mock_participaciones):
        """Debe exportar datos a CSV cuando export=csv"""
        request = MagicMock()
        request.GET = {"export": "csv"}

        # Mock del queryset con datos
        mock_qs = MagicMock()
        mock_participaciones.values.return_value.annotate.return_value.order_by.return_value = mock_qs
        mock_qs.__iter__ = lambda self: iter([
            {
                "participantes_id_participante__nombre": "Juan",
                "participantes_id_participante__correo": "juan@test.com",
                "participantes_id_participante__semestre": 3,
                "participantes_id_participante__facultad": "Ingeniería",
                "participantes_id_participante__roles_id_rol__nombre_rol": "Estudiante",
                "actividades_id_actividad__tipos_actividad_id_tipo__nombre_tipo": "Deporte",
                "total": 5
            }
        ])

        response = vw.analisis_comportamiento(request)

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])

    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.TiposActividad.objects")
    @patch("Analytics_Reports.views.render")
    def test_analisis_comportamiento_with_invalid_frequency(self, mock_render, mock_tipos, mock_participaciones):
        """Debe manejar frecuencia mínima inválida sin fallar"""
        request = MagicMock()
        request.GET = {"min_frecuencia": "invalid"}

        mock_qs = mock_participaciones.values.return_value.annotate.return_value.order_by.return_value
        mock_tipos.all.return_value.order_by.return_value = []

        vw.analisis_comportamiento(request)

        # No debe llamar filter con frecuencia inválida
        mock_render.assert_called_once()


# ==========================================================
# TESTS DE ENVÍO DE CORREOS
# ==========================================================

class EmailTests(SimpleTestCase):
    """Pruebas de envío y logging de correos"""

    @patch("Analytics_Reports.views.send_mail")
    @patch("Analytics_Reports.views.log_email")
    def test_enviar_email_calls_send_and_log(self, mock_log, mock_send):
        """Debe llamar send_mail y log_email"""
        vw.enviar_email("Asunto", "Mensaje", ["user@correo.com"])
        mock_send.assert_called_once()
        mock_log.assert_called_once()

    @patch("Analytics_Reports.views.enviar_email")
    def test_enviar_email_staff_uses_correct_recipients(self, mock_enviar):
        """Debe usar los correos de staff configurados"""
        vw.enviar_email_staff("Alerta", "Mensaje")
        args = mock_enviar.call_args[0]
        self.assertIn("admin@academia.com", args[2])
        self.assertIn("coordinador@academia.com", args[2])


# ==========================================================
# TESTS DE RECOMENDACIONES
# ==========================================================

class RecomendacionesTests(SimpleTestCase):
    """Pruebas unitarias de la vista recomendaciones"""

    @patch("Analytics_Reports.views.obtener_estudiantes_poca_asistencia")
    @patch("Analytics_Reports.views.obtener_proximos_reconocimientos")
    @patch("Analytics_Reports.views.obtener_estudiantes_inactivos")
    @patch("Analytics_Reports.views.obtener_estudiantes_destacados")
    @patch("Analytics_Reports.views.obtener_alertas_riesgo")
    @patch("Analytics_Reports.views.obtener_estudiantes_activos")
    @patch("Analytics_Reports.views.render")
    def test_recomendaciones_renders_correct_context(
        self, mock_render, mock_activos, mock_riesgo, mock_destacados,
        mock_inactivos, mock_reconocimientos, mock_poca_asistencia
    ):
        """Debe construir el contexto completo y renderizar"""
        request = MagicMock(GET={})

        for mock_fn in [
            mock_activos, mock_riesgo, mock_destacados,
            mock_inactivos, mock_reconocimientos, mock_poca_asistencia
        ]:
            mock_fn.return_value = []

        vw.recomendaciones(request)

        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        self.assertIn("poca_asistencia", context)
        self.assertIn("fecha_actualizacion", context)
        self.assertIn("alertas_riesgo", context)
        self.assertIn("estudiantes_activos", context)

    @patch("Analytics_Reports.views.obtener_estudiantes_poca_asistencia")
    @patch("Analytics_Reports.views.obtener_proximos_reconocimientos")
    @patch("Analytics_Reports.views.obtener_estudiantes_inactivos")
    @patch("Analytics_Reports.views.obtener_estudiantes_destacados")
    @patch("Analytics_Reports.views.obtener_alertas_riesgo")
    @patch("Analytics_Reports.views.obtener_estudiantes_activos")
    @patch("Analytics_Reports.views.enviar_notificaciones_automaticas")
    @patch("Analytics_Reports.views.messages")
    @patch("Analytics_Reports.views.render")
    def test_recomendaciones_sends_notifications_when_requested(
        self, mock_render, mock_messages, mock_enviar_notif,
        mock_activos, mock_riesgo, mock_destacados,
        mock_inactivos, mock_reconocimientos, mock_poca_asistencia
    ):
        """Debe enviar notificaciones cuando se solicita"""
        request = MagicMock()
        request.GET = {"enviar_notificaciones": "1"}

        for mock_fn in [mock_activos, mock_riesgo, mock_destacados,
                       mock_inactivos, mock_reconocimientos, mock_poca_asistencia]:
            mock_fn.return_value = []

        vw.recomendaciones(request)

        mock_enviar_notif.assert_called_once()
        mock_messages.success.assert_called_once()


# ==========================================================
# TESTS DE FUNCIONES AUXILIARES DE CONSULTA
# ==========================================================

class QueryHelpersTests(SimpleTestCase):
    """Verifica funciones que retornan datos (mockeados)"""

    @patch("Analytics_Reports.views.Participaciones.objects")
    def test_obtener_estudiantes_poca_asistencia(self, mock_participantes):
        """Debe filtrar correctamente estudiantes con poca asistencia"""
        mock_qs = MagicMock()
        mock_participantes.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = []
        
        vw.obtener_estudiantes_poca_asistencia(umbral_asistencias=2)
        mock_participantes.annotate.assert_called_once()

    @patch("Analytics_Reports.views.Participaciones.objects")
    def test_obtener_estudiantes_destacados(self, mock_participantes):
        """Debe anotar correctamente promedios"""
        mock_qs = MagicMock()
        mock_participantes.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = []
        
        vw.obtener_estudiantes_destacados()
        mock_participantes.annotate.assert_called_once()

    @patch("Analytics_Reports.views.Participaciones.objects")
    def test_obtener_estudiantes_inactivos(self, mock_participantes):
        """Debe filtrar correctamente estudiantes sin actividad reciente"""
        mock_qs = MagicMock()
        mock_participantes.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = []
        
        vw.obtener_estudiantes_inactivos()
        mock_participantes.annotate.assert_called_once()

    @patch("Analytics_Reports.views.Participaciones.objects")
    def test_obtener_estudiantes_activos(self, mock_participantes):
        """Debe filtrar estudiantes con asistencia reciente"""
        mock_qs = MagicMock()
        mock_participantes.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = []
        
        vw.obtener_estudiantes_activos(dias_actividad=7)
        mock_participantes.annotate.assert_called_once()

    @patch("Analytics_Reports.views.Participaciones.objects")
    def test_obtener_proximos_reconocimientos(self, mock_participantes):
        """Debe filtrar estudiantes cercanos a reconocimiento"""
        mock_qs = MagicMock()
        mock_participantes.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = []
        
        vw.obtener_proximos_reconocimientos()
        mock_participantes.annotate.assert_called_once()

    @patch("Analytics_Reports.views.Participaciones.objects")
    def test_obtener_alertas_riesgo(self, mock_participantes):
        """Debe filtrar estudiantes en riesgo"""
        mock_qs = MagicMock()
        mock_participantes.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = []
        
        vw.obtener_alertas_riesgo()
        mock_participantes.annotate.assert_called_once()


# ==========================================================
# TESTS DE NOTIFICACIONES AUTOMÁTICAS
# ==========================================================

class NotificacionesAutomaticasTests(SimpleTestCase):
    """Pruebas de envío de notificaciones automáticas"""

    @patch("Analytics_Reports.views.enviar_alerta_poca_asistencia")
    @patch("Analytics_Reports.views.enviar_notificacion_reconocimientos")
    @patch("Analytics_Reports.views.enviar_alerta_inactividad")
    def test_enviar_notificaciones_automaticas_with_data(
        self, mock_inact, mock_recon, mock_poca
    ):
        """Debe enviar notificaciones cuando hay datos"""
        context = {
            'poca_asistencia': [MagicMock()],
            'proximos_reconocimientos': [MagicMock()],
            'estudiantes_inactivos': [MagicMock()]
        }
        
        vw.enviar_notificaciones_automaticas(context)
        
        mock_poca.assert_called_once()
        mock_recon.assert_called_once()
        mock_inact.assert_called_once()

    @patch("Analytics_Reports.views.enviar_alerta_poca_asistencia")
    @patch("Analytics_Reports.views.enviar_notificacion_reconocimientos")
    @patch("Analytics_Reports.views.enviar_alerta_inactividad")
    def test_enviar_notificaciones_automaticas_without_data(
        self, mock_inact, mock_recon, mock_poca
    ):
        """No debe enviar notificaciones cuando no hay datos"""
        context = {
            'poca_asistencia': [],
            'proximos_reconocimientos': [],
            'estudiantes_inactivos': []
        }
        
        vw.enviar_notificaciones_automaticas(context)
        
        mock_poca.assert_not_called()
        mock_recon.assert_not_called()
        mock_inact.assert_not_called()

    @patch("Analytics_Reports.views.enviar_email_staff")
    def test_enviar_alerta_poca_asistencia(self, mock_email_staff):
        """Debe enviar alerta al staff con formato correcto"""
        estudiante = MagicMock()
        estudiante.participantes_id_participante.nombre = "Juan"
        estudiante.participantes_id_participante.apellido = "Pérez"
        estudiante.total_asistencias = 2
        estudiante.actividades_id_actividad.nombre = "Yoga"
        
        vw.enviar_alerta_poca_asistencia([estudiante])
        
        mock_email_staff.assert_called_once()
        args = mock_email_staff.call_args[0]
        self.assertIn("1 estudiantes con baja asistencia", args[0])
        self.assertIn("Juan Pérez", args[1])

    @patch("Analytics_Reports.views.enviar_email")
    def test_enviar_notificacion_reconocimientos(self, mock_email):
        """Debe enviar notificación individual a estudiante"""
        estudiante = MagicMock()
        estudiante.participantes_id_participante.nombre = "María"
        estudiante.participantes_id_participante.apellido = "García"
        estudiante.participantes_id_participante.correo = "maria@test.com"
        estudiante.total_asistencias = 9
        estudiante.actividades_id_actividad.nombre = "Danza"
        
        vw.enviar_notificacion_reconocimientos([estudiante])
        
        mock_email.assert_called_once()
        args = mock_email.call_args[0]
        self.assertIn("María", args[0])
        self.assertIn("9 asistencias", args[1])
        self.assertEqual(args[2], ["maria@test.com"])

    @patch("Analytics_Reports.views.enviar_email")
    def test_enviar_notificacion_reconocimientos_sin_correo(self, mock_email):
        """No debe enviar si el estudiante no tiene correo"""
        estudiante = MagicMock()
        estudiante.participantes_id_participante.correo = None
        estudiante.total_asistencias = 9
        
        vw.enviar_notificacion_reconocimientos([estudiante])
        
        mock_email.assert_not_called()

    @patch("Analytics_Reports.views.enviar_email_staff")
    def test_enviar_alerta_inactividad(self, mock_email_staff):
        """Debe enviar alerta de inactividad al staff"""
        estudiante = MagicMock()
        estudiante.participantes_id_participante.nombre = "Carlos"
        estudiante.participantes_id_participante.apellido = "López"
        estudiante.actividades_id_actividad.nombre = "Natación"
        
        vw.enviar_alerta_inactividad([estudiante])
        
        mock_email_staff.assert_called_once()
        args = mock_email_staff.call_args[0]
        self.assertIn("1 estudiantes inactivos", args[0])
        self.assertIn("Carlos López", args[1])


# ==========================================================
# TESTS DE ENCUESTAS FEEDBACK
# ==========================================================

class EncuestasFeedbackTests(SimpleTestCase):
    """Pruebas de generación de encuestas de feedback"""

    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.enviar_encuesta_feedback")
    def test_generar_encuesta_feedback_calls_for_each_student(
        self, mock_enviar, mock_participaciones
    ):
        """Debe enviar encuesta a cada estudiante que completó"""
        mock_qs = MagicMock()
        mock_participaciones.filter.return_value.filter.return_value.select_related.return_value = [
            MagicMock(), MagicMock()
        ]
        
        with patch("Analytics_Reports.views.timezone") as mock_tz:
            mock_tz.now.return_value = timezone.datetime(2024, 10, 19)
            vw.generar_encuesta_feedback()
        
        self.assertEqual(mock_enviar.call_count, 2)

    @patch("Analytics_Reports.views.enviar_email")
    def test_enviar_encuesta_feedback(self, mock_email):
        """Debe enviar encuesta con URL correcta"""
        participacion = MagicMock()
        participacion.participantes_id_participante.nombre = "Ana"
        participacion.participantes_id_participante.apellido = "Martínez"
        participacion.participantes_id_participante.correo = "ana@test.com"
        participacion.actividades_id_actividad.nombre = "Pilates"
        participacion.id_participacion = 123
        
        vw.enviar_encuesta_feedback(participacion)
        
        mock_email.assert_called_once()
        args = mock_email.call_args[0]
        self.assertIn("Pilates", args[0])
        self.assertIn("id=123", args[1])
        self.assertEqual(args[2], ["ana@test.com"])


# ==========================================================
# TESTS DE CONFIGURACIÓN
# ==========================================================

class ConfiguracionNotificacionesTests(SimpleTestCase):
    """Pruebas de configuración de notificaciones"""

    @patch("Analytics_Reports.views.messages")
    @patch("Analytics_Reports.views.render")
    def test_configurar_notificaciones_post(self, mock_render, mock_messages):
        """Debe procesar POST y guardar configuración"""
        request = MagicMock()
        request.method = 'POST'
        request.POST = {
            'umbral_asistencia': '60',
            'dias_inactividad': '21',
            'envio_automatico': 'on',
            'frecuencia_envio': 'diario'
        }
        
        vw.configurar_notificaciones(request)
        
        mock_messages.success.assert_called_once()
        mock_render.assert_called_once()

    @patch("Analytics_Reports.views.render")
    def test_configurar_notificaciones_get(self, mock_render):
        """Debe renderizar formulario en GET"""
        request = MagicMock()
        request.method = 'GET'
        
        vw.configurar_notificaciones(request)
        
        mock_render.assert_called_once()


# ==========================================================
# TESTS DE FUNCIONES DE COMPARACIONES
# ==========================================================

class ComparacionesTests(TestCase):
    """Pruebas para la vista comparaciones"""
    
    databases = '__all__'

    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.Asistencias.objects")
    @patch("Analytics_Reports.views.Participantes.objects")
    @patch("Analytics_Reports.views.render")
    def test_comparaciones_renders_context(self, mock_render, mock_participantes_model, 
                                          mock_asistencias, mock_participaciones):
        """Debe crear contexto con datos agregados"""
        request = MagicMock(GET={})
        
        mock_qs_part = MagicMock()
        mock_participaciones.values.return_value = mock_qs_part
        mock_qs_part.annotate.return_value = mock_qs_part
        mock_qs_part.order_by.return_value = [
            {"tipo": "Deporte", "total": 5},
            {"tipo": "Cultural", "total": 3},
        ]
        
        mock_asistencias.count.return_value = 10
        mock_participantes_model.count.return_value = 5
        mock_participaciones.values.return_value.annotate.return_value.filter.return_value.count.return_value = 2
        mock_participantes_model.objects.values_list.return_value.distinct.return_value.order_by.return_value = [1, 2, 3]
        
        vw.comparaciones(request)
        
        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        self.assertIn("resultados", context)
        self.assertIn("metricas", context)
        self.assertIsInstance(context["resultados"], list)


# ==========================================================
# TESTS DE VISTAS AUXILIARES
# ==========================================================

class VistasAuxiliaresTests(SimpleTestCase):
    """Pruebas de vistas simples"""

    @patch("Analytics_Reports.views.render")
    def test_analytics_index(self, mock_render):
        """Debe renderizar index correctamente"""
        request = MagicMock()
        vw.analytics_index(request)
        mock_render.assert_called_once_with(request, "index.html")

    @patch("Analytics_Reports.views.Participantes.objects")
    @patch("Analytics_Reports.views.render")
    def test_participantes_list(self, mock_render, mock_participantes):
        """Debe listar participantes ordenados"""
        mock_participantes.all.return_value.order_by.return_value = []
        request = MagicMock()
        
        vw.participantes_list(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][0], request)
        self.assertEqual(mock_render.call_args[0][1], "participantes.html")

    @patch("Analytics_Reports.views.Asistencias.objects")
    @patch("Analytics_Reports.views.render")
    def test_asistencia(self, mock_render, mock_asistencias):
        """Debe renderizar datos de asistencia"""
        mock_qs = MagicMock()
        mock_asistencias.values.return_value.annotate.return_value = []
        request = MagicMock()
        
        vw.asistencia(request)
        
        mock_render.assert_called_once()