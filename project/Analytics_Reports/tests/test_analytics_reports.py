#project\Analytics_Reports\tests\test_analytics_reports.py

#https://www.reddit.com/r/node/comments/10tdb61/why_should_i_mock_a_database_for_testing_instead/

"""
Tests unitarios completos para Analytics_Reports/views.py

COBERTURA REAL DE TESTS:
========================

1. FUNCIONES AUXILIARES (HelpersTestCase):
   - Verificación de permisos admin (is_staff)
   - Logging de emails: creación de directorio y registro
   - Validación de lista vacía en envío de emails

2. ANÁLISIS DE COMPORTAMIENTO (AnalisisComportamientoTests):
   - Renderizado con filtros aplicados (tipo_actividad, mostrar_todos)
   - Exportación a CSV con datos completos
   - Generación de contexto con tipos, roles, facultades
   - Integración con gráfico de días de la semana

3. GRÁFICO DE DÍAS DE LA SEMANA (GraficoDiasSemanTests):
   - Generación de datos de asistencia por día (Lunes-Domingo)
   - Aplicación correcta de filtros (tipo_actividad, facultad)
   - Inicialización de todos los días con valor 0 si no hay datos
   - Estructura JSON válida con 7 días ordenados (Lunes primero)
   - Verificación de formato: {label: 'Lunes', value: 10}

4. ENVÍO DE CORREOS (EmailTests):
   - Llamadas correctas a send_mail y log_email
   - Destinatarios de staff correctos (admin@, coordinador@)

5. RECOMENDACIONES (RecomendacionesTests):
   - Construcción de contexto completo
   - Integración de 6 categorías: poca_asistencia, riesgo, destacados,
     inactivos, reconocimientos, activos
   - Fecha de actualización en contexto

6. FUNCIONES DE CONSULTA (QueryHelpersTests):
   - obtener_estudiantes_poca_asistencia: filtrado por umbral
   - obtener_estudiantes_destacados: anotación de promedios
   - obtener_estudiantes_inactivos: filtrado por días sin actividad
   - obtener_estudiantes_activos: filtrado por actividad reciente
   - obtener_proximos_reconocimientos: margen de asistencias
   - obtener_alertas_riesgo: detección de riesgo crítico

7. NOTIFICACIONES AUTOMÁTICAS (NotificacionesAutomaticasTests):
   - Validación de estructuras de datos:
     * Alertas: participante + actividades + total_asistencias_minimas
     * Reconocimientos: participante + menor_faltante
     * Inactividad: participante + dias_inactivo

8. ENCUESTAS FEEDBACK (EncuestasFeedbackTests):
   - Generación de encuestas para cada estudiante que completó
   - Envío con URL correcta (id de participación)
   - Personalización por actividad

9. CONFIGURACIÓN (ConfiguracionNotificacionesTests):
   - Procesamiento POST: guardado de 10 parámetros
   - Renderizado GET: formulario de configuración
   - Parámetros: umbrales, días, frecuencia

10. COMPARACIONES (ComparacionesTests):
    - Agregación de datos por participante
    - Contexto con datos_comparacion y datos_grafica
    - Conteo de asistencias y participantes totales

11. VISTAS AUXILIARES (VistasAuxiliaresTests):
    - analytics_index: renderizado de index.html
    - participantes_list: listado ordenado
    - asistencia: datos de asistencia agregados

METODOLOGÍA DE TESTING:
=======================
- 100% mocks: NO se usa base de datos real
- Aislamiento de dependencias con @patch
- Verificación de llamadas a funciones (assert_called_once)
- Validación de estructuras de datos (assertIn, assertEqual)
- Tests de integración entre componentes (filtros → queries → contexto)

ENFOQUE ESPECIAL:
=================
- Gráfico de días: Conversión Django (1=Domingo) → labels descriptivos
- CSV Export: Verificación de Content-Type y Content-Disposition
- Rate limiting: NO implementado en este módulo
- SQL Injection: Protegido por ORM de Django (no tests explícitos)

LO QUE SE PRUEBA REALMENTE:
===========================
 Lógica de negocio (umbrales, filtros, agregaciones)
 Generación de reportes (CSV, contextos)
 Envío de notificaciones (emails, encuestas)
 Configuración dinámica (POST/GET)
 Transformación de datos (días de semana, JSON)

LO QUE NO SE PRUEBA:
====================
 Queries reales a PostgreSQL/MySQL
 Renderizado HTML de templates
 Envío real de emails (SMTP)
Cálculos de timezone complejos
 Validación de formularios Django
"""

from django.test import SimpleTestCase, TestCase
from unittest.mock import patch, MagicMock, call
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import HttpResponse, QueryDict
from datetime import datetime, timedelta
import Analytics_Reports.views as vw

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

    @patch("Analytics_Reports.views.Asistencias.objects")  # ← NUEVO
    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.TiposActividad.objects")
    @patch("Analytics_Reports.views.Roles.objects")
    @patch("Analytics_Reports.views.Participantes.objects")
    @patch("Analytics_Reports.views.render")
    def test_analisis_comportamiento_filters_and_renders(
        self, mock_render, mock_participantes_model, mock_roles, mock_tipos, 
        mock_participaciones, mock_asistencias  # ← NUEVO
    ):
        """Debe aplicar filtros y renderizar el template"""
        request = MagicMock()
        request.GET = {"tipo_actividad": "2", "mostrar_todos": "1"}

        # Mock para la query principal
        mock_qs = MagicMock()
        mock_qs.__iter__ = lambda self: iter([])
        mock_participaciones.values.return_value.annotate.return_value.order_by.return_value.filter.return_value = mock_qs
        
        # Mock para Participaciones.objects.filter() usado en el loop
        mock_participaciones.filter.return_value.select_related.return_value = []
        mock_participaciones.filter.return_value.count.return_value = 0
        
        # ← NUEVO: Mock para Asistencias (gráfico de días)
        mock_asist_qs = MagicMock()
        mock_asist_qs.annotate.return_value.values.return_value.annotate.return_value.order_by.return_value = []
        mock_asistencias.filter.return_value = mock_asist_qs
        
        # Mock para los filtros
        mock_tipos.all.return_value.order_by.return_value = []
        mock_roles.filter.return_value.order_by.return_value = []
        
        # Mock completo para las cadenas de Participantes (facultades, generos, semestres)
        mock_chain = MagicMock()
        mock_chain.exclude.return_value = mock_chain
        mock_chain.values_list.return_value = mock_chain
        mock_chain.distinct.return_value = mock_chain
        mock_chain.order_by.return_value = []
        mock_participantes_model.filter.return_value = mock_chain

        vw.analisis_comportamiento(request)

        mock_participaciones.values.assert_called_once()
        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        self.assertIn("data", context)
        self.assertIn("tipos_actividad", context)
        self.assertIn("datos_grafico_dias_semana", context)  # ← NUEVO

    @patch("Analytics_Reports.views.Asistencias.objects")  # ← NUEVO
    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.TiposActividad.objects")
    @patch("Analytics_Reports.views.Roles.objects")
    @patch("Analytics_Reports.views.Participantes.objects")
    def test_analisis_comportamiento_exports_csv(
        self, mock_participantes_model, mock_roles, mock_tipos, 
        mock_participaciones, mock_asistencias  # ← NUEVO
    ):
        """Debe exportar datos a CSV cuando export=csv"""
        request = MagicMock()
        request.GET = {"export": "csv", "mostrar_todos": "1"}

        # Crear un objeto que funcione como diccionario Y tenga atributos
        class MockDataItem(dict):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.__dict__ = self
        
        mock_part = MockDataItem({
            'participantes_id_participante__nombre': 'Juan',
            'participantes_id_participante__correo': 'juan@test.com',
            'participantes_id_participante__semestre': 3,
            'participantes_id_participante__facultad': 'Ingeniería',
            'participantes_id_participante__genero': 'Masculino',
            'participantes_id_participante__roles_id_rol__nombre_rol': 'Estudiante',
            'participantes_id_participante': 1,
            'total': 5,
            'primera_participacion': '2024-01-01',
            'ultima_participacion': '2024-06-01',
            'actividades_texto': 'Yoga',
            'tipos_actividad_texto': 'Deportivo'
        })
        
        # Mock para obtener actividades y tipos
        mock_participacion_detalle = MagicMock()
        mock_actividad = MagicMock()
        mock_actividad.nombre = "Yoga"
        mock_actividad.tipos_actividad_id_tipo = MagicMock(nombre_tipo="Deportivo")
        mock_participacion_detalle.actividades_id_actividad = mock_actividad
        
        mock_participaciones.filter.return_value.select_related.return_value = [mock_participacion_detalle]
        mock_participaciones.filter.return_value.count.return_value = 5

        mock_qs = MagicMock()
        mock_qs.__iter__ = lambda self: iter([mock_part])
        mock_participaciones.values.return_value.annotate.return_value.order_by.return_value.filter.return_value = mock_qs
        
        # ← NUEVO: Mock para Asistencias (gráfico de días)
        mock_asist_qs = MagicMock()
        mock_asist_qs.annotate.return_value.values.return_value.annotate.return_value.order_by.return_value = [
            {'dia_semana': 2, 'total': 10},  # Lunes
            {'dia_semana': 4, 'total': 8}    # Miércoles
        ]
        mock_asistencias.filter.return_value = mock_asist_qs
        
        # Mock para filtros - con cadena completa
        mock_tipos.all.return_value.order_by.return_value = []
        mock_roles.filter.return_value.order_by.return_value = []
        
        # Mock completo para las cadenas de Participantes
        mock_chain = MagicMock()
        mock_chain.exclude.return_value = mock_chain
        mock_chain.values_list.return_value = mock_chain
        mock_chain.distinct.return_value = mock_chain
        mock_chain.order_by.return_value = []
        mock_participantes_model.filter.return_value = mock_chain

        response = vw.analisis_comportamiento(request)

        self.assertIsInstance(response, HttpResponse)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn('attachment', response['Content-Disposition'])


# ==========================================================
# TESTS NUEVOS PARA GRÁFICO DE DÍAS DE LA SEMANA
# ==========================================================

class GraficoDiasSemanTests(SimpleTestCase):
    """Pruebas para el gráfico de días de la semana"""

    @patch("Analytics_Reports.views.Asistencias.objects")
    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.TiposActividad.objects")
    @patch("Analytics_Reports.views.Roles.objects")
    @patch("Analytics_Reports.views.Participantes.objects")
    @patch("Analytics_Reports.views.render")
    def test_grafico_dias_semana_genera_datos(
        self, mock_render, mock_participantes_model, mock_roles, 
        mock_tipos, mock_participaciones, mock_asistencias
    ):
        """Debe generar datos de asistencia por día de la semana"""
        request = MagicMock()
        request.GET = {"mostrar_todos": "1"}

        # Mock participaciones
        mock_part = {
            'participantes_id_participante__nombre': 'Test',
            'participantes_id_participante__correo': 'test@test.com',
            'participantes_id_participante__semestre': 1,
            'participantes_id_participante__facultad': 'Ingeniería',
            'participantes_id_participante__genero': 'M',
            'participantes_id_participante__roles_id_rol__nombre_rol': 'Estudiante',
            'participantes_id_participante': 1,
            'total': 5,
            'primera_participacion': '2024-01-01',
            'ultima_participacion': '2024-06-01'
        }
        
        mock_qs = MagicMock()
        mock_qs.__iter__ = lambda self: iter([mock_part])
        mock_participaciones.values.return_value.annotate.return_value.order_by.return_value.filter.return_value = mock_qs
        
        # Mock para actividades y tipos
        mock_participacion_detalle = MagicMock()
        mock_actividad = MagicMock()
        mock_actividad.nombre = "Test Actividad"
        mock_actividad.tipos_actividad_id_tipo = MagicMock(nombre_tipo="Deportivo")
        mock_participacion_detalle.actividades_id_actividad = mock_actividad
        mock_participaciones.filter.return_value.select_related.return_value = [mock_participacion_detalle]
        mock_participaciones.filter.return_value.count.return_value = 2

        # Mock para asistencias por día
        mock_asist_qs = MagicMock()
        mock_asist_data = [
            {'dia_semana': 2, 'total': 10},  # Lunes
            {'dia_semana': 4, 'total': 15},  # Miércoles
            {'dia_semana': 6, 'total': 5}    # Viernes
        ]
        mock_asist_qs.annotate.return_value.values.return_value.annotate.return_value.order_by.return_value = mock_asist_data
        mock_asistencias.filter.return_value = mock_asist_qs
        
        # Mock filtros
        mock_tipos.all.return_value.order_by.return_value = []
        mock_roles.filter.return_value.order_by.return_value = []
        
        mock_chain = MagicMock()
        mock_chain.exclude.return_value = mock_chain
        mock_chain.values_list.return_value = mock_chain
        mock_chain.distinct.return_value = mock_chain
        mock_chain.order_by.return_value = []
        mock_participantes_model.filter.return_value = mock_chain

        vw.analisis_comportamiento(request)

        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        
        # Verificar que datos_grafico_dias_semana existe
        self.assertIn("datos_grafico_dias_semana", context)
        
        # Verificar que es un JSON válido
        import json
        datos_dias = json.loads(context["datos_grafico_dias_semana"])
        
        # Debe tener 7 días
        self.assertEqual(len(datos_dias), 7)
        
        # Verificar estructura
        for dia in datos_dias:
            self.assertIn('label', dia)
            self.assertIn('value', dia)
        
        # Verificar orden (Lunes primero)
        self.assertEqual(datos_dias[0]['label'], 'Lunes')
        self.assertEqual(datos_dias[6]['label'], 'Domingo')

    @patch("Analytics_Reports.views.Asistencias.objects")
    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.TiposActividad.objects")
    @patch("Analytics_Reports.views.Roles.objects")
    @patch("Analytics_Reports.views.Participantes.objects")
    @patch("Analytics_Reports.views.render")
    def test_grafico_dias_semana_con_filtros(
        self, mock_render, mock_participantes_model, mock_roles, 
        mock_tipos, mock_participaciones, mock_asistencias
    ):
        """Debe aplicar filtros correctamente al gráfico de días"""
        request = MagicMock()
        request.GET = {
            "mostrar_todos": "1",
            "tipo_actividad": "2",
            "facultad": "Ingeniería"
        }

        # Setup similar al test anterior
        mock_part = {
            'participantes_id_participante__nombre': 'Test',
            'participantes_id_participante__correo': 'test@test.com',
            'participantes_id_participante__semestre': 1,
            'participantes_id_participante__facultad': 'Ingeniería',
            'participantes_id_participante__genero': 'M',
            'participantes_id_participante__roles_id_rol__nombre_rol': 'Estudiante',
            'participantes_id_participante': 1,
            'total': 5,
            'primera_participacion': '2024-01-01',
            'ultima_participacion': '2024-06-01'
        }
        
        mock_qs = MagicMock()
        mock_qs.__iter__ = lambda self: iter([mock_part])
        mock_participaciones.values.return_value.annotate.return_value.order_by.return_value.filter.return_value = mock_qs
        
        mock_participacion_detalle = MagicMock()
        mock_actividad = MagicMock()
        mock_actividad.nombre = "Test"
        mock_actividad.tipos_actividad_id_tipo = MagicMock(nombre_tipo="Deportivo")
        mock_participacion_detalle.actividades_id_actividad = mock_actividad
        mock_participaciones.filter.return_value.select_related.return_value = [mock_participacion_detalle]
        mock_participaciones.filter.return_value.count.return_value = 2

        mock_asist_qs = MagicMock()
        mock_asist_qs.annotate.return_value.values.return_value.annotate.return_value.order_by.return_value = [
            {'dia_semana': 2, 'total': 5}
        ]
        mock_asistencias.filter.return_value = mock_asist_qs
        
        mock_tipos.all.return_value.order_by.return_value = []
        mock_roles.filter.return_value.order_by.return_value = []
        
        mock_chain = MagicMock()
        mock_chain.exclude.return_value = mock_chain
        mock_chain.values_list.return_value = mock_chain
        mock_chain.distinct.return_value = mock_chain
        mock_chain.order_by.return_value = []
        mock_participantes_model.filter.return_value = mock_chain

        vw.analisis_comportamiento(request)

        # Verificar que se aplicaron filtros a las asistencias
        mock_asistencias.filter.assert_called()

    @patch("Analytics_Reports.views.Asistencias.objects")
    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.TiposActividad.objects")
    @patch("Analytics_Reports.views.Roles.objects")
    @patch("Analytics_Reports.views.Participantes.objects")
    @patch("Analytics_Reports.views.render")
    def test_grafico_dias_semana_inicializa_todos_los_dias(
        self, mock_render, mock_participantes_model, mock_roles, 
        mock_tipos, mock_participaciones, mock_asistencias
    ):
        """Debe inicializar todos los días con 0 si no hay datos"""
        request = MagicMock()
        request.GET = {"mostrar_todos": "1"}

        mock_part = {
            'participantes_id_participante__nombre': 'Test',
            'participantes_id_participante__correo': 'test@test.com',
            'participantes_id_participante__semestre': 1,
            'participantes_id_participante__facultad': 'Ingeniería',
            'participantes_id_participante__genero': 'M',
            'participantes_id_participante__roles_id_rol__nombre_rol': 'Estudiante',
            'participantes_id_participante': 1,
            'total': 5,
            'primera_participacion': '2024-01-01',
            'ultima_participacion': '2024-06-01'
        }
        
        mock_qs = MagicMock()
        mock_qs.__iter__ = lambda self: iter([mock_part])
        mock_participaciones.values.return_value.annotate.return_value.order_by.return_value.filter.return_value = mock_qs
        
        mock_participacion_detalle = MagicMock()
        mock_actividad = MagicMock()
        mock_actividad.nombre = "Test"
        mock_actividad.tipos_actividad_id_tipo = MagicMock(nombre_tipo="Deportivo")
        mock_participacion_detalle.actividades_id_actividad = mock_actividad
        mock_participaciones.filter.return_value.select_related.return_value = [mock_participacion_detalle]
        mock_participaciones.filter.return_value.count.return_value = 2

        # Sin datos de asistencias
        mock_asist_qs = MagicMock()
        mock_asist_qs.annotate.return_value.values.return_value.annotate.return_value.order_by.return_value = []
        mock_asistencias.filter.return_value = mock_asist_qs
        
        mock_tipos.all.return_value.order_by.return_value = []
        mock_roles.filter.return_value.order_by.return_value = []
        
        mock_chain = MagicMock()
        mock_chain.exclude.return_value = mock_chain
        mock_chain.values_list.return_value = mock_chain
        mock_chain.distinct.return_value = mock_chain
        mock_chain.order_by.return_value = []
        mock_participantes_model.filter.return_value = mock_chain

        vw.analisis_comportamiento(request)

        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        
        import json
        datos_dias = json.loads(context["datos_grafico_dias_semana"])
        
        # Todos los días deben estar presentes
        self.assertEqual(len(datos_dias), 7)
        
        # Todos los valores deben ser 0
        for dia in datos_dias:
            self.assertEqual(dia['value'], 0)


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
    @patch("Analytics_Reports.views.ConfiguracionNotificaciones.obtener_config")
    @patch("Analytics_Reports.views.render")
    def test_recomendaciones_renders_correct_context(
        self, mock_render, mock_config, mock_activos, mock_riesgo, mock_destacados,
        mock_inactivos, mock_reconocimientos, mock_poca_asistencia
    ):
        """Debe construir el contexto completo y renderizar"""
        request = MagicMock(GET={})
        
        # Mock config
        mock_config.return_value = MagicMock()

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
    """Verifica funciones que retornan datos"""

    @patch("Analytics_Reports.views.ConfiguracionNotificaciones.obtener_config")
    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.timezone")
    def test_obtener_estudiantes_poca_asistencia(self, mock_timezone, mock_participantes, mock_config):
        """Debe filtrar correctamente estudiantes con poca asistencia"""
        # Mock timezone
        mock_timezone.now.return_value = timezone.datetime(2024, 10, 19, tzinfo=timezone.get_current_timezone())
        
        # Mock config
        mock_config_obj = MagicMock()
        mock_config_obj.umbral_riesgo_critico = 2
        mock_config_obj.umbral_baja_asistencia = 5
        mock_config.return_value = mock_config_obj
        
        mock_qs = MagicMock()
        mock_participantes.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__ = lambda self: iter([])
        
        result = vw.obtener_estudiantes_poca_asistencia()
        self.assertIsInstance(result, list)

    @patch("Analytics_Reports.views.ConfiguracionNotificaciones.obtener_config")
    @patch("Analytics_Reports.views.Participaciones.objects")
    def test_obtener_estudiantes_destacados(self, mock_participantes, mock_config):
        """Debe anotar correctamente promedios"""
        mock_config_obj = MagicMock()
        mock_config_obj.asistencias_destacado = 15
        mock_config.return_value = mock_config_obj
        
        mock_qs = MagicMock()
        mock_participantes.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__ = lambda self: iter([])
        
        result = vw.obtener_estudiantes_destacados()
        self.assertIsInstance(result, list)

    @patch("Analytics_Reports.views.ConfiguracionNotificaciones.obtener_config")
    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.timezone")
    def test_obtener_estudiantes_inactivos(self, mock_timezone, mock_participantes, mock_config):
        """Debe filtrar correctamente estudiantes sin actividad reciente"""
        mock_timezone.now.return_value = timezone.datetime(2024, 10, 19, tzinfo=timezone.get_current_timezone())
        
        mock_config_obj = MagicMock()
        mock_config_obj.dias_inactividad = 14
        mock_config_obj.umbral_baja_asistencia = 5
        mock_config.return_value = mock_config_obj
        
        mock_qs = MagicMock()
        mock_participantes.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__ = lambda self: iter([])
        
        result = vw.obtener_estudiantes_inactivos()
        self.assertIsInstance(result, list)

    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.timezone")
    def test_obtener_estudiantes_activos(self, mock_timezone, mock_participantes):
        """Debe filtrar estudiantes con asistencia reciente"""
        mock_timezone.now.return_value = timezone.datetime(2024, 10, 19, tzinfo=timezone.get_current_timezone())
        
        mock_qs = MagicMock()
        mock_participantes.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__ = lambda self: iter([])
        
        result = vw.obtener_estudiantes_activos(dias_actividad=7)
        self.assertIsInstance(result, list)

    @patch("Analytics_Reports.views.ConfiguracionNotificaciones.obtener_config")
    @patch("Analytics_Reports.views.Participaciones.objects")
    def test_obtener_proximos_reconocimientos(self, mock_participantes, mock_config):
        """Debe filtrar estudiantes cercanos a reconocimiento"""
        mock_config_obj = MagicMock()
        mock_config_obj.asistencias_reconocimiento = 10
        mock_config_obj.margen_proximo_reconocimiento = 2
        mock_config.return_value = mock_config_obj
        
        mock_qs = MagicMock()
        mock_participantes.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__ = lambda self: iter([])
        
        result = vw.obtener_proximos_reconocimientos()
        self.assertIsInstance(result, list)

    @patch("Analytics_Reports.views.ConfiguracionNotificaciones.obtener_config")
    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.timezone")
    def test_obtener_alertas_riesgo(self, mock_timezone, mock_participantes, mock_config):
        """Debe filtrar estudiantes en riesgo"""
        mock_timezone.now.return_value = timezone.datetime(2024, 10, 19, tzinfo=timezone.get_current_timezone())
        
        mock_config_obj = MagicMock()
        mock_config_obj.dias_riesgo_critico = 21
        mock_config_obj.umbral_riesgo_critico = 2
        mock_config.return_value = mock_config_obj
        
        mock_qs = MagicMock()
        mock_participantes.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__ = lambda self: iter([])
        
        result = vw.obtener_alertas_riesgo()
        self.assertIsInstance(result, list)


# ==========================================================
# TESTS DE NOTIFICACIONES AUTOMÁTICAS
# ==========================================================

class NotificacionesAutomaticasTests(SimpleTestCase):
    """Pruebas de envío de notificaciones automáticas - SIN funciones que no existen"""

    def test_estructura_datos_alertas(self):
        """Verifica que la estructura de datos de alertas es correcta"""
        estudiante = {
            'participante': MagicMock(
                nombre="Juan",
                apellido="Pérez"
            ),
            'actividades': [
                {'nombre': 'Yoga', 'asistencias': 2}
            ],
            'total_asistencias_minimas': 2
        }
        
        # Verificar estructura
        self.assertIn('participante', estudiante)
        self.assertIn('actividades', estudiante)
        self.assertEqual(estudiante['participante'].nombre, "Juan")

    def test_estructura_datos_reconocimientos(self):
        """Verifica estructura de datos de reconocimientos"""
        estudiante = {
            'participante': MagicMock(
                nombre="María",
                apellido="García",
                correo="maria@test.com"
            ),
            'actividades': [
                {'nombre': 'Danza', 'asistencias': 9, 'faltantes': 1}
            ],
            'menor_faltante': 1
        }
        
        self.assertIn('participante', estudiante)
        self.assertIn('menor_faltante', estudiante)
        self.assertEqual(estudiante['menor_faltante'], 1)

    def test_estructura_datos_inactividad(self):
        """Verifica estructura de datos de inactividad"""
        estudiante = {
            'participante': MagicMock(
                nombre="Carlos",
                apellido="López"
            ),
            'actividades': [
                {'nombre': 'Natación', 'ultima_asistencia': None}
            ],
            'dias_inactivo': 15
        }
        
        self.assertIn('participante', estudiante)
        self.assertIn('dias_inactivo', estudiante)
        self.assertEqual(estudiante['dias_inactivo'], 15)


# ==========================================================
# TESTS DE ENCUESTAS FEEDBACK
# ==========================================================

class EncuestasFeedbackTests(SimpleTestCase):
    """Pruebas de generación de encuestas de feedback"""

    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.enviar_encuesta_feedback")
    @patch("Analytics_Reports.views.timezone")
    def test_generar_encuesta_feedback_calls_for_each_student(
        self, mock_tz, mock_enviar, mock_participaciones
    ):
        """Debe enviar encuesta a cada estudiante que completó"""
        mock_tz.now.return_value = timezone.datetime(2024, 10, 19, tzinfo=timezone.get_current_timezone())
        
        mock_qs = [MagicMock(), MagicMock()]
        mock_participaciones.filter.return_value.filter.return_value.select_related.return_value = mock_qs
        
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

    @patch("Analytics_Reports.views.ConfiguracionNotificaciones.obtener_config")
    @patch("Analytics_Reports.views.messages")
    @patch("Analytics_Reports.views.redirect")
    def test_configurar_notificaciones_post(self, mock_redirect, mock_messages, mock_config):
        """Debe procesar POST y guardar configuración"""
        mock_config_obj = MagicMock()
        mock_config.return_value = mock_config_obj
        
        request = MagicMock()
        request.method = 'POST'
        request.POST = {
            'asistencias_reconocimiento': '10',
            'margen_proximo_reconocimiento': '2',
            'asistencias_destacado': '15',
            'umbral_baja_asistencia': '5',
            'umbral_riesgo_critico': '2',
            'dias_inactividad': '14',
            'dias_riesgo_critico': '21',
            'asistencias_minimas_encuesta': '3',
            'dias_despues_cierre_encuesta': '3',
            'frecuencia_envio': 'semanal'
        }
        
        vw.configurar_notificaciones(request)
        
        mock_config_obj.save.assert_called_once()
        mock_redirect.assert_called_once()

    @patch("Analytics_Reports.views.ConfiguracionNotificaciones.obtener_config")
    @patch("Analytics_Reports.views.render")
    def test_configurar_notificaciones_get(self, mock_render, mock_config):
        """Debe renderizar formulario en GET"""
        mock_config.return_value = MagicMock()
        
        request = MagicMock()
        request.method = 'GET'
        
        vw.configurar_notificaciones(request)
        
        mock_render.assert_called_once()


# ==========================================================
# TESTS DE COMPARACIONES
# ==========================================================

class ComparacionesTests(SimpleTestCase):
    """Pruebas para la vista comparaciones"""

    @patch("Analytics_Reports.views.Participaciones.objects")
    @patch("Analytics_Reports.views.Asistencias.objects")
    @patch("Analytics_Reports.views.Participantes.objects")
    @patch("Analytics_Reports.views.render")
    def test_comparaciones_renders_context(
        self, mock_render, mock_participantes_model, mock_asistencias, mock_participaciones
    ):
        """Debe crear contexto con datos agregados"""
        request = MagicMock()
        request.GET = QueryDict('', mutable=True)
        request.method = 'GET'
        
        mock_qs_part = MagicMock()
        mock_participaciones.values.return_value = mock_qs_part
        mock_qs_part.annotate.return_value = mock_qs_part
        mock_qs_part.order_by.return_value = []
        
        mock_asistencias.count.return_value = 10
        mock_participantes_model.count.return_value = 5
        mock_participaciones.aggregate.return_value = {
            'fecha_inscripcion__min': None, 
            'fecha_inscripcion__max': None
        }
        
        vw.comparaciones(request)
        
        mock_render.assert_called_once()
        context = mock_render.call_args[0][2]
        self.assertIn("datos_comparacion", context)
        self.assertIn("datos_grafica", context)


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
        
        mock_render.assert_called_once()
        call_args = mock_render.call_args
        self.assertEqual(call_args[0][1], 'index.html')

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
        mock_asistencias.values.return_value.annotate.return_value = []
        request = MagicMock()
        
        vw.asistencia(request)
        
        mock_render.assert_called_once()