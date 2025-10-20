# analytics_reports/tests/test_analytics_reports.py

from django.test import SimpleTestCase, TestCase
from unittest.mock import patch, MagicMock
from django.utils import timezone
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


# ==========================================================
# TESTS DE FUNCIONES AUXILIARES DE CONSULTA
# ==========================================================

class QueryHelpersTests(SimpleTestCase):
    """Verifica funciones que retornan datos (mockeados)"""

    @patch("Analytics_Reports.views.Participaciones.objects")
    def test_obtener_estudiantes_poca_asistencia(self, mock_participantes):
        """Debe filtrar correctamente estudiantes con poca asistencia"""
        # FIX: Cambiar 'umbral' por 'umbral_asistencias'
        vw.obtener_estudiantes_poca_asistencia(umbral_asistencias=2)
        mock_participantes.annotate.assert_called_once()

    @patch("Analytics_Reports.views.Participaciones.objects")
    def test_obtener_estudiantes_destacados(self, mock_participantes):
        """Debe anotar correctamente promedios"""
        # FIX: Crear mock completo de la cadena de llamadas
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
        # FIX: Crear mock completo de la cadena de llamadas
        mock_qs = MagicMock()
        mock_participantes.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = []
        
        vw.obtener_estudiantes_inactivos()
        mock_participantes.annotate.assert_called_once()


# ==========================================================
# TESTS DE FUNCIONES DE COMPARACIONES
# ==========================================================

class ComparacionesTests(TestCase):  # FIX: Cambiar de SimpleTestCase a TestCase
    """Pruebas para la vista comparaciones"""
    
    # FIX: Agregar databases para permitir queries
    databases = '__all__'

    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.Asistencias.objects")
    @patch("Analytics_Reports.views.Participantes.objects")
    @patch("Analytics_Reports.views.render")
    def test_comparaciones_renders_context(self, mock_render, mock_participantes_model, 
                                          mock_asistencias, mock_participaciones):
        """Debe crear contexto con datos agregados"""
        request = MagicMock(GET={})
        
        # Mock para Participaciones
        mock_qs_part = MagicMock()
        mock_participaciones.values.return_value = mock_qs_part
        mock_qs_part.annotate.return_value = mock_qs_part
        mock_qs_part.order_by.return_value = [
            {"tipo": "Deporte", "total": 5},
            {"tipo": "Cultural", "total": 3},
        ]
        
        # Mock para Asistencias.count()
        mock_asistencias.count.return_value = 10
        
        # Mock para Participantes.count()
        mock_participantes_model.count.return_value = 5
        
        # Mock para la query de reincidencia
        mock_participaciones.values.return_value.annotate.return_value.filter.return_value.count.return_value = 2
        
        # Mock para semestres disponibles
        mock_participantes_model.objects.values_list.return_value.distinct.return_value.order_by.return_value = [1, 2, 3]
        
        vw.comparaciones(request)
        
        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        self.assertIn("resultados", context)  # FIX: Cambiar "datos" por "resultados"
        self.assertIn("metricas", context)
        self.assertIsInstance(context["resultados"], list)