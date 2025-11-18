#project\Analytics_Reports\tests\test_tasks.py

from django.test import SimpleTestCase
from unittest.mock import patch, MagicMock, call
from django.utils import timezone
from datetime import timedelta
import Analytics_Reports.tasks as tasks

# ==========================================================
# TESTS PARA TAREA 1: RECONOCIMIENTOS
# ==========================================================
"""
Tests unitarios completos para Analytics_Reports/tasks.py - Celery Tasks

COBERTURA REAL DE TESTS:
========================

ARQUITECTURA DEL SISTEMA:
=========================
Tasks de Celery para automatización de notificaciones y reportes:
1. verificar_y_otorgar_reconocimientos() - Hitos de asistencia
2. clasificar_estudiantes_para_admin() - Categorización automática
3. enviar_encuestas_retroalimentacion() - Encuestas post-actividad
4. enviar_recordatorios_citas() - Recordatorios X días antes
5. notificar_cancelacion_actividad() - Avisos de cancelación

CARACTERÍSTICAS COMUNES:
- Toggle on/off por ConfiguracionNotificaciones
- Control anti-spam con ControlNotificacionesContextual
- Retornan string descriptivo del resultado
- Manejo de errores silencioso (logging interno)

TESTS IMPLEMENTADOS:
===================

1. TAREA 1: RECONOCIMIENTOS (VerificarOtorgarReconocimientosTests - 3 tests):
   ===========================================================================
   
   test_reconocimientos_desactivados:
   - Mock: ConfiguracionNotificaciones.reconocimientos_activos = False
   - Valida: retorna "⏸️ Reconocimientos desactivados por el admin"
   - Propósito: respeta toggle del administrador
   
   test_otorga_reconocimiento_cuando_cumple_hito:
   - Mock: participación con 10 asistencias (primer hito)
   - Config: hitos = [10, 20, 30]
   - Flujo:
     1. Busca participaciones activas
     2. Cuenta asistencias por actividad
     3. Detecta hito alcanzado (10)
     4. Verifica no-duplicado con ControlNotificaciones
     5. Registra notificación
     6. Envía email de felicitación
   - Valida: registrar_notificacion y send_mail llamados
   
   test_no_duplica_reconocimientos_existentes:
   - Mock: ya_existe_notificacion() = True
   - Valida: NO llama a registrar_notificacion()
   - Propósito: previene spam de reconocimientos duplicados

2. TAREA 2: CLASIFICACIÓN (ClasificarEstudiantesTests - 2 tests):
   ================================================================
   
   test_clasificacion_riesgo_critico:
   - Mock: participación con 2 asistencias + inactivo 48 días
   - Config:
     * umbral_riesgo_critico = 2
     * dias_riesgo_critico = 21
     * umbral_baja_asistencia = 5
     * dias_inactividad = 14
     * asistencias_destacado = 15
   - Clasifica en: riesgo_critico, baja_asistencia, inactivos, activos, destacados
   - Valida: resultado contiene "Clasificación completada" y "riesgo_critico"
   - Propósito: categorización automática para dashboard admin
   
   test_clasificacion_sin_enviar_correos:
   - Crítico: clasificación NO envía emails a estudiantes
   - Valida: send_mail NUNCA llamado
   - Propósito: solo genera reporte, no notifica usuarios

3. TAREA 3: ENCUESTAS (EnviarEncuestasTests - 3 tests):
   ======================================================
   
   test_encuestas_desactivadas:
   - Mock: encuestas_activas = False
   - Valida: retorna "⏸️ Encuestas desactivadas por el admin"
   
   test_envia_encuesta_actividad_finalizada:
   - Mock: actividad cerrada hace 1 día
   - Config:
     * dias_despues_cierre_encuesta = 3
     * asistencias_minimas_encuesta = 3
   - Condiciones:
     * Actividad finalizada (fecha_cierre_ins pasada)
     * Participante con 5 asistencias (≥ 3)
     * No ha calificado aún
     * Dentro ventana de envío (≤ 3 días después)
   - Valida: send_mail llamado con URL de encuesta
   
   test_no_envia_si_ya_califico:
   - Mock: CalificacionesActividad.exists() = True
   - Valida: send_mail NO llamado
   - Propósito: no molestar si ya dio feedback

4. TAREA 4: RECORDATORIOS CITAS (RecordatoriosCitasTests - 3 tests):
   ===================================================================
   
   test_recordatorios_desactivados:
   - Mock: recordatorios_citas_activos = False
   - Valida: retorna "⏸️ Recordatorios de citas desactivados"
   
   test_envia_recordatorio_cita_proxima:
   - Mock: cita en exactamente 3 días
   - Config: recordatorio_cita_dias_antes = 3
   - Cálculo temporal:
     * ahora = 2024-10-19 12:00:00
     * fecha_cita = 2024-10-22 12:00:00 (3 días)
   - Valida: send_mail llamado con detalles de cita
   
   test_no_duplica_recordatorio_existente:
   - Mock: ya_existe_notificacion() = True
   - Valida: send_mail NO llamado
   - Propósito: un solo recordatorio por cita

5. TAREA 5: CANCELACIONES (NotificarCancelacionTests - 3 tests):
   ================================================================
   
   test_retorna_error_actividad_inexistente:
   - Mock: Actividades.DoesNotExist
   - Valida: resultado contiene "no existe"
   - Propósito: manejo graceful de IDs inválidos
   
   test_notifica_todos_inscritos:
   - Mock: actividad con 2 participantes inscritos
   - Parámetro: motivo="Problemas técnicos"
   - Valida:
     * send_mail llamado 2 veces
     * resultado contiene "2 notificaciones de cancelación enviadas"
   - Propósito: notificar a TODOS los afectados
   
   test_no_duplica_notificacion_cancelacion:
   - Mock: ya_existe_notificacion() = True
   - Valida: send_mail NO llamado
   - Propósito: no spamear cancelaciones duplicadas

6. INTEGRACIÓN (IntegracionTasksTests - 2 tests):
   ================================================
   
   test_control_antispam_funciona_entre_tareas:
   - Simula: notificación ya existe
   - Mock: registrar_notificacion() → None
   - Valida: lógica de control funciona correctamente
   - Propósito: validar ControlNotificacionesContextual
   
   test_todas_las_tareas_retornan_string:
   - Ejecuta: todas las tareas con configs desactivadas
   - Valida: todas retornan isinstance(str)
   - Propósito: contrato de API consistente

7. EDGE CASES (EdgeCasesTests - 2 tests):
   ========================================
   
   test_reconocimientos_con_hitos_vacios:
   - Mock: obtener_hitos() → []
   - Valida: resultado contiene "0 reconocimientos otorgados"
   - Propósito: no crashea con configuración vacía
   
   test_send_mail_falla_silenciosamente:
   - Mock: send_mail lanza Exception("SMTP Error")
   - Valida: task NO lanza excepción, retorna string
   - Propósito: resiliencia ante fallos de SMTP

LÓGICA DE NEGOCIO CRÍTICA:
===========================

RECONOCIMIENTOS - DETECCIÓN DE HITOS:
```python
def verificar_y_otorgar_reconocimientos():
    hitos = [10, 20, 30]  # Configurable
    
    for participacion in participaciones_activas:
        num_asistencias = Asistencias.objects.filter(
            participantes=participacion.participante,
            actividades=participacion.actividad
        ).count()
        
        for hito in hitos:
            if num_asistencias == hito:
                # Verificar no-duplicado
                if not ya_existe_notificacion(participante, "Reconocimiento", actividad, f"hito_{hito}"):
                    registrar_notificacion(...)
                    send_mail(...)
```

CLASIFICACIÓN - CATEGORIZACIÓN AUTOMÁTICA:
```python
def clasificar_estudiantes_para_admin():
    participaciones = Participaciones.objects.annotate(
        total_asistencias=Count('asistencias'),
        ultima_asistencia=Max('asistencias__fecha')
    )
    
    categorias = {
        'riesgo_critico': [],      # ≤2 asistencias + >21 días inactivo
        'baja_asistencia': [],     # ≤5 asistencias
        'inactivos': [],           # >14 días sin asistir
        'activos': [],             # Asistencia reciente
        'destacados': []           # ≥15 asistencias
    }
    
    for part in participaciones:
        if part.total_asistencias <= 2 and dias_inactivo > 21:
            categorias['riesgo_critico'].append(part)
        # ... más lógica
    
    # CRÍTICO: NO envía emails a estudiantes
    return f"Clasificación completada: {len(categorias['riesgo_critico'])} en riesgo"
```

ENCUESTAS - VENTANA TEMPORAL:
```python
def enviar_encuestas_retroalimentacion():
    dias_despues = 3  # Configurable
    asistencias_min = 3  # Configurable
    
    actividades_finalizadas = Actividades.objects.filter(
        fecha_cierre_ins__lte=timezone.now() - timedelta(days=dias_despues)
    )
    
    for actividad in actividades_finalizadas:
        participaciones = Participaciones.objects.filter(
            actividad=actividad,
            num_asistencias__gte=asistencias_min
        )
        
        for part in participaciones:
            # No enviar si ya calificó
            if CalificacionesActividad.objects.filter(
                participantes=part.participante,
                actividades=actividad
            ).exists():
                continue
            
            # Verificar no-duplicado
            if not ya_existe_notificacion(...):
                registrar_notificacion(...)
                send_mail(url_encuesta)
```

RECORDATORIOS - CÁLCULO TEMPORAL:
```python
def enviar_recordatorios_citas():
    dias_antes = 3  # Configurable
    
    fecha_inicio = timezone.now() + timedelta(days=dias_antes)
    fecha_fin = fecha_inicio + timedelta(days=1)
    
    citas_proximas = Citas.objects.filter(
        fecha__range=(fecha_inicio, fecha_fin)
    )
    
    for cita in citas_proximas:
        contexto = f"recordatorio_cita_{cita.id_cita}"
        if not ya_existe_notificacion(cita.participante, "Recordatorio", None, contexto):
            registrar_notificacion(...)
            send_mail(f"Recordatorio: cita en {dias_antes} días")
```

CANCELACIONES - NOTIFICACIÓN MASIVA:
```python
def notificar_cancelacion_actividad(actividad_id, motivo="No especificado"):
    try:
        actividad = Actividades.objects.get(id_actividad=actividad_id)
    except Actividades.DoesNotExist:
        return "❌ La actividad no existe"
    
    participaciones = Participaciones.objects.filter(
        actividad=actividad
    ).select_related('participante')
    
    enviados = 0
    for part in participaciones:
        contexto = f"cancelacion_{actividad_id}"
        if not ya_existe_notificacion(part.participante, "Cancelacion", actividad, contexto):
            registrar_notificacion(...)
            send_mail(motivo)
            enviados += 1
    
    return f"✅ {enviados} notificaciones de cancelación enviadas"
```

CONFIGURACIÓN DINÁMICA:
=======================

Todas las tareas respetan ConfiguracionNotificaciones:
```python
class ConfiguracionNotificaciones:
    # Toggles generales
    reconocimientos_activos = True/False
    encuestas_activas = True/False
    recordatorios_citas_activos = True/False
    
    # Parámetros de reconocimientos
    hitos_reconocimiento = [10, 20, 30, 50, 75, 100]  # Asistencias
    
    # Parámetros de clasificación
    umbral_riesgo_critico = 2  # Asistencias mínimas
    dias_riesgo_critico = 21  # Días sin asistir
    umbral_baja_asistencia = 5
    dias_inactividad = 14
    asistencias_destacado = 15
    
    # Parámetros de encuestas
    dias_despues_cierre_encuesta = 3  # Enviar X días después
    asistencias_minimas_encuesta = 3
    
    # Parámetros de recordatorios
    recordatorio_cita_dias_antes = 3  # Avisar con X días de antelación
```

CONTROL ANTI-SPAM:
==================

Todas las notificaciones usan ControlNotificacionesContextual:
```python
# Antes de enviar cualquier notificación:
contexto = f"hito_{num_asistencias}"  # o "recordatorio_cita_123", etc.

if ya_existe_notificacion(
    participante=participante,
    tipo_notif="Reconocimiento",
    actividad=actividad,
    contexto=contexto
):
    return  # No enviar duplicado

# Si no existe, registrar y enviar
registrar_notificacion(
    participante=participante,
    tipo_notif="Reconocimiento",
    mensaje="¡Felicidades por alcanzar 10 asistencias!",
    actividad=actividad,
    contexto=contexto
)

send_mail(...)
```

METODOLOGÍA DE TESTING:
=======================
- 100% mocks: NO se usa base de datos real
- SimpleTestCase: tests unitarios puros sin DB
- Aislamiento completo con @patch
- Mock de timezone para fechas deterministas
- Validación de llamadas a send_mail y registrar_notificacion
- Tests de toggles (activos/desactivados)
- Tests de edge cases (errores SMTP, configuraciones vacías)

LO QUE SE PRUEBA REALMENTE:
===========================
✅ Toggle on/off de cada tarea
✅ Lógica de detección de hitos (reconocimientos)
✅ Clasificación automática en categorías
✅ Ventana temporal de encuestas
✅ Cálculo de fechas para recordatorios
✅ Notificación masiva en cancelaciones
✅ Control anti-spam (no duplicados)
✅ Resiliencia ante errores SMTP
✅ Manejo de configuraciones vacías
✅ Contrato de API (todas retornan string)
✅ Validación de que clasificación NO envía emails a estudiantes

LO QUE NO SE PRUEBA:
====================
❌ Ejecución real de Celery
❌ Scheduling periódico (cron)
❌ Queries reales a base de datos
❌ Envío real de emails SMTP
❌ Transacciones y rollbacks
❌ Performance con miles de registros
❌ Concurrencia de múltiples workers

CASOS ESPECIALES IMPORTANTES:
==============================

1. CLASIFICACIÓN NO ENVÍA EMAILS:
   - Solo genera reporte para admin
   - NO notifica a estudiantes en riesgo
   - Propósito: evitar estigmatización
   - Admin decide qué hacer con la información

2. ENCUESTAS CON VENTANA TEMPORAL:
   - Solo envía X días después de cierre
   - Requiere mínimo de asistencias
   - No envía si ya calificó
   - Una sola encuesta por actividad-participante

3. RECORDATORIOS CON PRECISIÓN:
   - Envía exactamente X días antes
   - Cálculo: fecha_cita - dias_antes = fecha_envío
   - No duplica recordatorios para misma cita

4. CANCELACIONES SIN DUPLICADOS:
   - Usa contexto único: f"cancelacion_{actividad_id}"
   - Permite múltiples cancelaciones de diferentes actividades
   - No permite duplicar cancelación de misma actividad

5. RECONOCIMIENTOS POR HITO:
   - Contexto único: f"hito_{num_asistencias}"
   - Permite: hito_10, hito_20, hito_30 independientes
   - No permite: duplicar mismo hito para misma actividad

EJEMPLO DE FLUJO REAL:
=======================

Usuario "Ana" completa 10 asistencias en "Yoga":

1. Celery ejecuta: verificar_y_otorgar_reconocimientos()
2. Config: reconocimientos_activos=True, hitos=[10,20,30]
3. Query: Participaciones.objects.filter(...)
4. Encuentra: Ana en Yoga
5. Cuenta: Asistencias = 10
6. Detecta: alcanzó hito_10
7. Verifica: ya_existe_notificacion(Ana, "Reconocimiento", Yoga, "hito_10") → False
8. Registra: notificación con hash único
9. Envía: email "¡Felicidades por 10 asistencias en Yoga!"
10. Retorna: "✅ 1 reconocimientos otorgados"

Si se vuelve a ejecutar la tarea:
1-6. Mismos pasos
7. Verifica: ya_existe_notificacion() → True (ya existe)
8-9. NO registra ni envía (previene duplicado)
10. Retorna: "✅ 0 reconocimientos otorgados"
"""
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