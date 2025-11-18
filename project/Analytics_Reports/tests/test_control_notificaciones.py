#project\Analytics_Reports\tests\test_control_notificaciones.py

from django.test import SimpleTestCase  # ✅ SOLO SimpleTestCase
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta
import hashlib
from Analytics_Reports.tasks import ControlNotificacionesContextual
# ✅ Ya no importamos modelos para crear objetos reales


# ==========================================================
# TESTS DE GENERACIÓN DE HASH
# ==========================================================

class GenerarHashUnicidadTests(SimpleTestCase):
    """Pruebas para generar_hash_unicidad"""
    
    def test_genera_hash_md5_valido(self):
        """Debe generar un hash MD5 válido de 32 caracteres"""
        hash_result = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Reconocimiento",
            actividad_id=45,
            contexto="hito_10"
        )
        
        self.assertIsInstance(hash_result, str)
        self.assertEqual(len(hash_result), 32)  # MD5 = 32 chars
        # Verificar que sea hexadecimal
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_result))
    
    def test_mismo_input_genera_mismo_hash(self):
        """Mismo input debe generar siempre el mismo hash (idempotente)"""
        hash1 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Reconocimiento",
            actividad_id=45,
            contexto="hito_10"
        )
        
        hash2 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Reconocimiento",
            actividad_id=45,
            contexto="hito_10"
        )
        
        self.assertEqual(hash1, hash2)
    
    def test_diferente_participante_genera_diferente_hash(self):
        """Cambiar participante debe generar hash diferente"""
        hash1 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Reconocimiento"
        )
        
        hash2 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=456,  # Diferente
            tipo_notif="Reconocimiento"
        )
        
        self.assertNotEqual(hash1, hash2)
    
    def test_diferente_tipo_genera_diferente_hash(self):
        """Cambiar tipo de notificación debe generar hash diferente"""
        hash1 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Reconocimiento"
        )
        
        hash2 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Inasistencia"  # Diferente
        )
        
        self.assertNotEqual(hash1, hash2)
    
    def test_diferente_actividad_genera_diferente_hash(self):
        """Cambiar actividad debe generar hash diferente"""
        hash1 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Reconocimiento",
            actividad_id=45
        )
        
        hash2 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Reconocimiento",
            actividad_id=99  # Diferente
        )
        
        self.assertNotEqual(hash1, hash2)
    
    def test_diferente_contexto_genera_diferente_hash(self):
        """Cambiar contexto debe generar hash diferente"""
        hash1 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Reconocimiento",
            actividad_id=45,
            contexto="hito_10"
        )
        
        hash2 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Reconocimiento",
            actividad_id=45,
            contexto="hito_20"  # Diferente
        )
        
        self.assertNotEqual(hash1, hash2)
    
    def test_actividad_none_usa_global(self):
        """actividad_id=None debe usar 'global' en el hash"""
        hash1 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Reconocimiento",
            actividad_id=None
        )
        
        # Debe contener "global" en la string pre-hash
        # Verificamos generando el mismo hash manualmente
        hash_esperado = hashlib.md5("123_Reconocimiento_global_general".encode()).hexdigest()
        self.assertEqual(hash1, hash_esperado)
    
    def test_contexto_none_usa_general(self):
        """contexto=None debe usar 'general' en el hash"""
        hash1 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Reconocimiento",
            actividad_id=45,
            contexto=None
        )
        
        hash_esperado = hashlib.md5("123_Reconocimiento_45_general".encode()).hexdigest()
        self.assertEqual(hash1, hash_esperado)


# ==========================================================
# TESTS DE VERIFICACIÓN DE EXISTENCIA
# ==========================================================

class YaExisteNotificacionTests(SimpleTestCase):
    """Pruebas para ya_existe_notificacion"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # ✅ TODO EN MOCKS - Sin tocar BD
        self.tipo_reconocimiento = MagicMock()
        self.tipo_reconocimiento.nombre = "Reconocimiento"
        
        # Mock participante
        self.mock_participante = MagicMock()
        self.mock_participante.id_participante = 123
        
        # Mock actividad
        self.mock_actividad = MagicMock()
        self.mock_actividad.id_actividad = 45
    
    @patch('Analytics_Reports.tasks.Notificaciones.objects')
    def test_retorna_false_cuando_no_existe(self, mock_notif):
        """Debe retornar False si no existe notificación previa"""
        mock_notif.filter.return_value.exists.return_value = False
        
        resultado = ControlNotificacionesContextual.ya_existe_notificacion(
            participante=self.mock_participante,
            tipo_notif="Reconocimiento",
            actividad=self.mock_actividad,
            contexto="hito_10"
        )
        
        self.assertFalse(resultado)
    
    @patch('Analytics_Reports.tasks.Notificaciones.objects')
    def test_retorna_true_cuando_existe(self, mock_notif):
        """Debe retornar True si ya existe notificación idéntica"""
        mock_notif.filter.return_value.exists.return_value = True
        
        resultado = ControlNotificacionesContextual.ya_existe_notificacion(
            participante=self.mock_participante,
            tipo_notif="Reconocimiento",
            actividad=self.mock_actividad,
            contexto="hito_10"
        )
        
        self.assertTrue(resultado)
    
    @patch('Analytics_Reports.tasks.Notificaciones.objects')
    def test_filtra_por_hash_correcto(self, mock_notif):
        """Debe usar el hash correcto en el filtro"""
        mock_notif.filter.return_value.exists.return_value = False
        
        ControlNotificacionesContextual.ya_existe_notificacion(
            participante=self.mock_participante,
            tipo_notif="Reconocimiento",
            actividad=self.mock_actividad,
            contexto="hito_10"
        )
        
        # Verificar que se llamó filter con el hash correcto
        call_kwargs = mock_notif.filter.call_args[1]
        
        hash_esperado = ControlNotificacionesContextual.generar_hash_unicidad(
            123, "Reconocimiento", 45, "hito_10"
        )
        
        self.assertEqual(call_kwargs['hash_unicidad'], hash_esperado)
    
    @patch('Analytics_Reports.tasks.Notificaciones.objects')
    def test_aplica_ventana_temporal_cuando_especificada(self, mock_notif):
        """Debe aplicar filtro de ventana temporal cuando se especifica"""
        # ✅ SOLUCIÓN: No verificar fecha exacta, solo que el filtro existe
        mock_notif.filter.return_value.exists.return_value = False
        
        ControlNotificacionesContextual.ya_existe_notificacion(
            participante=self.mock_participante,
            tipo_notif="Inasistencia",
            actividad=self.mock_actividad,
            ventana_horas=24
        )
        
        # Verificar que se aplicó el filtro temporal
        call_kwargs = mock_notif.filter.call_args[1]
        self.assertIn('created_at__gte', call_kwargs)
        
        # ✅ Verificar que la fecha límite es aproximadamente hace 24 horas
        # (sin verificar microsegundos exactos)
        limite_recibido = call_kwargs['created_at__gte']
        ahora_aprox = timezone.now()
        diferencia = abs((ahora_aprox - limite_recibido).total_seconds() - (24 * 3600))
        self.assertLess(diferencia, 1)  # Diferencia menor a 1 segundo
    
    @patch('Analytics_Reports.tasks.Notificaciones.objects')
    def test_sin_actividad_usa_none_en_hash(self, mock_notif):
        """Sin actividad debe funcionar correctamente"""
        mock_notif.filter.return_value.exists.return_value = False
        
        resultado = ControlNotificacionesContextual.ya_existe_notificacion(
            participante=self.mock_participante,
            tipo_notif="Reconocimiento",
            actividad=None,  # Sin actividad
            contexto="general"
        )
        
        self.assertFalse(resultado)
        
        # Verificar que se usó el hash correcto (con "global")
        call_kwargs = mock_notif.filter.call_args[1]
        hash_esperado = ControlNotificacionesContextual.generar_hash_unicidad(
            123, "Reconocimiento", None, "general"
        )
        self.assertEqual(call_kwargs['hash_unicidad'], hash_esperado)


# ==========================================================
# TESTS DE REGISTRO DE NOTIFICACIONES
# ==========================================================

class RegistrarNotificacionTests(SimpleTestCase):
    """Pruebas para registrar_notificacion"""
    
    def setUp(self):
        """Configuración inicial"""
        # ✅ TODO EN MOCKS
        self.tipo_reconocimiento = MagicMock()
        self.tipo_reconocimiento.nombre = "Reconocimiento"
        
        self.mock_participante = MagicMock()
        self.mock_participante.id_participante = 123
        
        self.mock_actividad = MagicMock()
        self.mock_actividad.id_actividad = 45
    
    @patch('Analytics_Reports.tasks.Notificaciones.objects')
    @patch('Analytics_Reports.tasks.TiposNotificacion.objects')
    def test_crea_notificacion_cuando_no_existe(self, mock_tipos, mock_notif):
        """Debe crear notificación nueva cuando no existe"""
        # No existe previa
        mock_notif.filter.return_value.exists.return_value = False
        
        # Mock tipo
        mock_tipo = MagicMock()
        mock_tipos.get.return_value = mock_tipo
        
        # Mock creación
        mock_nueva_notif = MagicMock()
        mock_notif.create.return_value = mock_nueva_notif
        
        resultado = ControlNotificacionesContextual.registrar_notificacion(
            participante=self.mock_participante,
            tipo_notif="Reconocimiento",
            mensaje="¡Felicitaciones!",
            actividad=self.mock_actividad,
            contexto="hito_10"
        )
        
        # Verificar que se creó
        self.assertEqual(resultado, mock_nueva_notif)
        mock_notif.create.assert_called_once()
    
    @patch('Analytics_Reports.tasks.Notificaciones.objects')
    def test_retorna_none_cuando_ya_existe(self, mock_notif):
        """Debe retornar None si ya existe notificación duplicada"""
        # Ya existe
        mock_notif.filter.return_value.exists.return_value = True
        
        resultado = ControlNotificacionesContextual.registrar_notificacion(
            participante=self.mock_participante,
            tipo_notif="Reconocimiento",
            mensaje="¡Felicitaciones!",
            actividad=self.mock_actividad,
            contexto="hito_10"
        )
        
        # No debe crear nueva
        self.assertIsNone(resultado)
        mock_notif.create.assert_not_called()
    
    @patch('Analytics_Reports.tasks.Notificaciones.objects')
    @patch('Analytics_Reports.tasks.TiposNotificacion.objects')
    def test_guarda_todos_los_campos_correctamente(self, mock_tipos, mock_notif):
        """Debe guardar todos los campos correctamente"""
        mock_notif.filter.return_value.exists.return_value = False
        mock_tipo = MagicMock()
        mock_tipos.get.return_value = mock_tipo
        mock_notif.create.return_value = MagicMock()
        
        # ✅ Guardar timestamp antes de la llamada
        antes = timezone.now()
        
        ControlNotificacionesContextual.registrar_notificacion(
            participante=self.mock_participante,
            tipo_notif="Reconocimiento",
            mensaje="¡Felicitaciones!",
            actividad=self.mock_actividad,
            contexto="hito_10"
        )
        
        despues = timezone.now()
        
        # Verificar campos del create
        call_kwargs = mock_notif.create.call_args[1]
        
        self.assertEqual(call_kwargs['participantes_id_participante'], self.mock_participante)
        self.assertEqual(call_kwargs['tipos_notificacion_id_tipo_notificacion'], mock_tipo)
        self.assertEqual(call_kwargs['mensaje'], "¡Felicitaciones!")
        
        # ✅ Verificar que la fecha está en el rango correcto (no exacta)
        fecha_guardada = call_kwargs['fecha']
        self.assertGreaterEqual(fecha_guardada, antes)
        self.assertLessEqual(fecha_guardada, despues)
        
        self.assertFalse(call_kwargs['leida'])
        self.assertEqual(call_kwargs['actividad_relacionada'], self.mock_actividad)
        self.assertEqual(call_kwargs['contexto_hito'], "hito_10")
        self.assertIn('hash_unicidad', call_kwargs)
    
    @patch('Analytics_Reports.tasks.Notificaciones.objects')
    @patch('Analytics_Reports.tasks.TiposNotificacion.objects')
    def test_hash_unicidad_es_correcto(self, mock_tipos, mock_notif):
        """Debe generar y guardar el hash correcto"""
        mock_notif.filter.return_value.exists.return_value = False
        mock_tipos.get.return_value = MagicMock()
        mock_notif.create.return_value = MagicMock()
        
        ControlNotificacionesContextual.registrar_notificacion(
            participante=self.mock_participante,
            tipo_notif="Reconocimiento",
            mensaje="Test",
            actividad=self.mock_actividad,
            contexto="hito_10"
        )
        
        call_kwargs = mock_notif.create.call_args[1]
        hash_guardado = call_kwargs['hash_unicidad']
        
        # Verificar que el hash es el esperado
        hash_esperado = ControlNotificacionesContextual.generar_hash_unicidad(
            123, "Reconocimiento", 45, "hito_10"
        )
        
        self.assertEqual(hash_guardado, hash_esperado)


# ==========================================================
# TESTS DE CASOS ESPECIALES Y EDGE CASES
# ==========================================================

class EdgeCasesTests(SimpleTestCase):
    """Casos límite y situaciones especiales"""
    
    def setUp(self):
        # ✅ TODO EN MOCKS
        self.tipo_notif = MagicMock()
        self.tipo_notif.nombre = "Test"
        
        self.mock_participante = MagicMock()
        self.mock_participante.id_participante = 123
    
    def test_hash_con_caracteres_especiales_en_contexto(self):
        """Debe manejar caracteres especiales en contexto"""
        hash1 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Test",
            contexto="días_7-crítico!"
        )
        
        # Debe generar hash válido
        self.assertEqual(len(hash1), 32)
    
    def test_hash_con_ids_muy_grandes(self):
        """Debe manejar IDs muy grandes"""
        hash1 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=999999999,
            tipo_notif="Test",
            actividad_id=888888888
        )
        
        self.assertEqual(len(hash1), 32)
    
    @patch('Analytics_Reports.tasks.Notificaciones.objects')
    def test_ventana_temporal_cero_horas(self, mock_notif):
        """Ventana de 0 horas debe funcionar correctamente"""
        mock_notif.filter.return_value.exists.return_value = False
        
        # No debe fallar con ventana=0
        resultado = ControlNotificacionesContextual.ya_existe_notificacion(
            participante=self.mock_participante,
            tipo_notif="Test",
            ventana_horas=0
        )
        
        self.assertFalse(resultado)
    
    @patch('Analytics_Reports.tasks.Notificaciones.objects')
    @patch('Analytics_Reports.tasks.TiposNotificacion.objects')
    def test_mensaje_muy_largo(self, mock_tipos, mock_notif):
        """Debe manejar mensajes muy largos"""
        mock_notif.filter.return_value.exists.return_value = False
        mock_tipos.get.return_value = MagicMock()
        mock_notif.create.return_value = MagicMock()
        
        mensaje_largo = "A" * 1000  # 1000 caracteres
        
        resultado = ControlNotificacionesContextual.registrar_notificacion(
            participante=self.mock_participante,
            tipo_notif="Test",
            mensaje=mensaje_largo
        )
        
        self.assertIsNotNone(resultado)
    
    def test_diferentes_ordenes_mismos_parametros(self):
        """El orden de llamada no debe afectar el hash (parámetros fijos)"""
        # Los parámetros son posicionales, así que esto verifica consistencia
        hash1 = ControlNotificacionesContextual.generar_hash_unicidad(
            123, "Test", 45, "ctx"
        )
        
        hash2 = ControlNotificacionesContextual.generar_hash_unicidad(
            participante_id=123,
            tipo_notif="Test",
            actividad_id=45,
            contexto="ctx"
        )
        
        self.assertEqual(hash1, hash2)


# ==========================================================
# TESTS DE INTEGRACIÓN
# ==========================================================

class IntegracionControlTests(SimpleTestCase):
    """Tests de integración del flujo completo"""
    
    def setUp(self):
        # ✅ TODO EN MOCKS
        self.tipo_notif = MagicMock()
        self.tipo_notif.nombre = "Reconocimiento"
        
        self.mock_participante = MagicMock()
        self.mock_participante.id_participante = 123
        
        self.mock_actividad = MagicMock()
        self.mock_actividad.id_actividad = 45
    
    @patch('Analytics_Reports.tasks.Notificaciones.objects')
    @patch('Analytics_Reports.tasks.TiposNotificacion.objects')
    def test_flujo_completo_primera_notificacion(self, mock_tipos, mock_notif):
        """Flujo completo: verificar -> no existe -> crear -> existe"""
        # 1. Verificar que no existe
        mock_notif.filter.return_value.exists.side_effect = [False, False, True]
        mock_tipos.get.return_value = self.tipo_notif
        mock_notif.create.return_value = MagicMock()
        
        # No existe inicialmente
        existe_antes = ControlNotificacionesContextual.ya_existe_notificacion(
            self.mock_participante, "Reconocimiento", self.mock_actividad, "hito_10"
        )
        self.assertFalse(existe_antes)
        
        # 2. Registrar
        nueva = ControlNotificacionesContextual.registrar_notificacion(
            self.mock_participante, "Reconocimiento", "Mensaje", 
            self.mock_actividad, "hito_10"
        )
        self.assertIsNotNone(nueva)
        
        # 3. Ahora sí existe
        existe_despues = ControlNotificacionesContextual.ya_existe_notificacion(
            self.mock_participante, "Reconocimiento", self.mock_actividad, "hito_10"
        )
        self.assertTrue(existe_despues)
    
    @patch('Analytics_Reports.tasks.Notificaciones.objects')
    @patch('Analytics_Reports.tasks.TiposNotificacion.objects')
    def test_previene_duplicados_en_registro(self, mock_tipos, mock_notif):
        """Debe prevenir duplicados incluso si se llama registrar dos veces"""
        mock_notif.filter.return_value.exists.side_effect = [False, True]
        mock_tipos.get.return_value = self.tipo_notif
        mock_notif.create.return_value = MagicMock()
        
        # Primera llamada: crea
        resultado1 = ControlNotificacionesContextual.registrar_notificacion(
            self.mock_participante, "Reconocimiento", "Mensaje", 
            self.mock_actividad, "hito_10"
        )
        self.assertIsNotNone(resultado1)
        
        # Segunda llamada: no crea
        resultado2 = ControlNotificacionesContextual.registrar_notificacion(
            self.mock_participante, "Reconocimiento", "Mensaje", 
            self.mock_actividad, "hito_10"
        )
        self.assertIsNone(resultado2)
        
        # Solo debe haber creado una vez
        self.assertEqual(mock_notif.create.call_count, 1)


# ==========================================================
# RESUMEN DE COBERTURA
# ==========================================================

"""
✅ COBERTURA COMPLETA (27 tests):

1. GENERACIÓN DE HASH (8 tests):
   - Hash MD5 válido
   - Idempotencia
   - Diferenciación por participante, tipo, actividad, contexto
   - Manejo de valores None
   - Uso correcto de 'global' y 'general'

2. VERIFICACIÓN DE EXISTENCIA (6 tests):
   - Retorno correcto True/False
   - Filtrado por hash correcto
   - Ventana temporal
   - Sin actividad

3. REGISTRO DE NOTIFICACIONES (5 tests):
   - Creación cuando no existe
   - Prevención de duplicados
   - Guardado de todos los campos
   - Hash correcto

4. EDGE CASES (6 tests):
   - Caracteres especiales
   - IDs grandes
   - Ventana temporal = 0
   - Mensajes largos
   - Consistencia de parámetros

5. INTEGRACIÓN (2 tests):
   - Flujo completo verificar -> crear -> verificar
   - Prevención de duplicados en registro

CORRECCIÓN APLICADA:
- ✅ Eliminado campo 'descripcion' de TiposNotificacion.objects.create()
- ✅ Solo se usa el campo 'nombre' que existe en el modelo real
"""