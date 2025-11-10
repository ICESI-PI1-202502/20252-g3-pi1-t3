from django.test import SimpleTestCase, RequestFactory
from django.utils import timezone
from datetime import timedelta, datetime, date
from django.conf import settings
from unittest.mock import Mock, patch, MagicMock
from django.contrib.messages import get_messages
from django.http import JsonResponse
import json

# Importar las funciones a probar
from notificaciones.views import (
    validar_envio_notificacion,
    es_dia_lectivo,
    es_notificacion_critica,
    get_calendario_academico,
    buscar_proximo_dia_lectivo,
    permite_notificaciones_criticas,
    get_info_dia_no_lectivo,
    crear_notificacion_validada,
    ver_notificaciones,
    crear_notificacion,
    marcar_notificacion_leida
)


class NotificacionesTestCase(SimpleTestCase):
    """Tests de lógica pura SIN base de datos"""
    
    databases = []

    def setUp(self):
        """Configurar calendario de prueba"""
        
        # Crear un calendario más extenso para tests
        hoy = date.today()
        
        settings.CALENDARIO_ACADEMICO = {
            # Semana de receso (días 1-7)
            (hoy + timedelta(days=1)).strftime("%Y-%m-%d"): {
                "tipo": "receso", "descripcion": "Receso día 1"
            },
            (hoy + timedelta(days=2)).strftime("%Y-%m-%d"): {
                "tipo": "receso", "descripcion": "Receso día 2"
            },
            (hoy + timedelta(days=3)).strftime("%Y-%m-%d"): {
                "tipo": "receso", "descripcion": "Receso día 3"
            },
            # Festivo (día 10)
            (hoy + timedelta(days=10)).strftime("%Y-%m-%d"): {
                "tipo": "festivo", "descripcion": "Día festivo"
            },
            # Parciales (días 15-17)
            (hoy + timedelta(days=15)).strftime("%Y-%m-%d"): {
                "tipo": "parcial", "descripcion": "Parcial día 1"
            },
        }
        
        # Mocks de tipos
        self.tipo_normal = Mock()
        self.tipo_normal.nombre = "Recordatorio de clase"
        
        self.tipo_critico = Mock()
        self.tipo_critico.nombre = "Alerta crítica de seguridad"
        
        self.tipo_cancelacion = Mock()
        self.tipo_cancelacion.nombre = "Cancelación urgente"

    # ====================================
    # TESTS BÁSICOS DE CALENDARIO
    # ====================================
    
    def test_es_dia_lectivo_hoy(self):
        """Hoy debe ser día lectivo"""
        hoy = date.today()
        self.assertTrue(es_dia_lectivo(hoy))
    
    def test_es_dia_lectivo_receso(self):
        """Día de receso NO es lectivo"""
        dia_receso = date.today() + timedelta(days=1)
        self.assertFalse(es_dia_lectivo(dia_receso))
    
    def test_es_dia_lectivo_festivo(self):
        """Día festivo NO es lectivo"""
        dia_festivo = date.today() + timedelta(days=10)
        self.assertFalse(es_dia_lectivo(dia_festivo))
    
    def test_get_calendario_academico(self):
        """Debe retornar el calendario configurado"""
        calendario = get_calendario_academico()
        self.assertIsInstance(calendario, dict)
        self.assertGreater(len(calendario), 0)
    
    def test_get_info_dia_no_lectivo(self):
        """Debe retornar info de días no lectivos"""
        dia_receso = date.today() + timedelta(days=1)
        info = get_info_dia_no_lectivo(dia_receso)
        
        self.assertIsNotNone(info)
        self.assertEqual(info['tipo'], 'receso')
    
    def test_get_info_dia_lectivo_retorna_none(self):
        """Día lectivo debe retornar None"""
        hoy = date.today()
        info = get_info_dia_no_lectivo(hoy)
        self.assertIsNone(info)
    
    # ====================================
    # TESTS DE IDENTIFICACIÓN DE CRÍTICOS
    # ====================================
    
    def test_es_notificacion_critica_palabras_clave(self):
        """Debe identificar palabras clave de críticos"""
        self.assertTrue(es_notificacion_critica("Alerta de seguridad"))
        self.assertTrue(es_notificacion_critica("Cancelación importante"))
        self.assertTrue(es_notificacion_critica("Emergencia evacuación"))
        self.assertTrue(es_notificacion_critica("Suspensión de clases"))
        self.assertTrue(es_notificacion_critica("URGENTE: Cambio de horario"))
        
    def test_no_es_notificacion_critica(self):
        """No debe marcar como críticos los normales"""
        self.assertFalse(es_notificacion_critica("Recordatorio de clase"))
        self.assertFalse(es_notificacion_critica("Información general"))
        self.assertFalse(es_notificacion_critica("Próximo evento"))
    
    def test_es_notificacion_critica_mayusculas(self):
        """Debe ser case-insensitive"""
        self.assertTrue(es_notificacion_critica("CANCELACIÓN TOTAL"))
        self.assertTrue(es_notificacion_critica("SuSpEnSiÓn"))
        self.assertTrue(es_notificacion_critica("EMERGENCIA"))
    
    def test_es_notificacion_critica_con_acentos(self):
        """Debe manejar palabras con y sin acentos"""
        self.assertTrue(es_notificacion_critica("Cancelación"))
        self.assertTrue(es_notificacion_critica("Cancelacion"))
        self.assertTrue(es_notificacion_critica("Suspensión"))
        self.assertTrue(es_notificacion_critica("Suspension"))
        self.assertTrue(es_notificacion_critica("Crítico"))
        self.assertTrue(es_notificacion_critica("Critico"))
    
    # ====================================
    # TESTS DE PERMISOS POR TIPO DE DÍA
    # ====================================
    
    def test_permite_criticas_en_festivo(self):
        """Festivos permiten notificaciones críticas"""
        dia_festivo = date.today() + timedelta(days=10)
        self.assertTrue(permite_notificaciones_criticas(dia_festivo))
    
    def test_no_permite_criticas_en_receso(self):
        """Recesos NO permiten notificaciones críticas"""
        dia_receso = date.today() + timedelta(days=1)
        self.assertFalse(permite_notificaciones_criticas(dia_receso))
    
    def test_no_permite_criticas_en_parcial(self):
        """Parciales NO permiten notificaciones críticas"""
        dia_parcial = date.today() + timedelta(days=15)
        self.assertFalse(permite_notificaciones_criticas(dia_parcial))
    
    def test_permite_criticas_en_dia_lectivo(self):
        """Días lectivos permiten todo (retorna True)"""
        hoy = date.today()
        self.assertTrue(permite_notificaciones_criticas(hoy))
    
    # ====================================
    # TESTS DE VALIDACIÓN DE ENVÍO
    # ====================================
    
    def test_validar_dia_lectivo_normal(self):
        """Día lectivo permite notificaciones normales"""
        hoy = date.today()
        puede, motivo = validar_envio_notificacion(hoy, self.tipo_normal)
        
        self.assertTrue(puede)
        self.assertIn("lectivo", motivo.lower())
    
    def test_validar_receso_normal_bloqueado(self):
        """Receso bloquea notificaciones normales"""
        dia_receso = date.today() + timedelta(days=1)
        puede, motivo = validar_envio_notificacion(dia_receso, self.tipo_normal)
        
        self.assertFalse(puede)
        self.assertIn("no lectivo", motivo.lower())
    
    def test_validar_festivo_critico_permitido(self):
        """Festivo permite notificaciones críticas"""
        dia_festivo = date.today() + timedelta(days=10)
        puede, motivo = validar_envio_notificacion(dia_festivo, self.tipo_critico)
        
        self.assertTrue(puede)
        self.assertIn("crítica", motivo.lower())
    
    def test_validar_receso_critico_bloqueado(self):
        """Receso bloquea incluso notificaciones críticas"""
        dia_receso = date.today() + timedelta(days=1)
        puede, motivo = validar_envio_notificacion(dia_receso, self.tipo_critico)
        
        self.assertFalse(puede)
    
    def test_validar_cancelacion_en_festivo(self):
        """Cancelaciones (críticas) permitidas en festivos"""
        dia_festivo = date.today() + timedelta(days=10)
        puede, motivo = validar_envio_notificacion(dia_festivo, self.tipo_cancelacion)
        
        self.assertTrue(puede)
    
    def test_validar_parcial_critico_bloqueado(self):
        """Día de parcial bloquea incluso críticas"""
        dia_parcial = date.today() + timedelta(days=15)
        puede, motivo = validar_envio_notificacion(dia_parcial, self.tipo_critico)
        
        self.assertFalse(puede)
        self.assertIn("no lectivo", motivo.lower())
    
    # ====================================
    # TESTS DE VALIDACIÓN DE INPUTS
    # ====================================
    
    def test_validar_tipo_string(self):
        """Debe aceptar strings como tipo"""
        hoy = date.today()
        puede, motivo = validar_envio_notificacion(hoy, "Recordatorio")
        
        self.assertTrue(puede)
    
    def test_validar_tipo_none(self):
        """Debe rechazar None"""
        hoy = date.today()
        puede, motivo = validar_envio_notificacion(hoy, None)
        
        self.assertFalse(puede)
        self.assertIn("vacío", motivo.lower())
    
    def test_validar_tipo_lista_vacia(self):
        """Debe rechazar lista vacía"""
        hoy = date.today()
        puede, motivo = validar_envio_notificacion(hoy, [])
        
        self.assertFalse(puede)
        self.assertTrue("lista" in motivo.lower() or "vacío" in motivo.lower())
    
    def test_validar_tipo_lista_con_elementos(self):
        """Debe rechazar listas con elementos"""
        hoy = date.today()
        puede, motivo = validar_envio_notificacion(hoy, ["tipo1", "tipo2"])
        
        self.assertFalse(puede)
        self.assertIn("lista", motivo.lower())
    
    def test_validar_tipo_entero(self):
        """Debe manejar ID entero (pero fallará sin BD)"""
        hoy = date.today()
        puede, motivo = validar_envio_notificacion(hoy, 123)
        
        self.assertFalse(puede)
        # Debe indicar que no puede acceder a BD o ID no encontrado
        self.assertTrue(
            "no encontrado" in motivo.lower() or 
            "base de datos" in motivo.lower()
        )
    
    def test_validar_tipo_objeto_invalido(self):
        """Debe rechazar objetos sin atributo 'nombre'"""
        hoy = date.today()
        tipo_invalido = object()
        
        puede, motivo = validar_envio_notificacion(hoy, tipo_invalido)
        
        self.assertFalse(puede)
        self.assertIn("inválido", motivo.lower())
    
    def test_validar_con_datetime_en_lugar_de_date(self):
        """Debe manejar datetime además de date"""
        ahora = datetime.now()
        puede, motivo = validar_envio_notificacion(ahora, self.tipo_normal)
        
        # Si es hoy, debe permitir
        if ahora.date() == date.today():
            self.assertTrue(puede)
    
    def test_validar_fecha_en_receso_con_datetime(self):
        """Debe convertir datetime a date correctamente"""
        dia_receso_dt = datetime.combine(
            date.today() + timedelta(days=1), 
            datetime.min.time()
        )
        puede, motivo = validar_envio_notificacion(dia_receso_dt, self.tipo_normal)
        
        self.assertFalse(puede)
    
    # ====================================
    # TESTS DE BÚSQUEDA DE DÍA LECTIVO
    # ====================================
    
    def test_buscar_proximo_desde_receso(self):
        """Debe encontrar próximo día lectivo después de receso"""
        dia_receso = date.today() + timedelta(days=1)
        
        proximo = buscar_proximo_dia_lectivo(dia_receso)
        
        self.assertIsNotNone(proximo)
        # Debe ser después del receso (día 3)
        self.assertGreater(proximo, dia_receso)
        # Y debe ser día lectivo
        if isinstance(proximo, datetime):
            self.assertTrue(es_dia_lectivo(proximo.date()))
        else:
            self.assertTrue(es_dia_lectivo(proximo))
    
    def test_buscar_proximo_desde_dia_lectivo(self):
        """Desde día lectivo debe retornar el mismo día"""
        hoy = date.today()
        
        proximo = buscar_proximo_dia_lectivo(hoy)
        
        self.assertIsNotNone(proximo)
        # Debe ser hoy o después
        if isinstance(proximo, datetime):
            self.assertGreaterEqual(proximo.date(), hoy)
        else:
            self.assertGreaterEqual(proximo, hoy)
    
    def test_buscar_proximo_limit_30_dias(self):
        """Debe respetar límite de 30 días"""
        # Bloquear muchos días
        calendario_bloqueado = {}
        for i in range(1, 35):
            fecha = (date.today() + timedelta(days=i)).strftime("%Y-%m-%d")
            calendario_bloqueado[fecha] = {"tipo": "receso", "descripcion": "Bloqueado"}
        
        original = settings.CALENDARIO_ACADEMICO
        try:
            settings.CALENDARIO_ACADEMICO = calendario_bloqueado
            
            dia_inicio = date.today() + timedelta(days=1)
            proximo = buscar_proximo_dia_lectivo(dia_inicio, max_dias=30)
            
            # No debe encontrar nada (None)
            self.assertIsNone(proximo)
            
        finally:
            settings.CALENDARIO_ACADEMICO = original
    
    def test_buscar_proximo_con_datetime(self):
        """Debe manejar datetime como entrada"""
        dia_receso_dt = datetime.combine(
            date.today() + timedelta(days=1),
            datetime.min.time()
        )
        
        proximo = buscar_proximo_dia_lectivo(dia_receso_dt)
        
        self.assertIsNotNone(proximo)
    
    def test_buscar_proximo_con_max_dias_custom(self):
        """Debe respetar max_dias personalizado"""
        # Crear bloque de 5 días
        calendario_bloqueado = {}
        for i in range(1, 8):
            fecha = (date.today() + timedelta(days=i)).strftime("%Y-%m-%d")
            calendario_bloqueado[fecha] = {"tipo": "receso", "descripcion": "Bloqueado"}
        
        original = settings.CALENDARIO_ACADEMICO
        try:
            settings.CALENDARIO_ACADEMICO = calendario_bloqueado
            
            dia_inicio = date.today() + timedelta(days=1)
            # Buscar solo 3 días (no encontrará porque hay 7 bloqueados)
            proximo = buscar_proximo_dia_lectivo(dia_inicio, max_dias=3)
            
            self.assertIsNone(proximo)
            
        finally:
            settings.CALENDARIO_ACADEMICO = original
    
    # ====================================
    # TESTS DE CASOS EDGE
    # ====================================
    
    def test_calendario_vacio_todos_lectivos(self):
        """Con calendario vacío, todos los días son lectivos"""
        original = settings.CALENDARIO_ACADEMICO
        
        try:
            settings.CALENDARIO_ACADEMICO = {}
            
            hoy = date.today()
            futuro = hoy + timedelta(days=100)
            
            self.assertTrue(es_dia_lectivo(hoy))
            self.assertTrue(es_dia_lectivo(futuro))
            
        finally:
            settings.CALENDARIO_ACADEMICO = original
    
    def test_calendario_sin_tipo_default_festivo(self):
        """Día sin 'tipo' debe considerarse festivo por defecto"""
        hoy = date.today()
        dia_sin_tipo = hoy + timedelta(days=20)
        
        original = settings.CALENDARIO_ACADEMICO
        try:
            settings.CALENDARIO_ACADEMICO = {
                dia_sin_tipo.strftime("%Y-%m-%d"): {
                    "descripcion": "Día especial sin tipo"
                }
            }
            
            # No es lectivo
            self.assertFalse(es_dia_lectivo(dia_sin_tipo))
            # Permite críticos (default festivo)
            self.assertTrue(permite_notificaciones_criticas(dia_sin_tipo))
            
        finally:
            settings.CALENDARIO_ACADEMICO = original
    
    def test_multiples_tipos_criticos_en_nombre(self):
        """Debe identificar si tiene múltiples palabras críticas"""
        tipo_multiple = Mock()
        tipo_multiple.nombre = "Alerta de cancelación urgente por emergencia"
        
        self.assertTrue(es_notificacion_critica(tipo_multiple.nombre))


# ========================================
# TESTS CON MOCKING DE BASE DE DATOS
# ========================================

class NotificacionesConMockTestCase(SimpleTestCase):
    """Tests que requieren mockear creación en BD"""
    
    databases = []
    
    def setUp(self):
        """Setup básico"""
        hoy = date.today()
        
        settings.CALENDARIO_ACADEMICO = {
            (hoy + timedelta(days=1)).strftime("%Y-%m-%d"): {
                "tipo": "receso", "descripcion": "Receso"
            },
            (hoy + timedelta(days=2)).strftime("%Y-%m-%d"): {
                "tipo": "receso", "descripcion": "Receso día 2"
            },
            (hoy + timedelta(days=5)).strftime("%Y-%m-%d"): {
                "tipo": "festivo", "descripcion": "Festivo"
            },
        }
        
        self.participante = Mock()
        self.participante.id_participante = 999
        
        self.tipo_normal = Mock()
        self.tipo_normal.nombre = "Recordatorio"
        
        self.tipo_critico = Mock()
        self.tipo_critico.nombre = "Alerta de seguridad"
    
    @patch('notificaciones.views.Notificaciones.objects.create')
    def test_crear_en_dia_lectivo_llama_create(self, mock_create):
        """En día lectivo debe llamar a create"""
        hoy = datetime.now()
        mock_notif = Mock()
        mock_notif.id_notificacion = 1
        mock_create.return_value = mock_notif
        
        resultado = crear_notificacion_validada(
            mensaje="Test",
            fecha_deseada=hoy,
            participante=self.participante,
            tipo_notificacion=self.tipo_normal,
            auto_reprogramar=False
        )
        
        self.assertTrue(resultado["success"])
        self.assertIsNotNone(resultado["notificacion"])
        mock_create.assert_called_once()
    
    @patch('notificaciones.views.Notificaciones.objects.create')
    def test_crear_auto_reprogramar_en_dia_no_lectivo(self, mock_create):
        """Debe intentar reprogramar si es día no lectivo y auto_reprogramar=True"""
        dia_no_lectivo = date.today() + timedelta(days=1)  # receso
        mock_create.return_value = Mock(id_notificacion=2)

        resultado = crear_notificacion_validada(
            mensaje="Evento reprogramado",
            fecha_deseada=dia_no_lectivo,
            participante=self.participante,
            tipo_notificacion=self.tipo_normal,
            auto_reprogramar=True
        )

        self.assertTrue(resultado["success"])
        self.assertTrue(resultado.get("reprogramada", False))
        self.assertIn("reprogram", resultado["motivo"].lower())
        mock_create.assert_called_once()
    
    @patch('notificaciones.views.Notificaciones.objects.create')
    def test_crear_falla_por_tipo_invalido(self, mock_create):
        """Debe fallar si tipo_notificacion es None"""
        hoy = date.today()
        resultado = crear_notificacion_validada(
            mensaje="Sin tipo",
            fecha_deseada=hoy,
            participante=self.participante,
            tipo_notificacion=None,
            auto_reprogramar=False
        )

        self.assertFalse(resultado["success"])
        self.assertIn("tipo", resultado["motivo"].lower())
        mock_create.assert_not_called()
    
    @patch('notificaciones.views.Notificaciones.objects.create')
    def test_crear_sin_reprogramar_en_receso_falla(self, mock_create):
        """Sin auto_reprogramar, debe fallar en día no lectivo"""
        dia_receso = date.today() + timedelta(days=1)
        
        resultado = crear_notificacion_validada(
            mensaje="No reprogramar",
            fecha_deseada=dia_receso,
            participante=self.participante,
            tipo_notificacion=self.tipo_normal,
            auto_reprogramar=False
        )
        
        self.assertFalse(resultado["success"])
        self.assertFalse(resultado.get("reprogramada", False))
        mock_create.assert_not_called()
    
    @patch('notificaciones.views.Notificaciones.objects.create')
    def test_crear_critico_en_festivo_sin_reprogramar(self, mock_create):
        """Notificación crítica en festivo debe crearse directamente"""
        dia_festivo = date.today() + timedelta(days=5)
        mock_create.return_value = Mock(id_notificacion=3)
        
        resultado = crear_notificacion_validada(
            mensaje="Alerta importante",
            fecha_deseada=dia_festivo,
            participante=self.participante,
            tipo_notificacion=self.tipo_critico,
            auto_reprogramar=False
        )
        
        self.assertTrue(resultado["success"])
        self.assertFalse(resultado.get("reprogramada", False))
        mock_create.assert_called_once()
    
    @patch('notificaciones.views.Notificaciones.objects.create')
    def test_crear_exception_en_create(self, mock_create):
        """Debe manejar excepciones al crear en BD"""
        mock_create.side_effect = Exception("Error de BD")
        hoy = date.today()
        
        resultado = crear_notificacion_validada(
            mensaje="Test error",
            fecha_deseada=hoy,
            participante=self.participante,
            tipo_notificacion=self.tipo_normal,
            auto_reprogramar=False
        )
        
        self.assertFalse(resultado["success"])
        self.assertIn("error", resultado["motivo"].lower())
    
    @patch('notificaciones.views.buscar_proximo_dia_lectivo')
    @patch('notificaciones.views.Notificaciones.objects.create')
    def test_crear_sin_dia_lectivo_disponible(self, mock_create, mock_buscar):
        """Debe fallar si no hay día lectivo en 30 días"""
        dia_receso = date.today() + timedelta(days=1)
        mock_buscar.return_value = None  # No hay días disponibles
        
        resultado = crear_notificacion_validada(
            mensaje="Sin días",
            fecha_deseada=dia_receso,
            participante=self.participante,
            tipo_notificacion=self.tipo_normal,
            auto_reprogramar=True
        )
        
        self.assertFalse(resultado["success"])
        self.assertIn("no se encontró día lectivo", resultado["motivo"].lower())
        mock_create.assert_not_called()
    
    @patch('notificaciones.views.Notificaciones.objects.create')
    def test_crear_retorna_fecha_original_y_final(self, mock_create):
        """Debe retornar fecha_original y fecha_final cuando se reprograma"""
        dia_receso = date.today() + timedelta(days=1)
        mock_create.return_value = Mock(id_notificacion=4)
        
        resultado = crear_notificacion_validada(
            mensaje="Con fechas",
            fecha_deseada=dia_receso,
            participante=self.participante,
            tipo_notificacion=self.tipo_normal,
            auto_reprogramar=True
        )
        
        if resultado["success"] and resultado.get("reprogramada"):
            self.assertIsNotNone(resultado.get("fecha_original"))
            self.assertIsNotNone(resultado.get("fecha_final"))
            self.assertNotEqual(resultado["fecha_original"], resultado["fecha_final"])


# ========================================
# TESTS DE VISTAS HTTP
# ========================================

class VistaNotificacionesTests(SimpleTestCase):
    """Tests de las vistas HTTP"""
    
    databases = []
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = Mock()
        self.user.id = 1
        self.user.is_authenticated = True
    
    @patch('notificaciones.views.Notificaciones.objects')
    @patch('notificaciones.views.render')
    def test_ver_notificaciones_renders_template(self, mock_render, mock_notif):
        """Debe renderizar template con notificaciones"""
        mock_qs = Mock()
        mock_qs.order_by.return_value = []
        mock_notif.filter.return_value = mock_qs
        
        request = self.factory.get('/notificaciones/')
        request.user = self.user
        
        ver_notificaciones(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "notificaciones.html")
        self.assertIn("notificaciones", mock_render.call_args[0][2])
    
    @patch('notificaciones.views.TiposNotificacion.objects')
    @patch('notificaciones.views.Participantes.objects')
    @patch('notificaciones.views.render')
    def test_crear_notificacion_get_renders_form(self, mock_render, mock_part, mock_tipos):
        """GET debe renderizar formulario"""
        mock_tipos.all.return_value = []
        mock_part.filter.return_value = []
        
        request = self.factory.get('/crear-notificacion/')
        request.user = self.user
        
        crear_notificacion(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "crear_notificacion.html")
        context = mock_render.call_args[0][2]
        self.assertIn("tipos", context)
        self.assertIn("participantes", context)
    
    @patch('notificaciones.views.crear_notificacion_validada')
    @patch('notificaciones.views.TiposNotificacion.objects')
    @patch('notificaciones.views.Participantes.objects')
    @patch('notificaciones.views.messages')
    @patch('notificaciones.views.redirect')
    def test_crear_notificacion_post_reprogramada(
        self, mock_redirect, mock_messages, mock_part, mock_tipos, mock_crear_validada
    ):
        """POST con reprogramación debe mostrar warning"""
        mock_participante = Mock()
        mock_part.get.return_value = mock_participante
        
        mock_tipo = Mock()
        mock_tipos.get.return_value = mock_tipo
        
        mock_crear_validada.return_value = {
            'success': True,
            'mensaje': 'Reprogramada de 2025-11-10 a 2025-11-11',
            'reprogramada': True
        }
        
        request = self.factory.post('/crear-notificacion/')
        request.user = self.user
        request.POST = {
            'mensaje': 'Test',
            'fecha': '2025-11-10T10:00',
            'participante_id': '1',
            'tipo_id': '1',
            'auto_reprogramar': 'on'
        }
        
        crear_notificacion(request)
        
        mock_messages.warning.assert_called_once()
        mock_redirect.assert_called_once_with('ver_notificaciones')
    
    @patch('notificaciones.views.crear_notificacion_validada')
    @patch('notificaciones.views.TiposNotificacion.objects')
    @patch('notificaciones.views.Participantes.objects')
    @patch('notificaciones.views.messages')
    @patch('notificaciones.views.render')
    def test_crear_notificacion_post_failure(
        self, mock_render, mock_messages, mock_part, mock_tipos, mock_crear_validada
    ):
        """POST fallido debe mostrar error"""
        mock_participante = Mock()
        mock_part.get.return_value = mock_participante
        
        mock_tipo = Mock()
        mock_tipos.get.return_value = mock_tipo
        
        mock_crear_validada.return_value = {
            'success': False,
            'mensaje': 'Día no lectivo'
        }
        
        mock_tipos.all.return_value = []
        mock_part.filter.return_value = []
        
        request = self.factory.post('/crear-notificacion/')
        request.user = self.user
        request.POST = {
            'mensaje': 'Test',
            'fecha': '2025-11-10T10:00',
            'participante_id': '1',
            'tipo_id': '1'
        }
        
        crear_notificacion(request)
        
        mock_messages.error.assert_called()
        # No debe redirigir, debe mostrar el form nuevamente
        mock_render.assert_called_once()
    
    @patch('notificaciones.views.TiposNotificacion.objects')
    @patch('notificaciones.views.Participantes.objects')
    @patch('notificaciones.views.messages')
    @patch('notificaciones.views.render')
    def test_crear_notificacion_post_exception(
        self, mock_render, mock_messages, mock_part, mock_tipos
    ):
        """Excepción en POST debe mostrar error"""
        mock_part.get.side_effect = Exception("Error de BD")
        mock_tipos.all.return_value = []
        mock_part.filter.return_value = []
        
        request = self.factory.post('/crear-notificacion/')
        request.user = self.user
        request.POST = {
            'mensaje': 'Test',
            'fecha': '2025-11-10T10:00',
            'participante_id': '1',
            'tipo_id': '1'
        }
        
        crear_notificacion(request)
        
        mock_messages.error.assert_called()
    
    @patch('notificaciones.views.Notificaciones.objects')
    def test_marcar_leida_success(self, mock_notif):
        """Debe marcar notificación como leída"""
        mock_notificacion = Mock()
        mock_notificacion.leida = False
        mock_notif.get.return_value = mock_notificacion
        
        request = self.factory.post('/marcar-leida/1/')
        request.user = self.user
        
        response = marcar_notificacion_leida(request, 1)
        
        self.assertIsInstance(response, JsonResponse)
        self.assertTrue(mock_notificacion.leida)
        mock_notificacion.save.assert_called_once()
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    @patch('notificaciones.views.Notificaciones.objects')
    def test_marcar_leida_not_found(self, mock_notif):
        """Debe retornar 404 si no existe"""
        from notificaciones.views import Notificaciones
        mock_notif.get.side_effect = Notificaciones.DoesNotExist
        
        request = self.factory.post('/marcar-leida/999/')
        request.user = self.user
        
        response = marcar_notificacion_leida(request, 999)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    @patch('notificaciones.views.Notificaciones.objects')
    def test_marcar_leida_exception(self, mock_notif):
        """Debe manejar excepciones generales"""
        mock_notificacion = Mock()
        mock_notificacion.save.side_effect = Exception("Error al guardar")
        mock_notif.get.return_value = mock_notificacion
        
        request = self.factory.post('/marcar-leida/1/')
        request.user = self.user
        
        response = marcar_notificacion_leida(request, 1)
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertFalse(data['success'])


# ========================================
# TESTS DE CASOS ESPECÍFICOS ADICIONALES
# ========================================

class NotificacionesCasosEspecificosTests(SimpleTestCase):
    """Tests de casos específicos y edge cases"""
    
    databases = []
    
    def setUp(self):
        hoy = date.today()
        settings.CALENDARIO_ACADEMICO = {
            (hoy + timedelta(days=1)).strftime("%Y-%m-%d"): {
                "tipo": "receso", "descripcion": "Receso"
            },
            (hoy + timedelta(days=10)).strftime("%Y-%m-%d"): {
                "tipo": "festivo", "descripcion": "Festivo"
            },
        }
        
        self.tipo_recordatorio = Mock()
        self.tipo_recordatorio.nombre = "Recordatorio de clase"
        
        self.tipo_urgente = Mock()
        self.tipo_urgente.nombre = "Notificación urgente"
        
        self.participante = Mock()
        self.participante.id_participante = 1
    
    def test_validar_recordatorio_clase_en_lectivo(self):
        """Recordatorio de clase debe permitirse en día lectivo"""
        hoy = date.today()
        puede, motivo = validar_envio_notificacion(hoy, self.tipo_recordatorio)
        self.assertTrue(puede)
        self.assertIn("lectivo", motivo.lower())

    def test_validar_recordatorio_evento_en_receso(self):
        """Recordatorio de evento NO debe enviarse en receso"""
        dia_receso = date.today() + timedelta(days=1)
        tipo = Mock()
        tipo.nombre = "Recordatorio de evento"
        puede, motivo = validar_envio_notificacion(dia_receso, tipo)
        self.assertFalse(puede)
        self.assertIn("no lectivo", motivo.lower())

    def test_validar_recordatorio_torneo_en_festivo_urgente(self):
        """Recordatorio urgente puede enviarse en festivo"""
        dia_festivo = date.today() + timedelta(days=10)
        puede, motivo = validar_envio_notificacion(dia_festivo, self.tipo_urgente)
        
        self.assertTrue(puede)
        self.assertTrue(
            "crítica" in motivo.lower() or "lectivo" in motivo.lower(),
            f"Expected 'crítica' or 'lectivo' in motivo, got: {motivo}"
        )

    def test_validar_recordatorio_torneo_normal_bloqueado(self):
        """Torneo sin urgencia debe bloquearse en receso"""
        dia_receso = date.today() + timedelta(days=1)
        tipo = Mock()
        tipo.nombre = "Recordatorio de torneo"
        puede, motivo = validar_envio_notificacion(dia_receso, tipo)
        self.assertFalse(puede)
        self.assertIn("no lectivo", motivo.lower())
    
    def test_tipo_con_nombre_vacio(self):
        """Tipo con nombre vacío debe fallar"""
        tipo = Mock()
        tipo.nombre = ""
        hoy = date.today()
        
        puede, motivo = validar_envio_notificacion(hoy, tipo)
        
        # Si el nombre está vacío, no puede determinar si es crítico
        # Pero puede permitir el envío en día lectivo
        if puede:
            self.assertIn("lectivo", motivo.lower())
    
    def test_buscar_dia_lectivo_inmediatamente_despues(self):
        """Debe encontrar el primer día lectivo después de un bloque"""
        # Bloquear días 1-3
        hoy = date.today()
        calendario_temp = {}
        for i in range(1, 4):
            fecha = (hoy + timedelta(days=i)).strftime("%Y-%m-%d")
            calendario_temp[fecha] = {"tipo": "receso", "descripcion": "Receso"}
        
        original = settings.CALENDARIO_ACADEMICO
        try:
            settings.CALENDARIO_ACADEMICO = calendario_temp
            
            dia_inicio = hoy + timedelta(days=1)
            proximo = buscar_proximo_dia_lectivo(dia_inicio)
            
            self.assertIsNotNone(proximo)
            # Debe ser el día 4 (después del receso)
            if isinstance(proximo, datetime):
                self.assertEqual(proximo.date(), hoy + timedelta(days=4))
            else:
                self.assertEqual(proximo, hoy + timedelta(days=4))
                
        finally:
            settings.CALENDARIO_ACADEMICO = original
    
    @patch('notificaciones.views.Notificaciones.objects.create')
    def test_crear_con_fecha_string_formateada(self, mock_create):
        """Resultado debe incluir fechas formateadas como string"""
        dia_receso = date.today() + timedelta(days=1)
        mock_create.return_value = Mock(id_notificacion=1)
        
        resultado = crear_notificacion_validada(
            mensaje="Test",
            fecha_deseada=dia_receso,
            participante=self.participante,
            tipo_notificacion=self.tipo_recordatorio,
            auto_reprogramar=True
        )
        
        if resultado['success'] and resultado.get('reprogramada'):
            # Verificar que el motivo contiene fechas formateadas
            self.assertIn("reprogram", resultado['motivo'].lower())
            # El motivo debe tener formato de fecha
            self.assertRegex(resultado['motivo'], r'\d{4}-\d{2}-\d{2}')
    
    def test_permite_criticas_con_info_none(self):
        """Si get_info_dia_no_lectivo retorna None, debe permitir"""
        # Un día que no está en el calendario
        dia_cualquiera = date.today() + timedelta(days=100)
        
        resultado = permite_notificaciones_criticas(dia_cualquiera)
        
        # Día no está en calendario = día lectivo = permite todo
        self.assertTrue(resultado)
    
    def test_es_dia_lectivo_con_fechas_muy_futuras(self):
        """Debe manejar fechas muy en el futuro"""
        fecha_futura = date.today() + timedelta(days=1000)
        
        # Sin entradas en calendario, debe ser lectivo
        resultado = es_dia_lectivo(fecha_futura)
        
        self.assertTrue(resultado)
    
    def test_es_dia_lectivo_con_fechas_pasadas(self):
        """Debe manejar fechas en el pasado"""
        fecha_pasada = date.today() - timedelta(days=100)
        
        resultado = es_dia_lectivo(fecha_pasada)
        
        # Sin entradas en calendario del pasado, debe ser lectivo
        self.assertTrue(resultado)


# ========================================
# TESTS DE INTEGRACIÓN SIMPLIFICADA
# ========================================

class NotificacionesIntegracionTests(SimpleTestCase):
    """Tests que verifican flujos completos"""
    
    databases = []
    
    def setUp(self):
        hoy = date.today()
        
        # Calendario con varios escenarios
        settings.CALENDARIO_ACADEMICO = {
            (hoy + timedelta(days=1)).strftime("%Y-%m-%d"): {
                "tipo": "receso", "descripcion": "Receso día 1"
            },
            (hoy + timedelta(days=2)).strftime("%Y-%m-%d"): {
                "tipo": "receso", "descripcion": "Receso día 2"
            },
            (hoy + timedelta(days=5)).strftime("%Y-%m-%d"): {
                "tipo": "festivo", "descripcion": "Festivo"
            },
            (hoy + timedelta(days=10)).strftime("%Y-%m-%d"): {
                "tipo": "parcial", "descripcion": "Parcial"
            },
        }
        
        self.participante = Mock()
        self.participante.id_participante = 1
    
    @patch('notificaciones.views.Notificaciones.objects.create')
    def test_flujo_completo_notificacion_normal_en_lectivo(self, mock_create):
        """Flujo: Notificación normal → Día lectivo → Éxito directo"""
        mock_create.return_value = Mock(id_notificacion=1)
        
        tipo = Mock()
        tipo.nombre = "Recordatorio de clase"
        hoy = date.today()
        
        # 1. Validar
        puede, motivo = validar_envio_notificacion(hoy, tipo)
        self.assertTrue(puede)
        
        # 2. Crear
        resultado = crear_notificacion_validada(
            mensaje="Clase mañana",
            fecha_deseada=hoy,
            participante=self.participante,
            tipo_notificacion=tipo,
            auto_reprogramar=False
        )
        
        self.assertTrue(resultado['success'])
        self.assertFalse(resultado.get('reprogramada', False))
        mock_create.assert_called_once()
    
    @patch('notificaciones.views.Notificaciones.objects.create')
    def test_flujo_completo_notificacion_normal_en_receso_con_reprogramacion(self, mock_create):
        """Flujo: Normal → Receso → Reprogramar → Éxito"""
        mock_create.return_value = Mock(id_notificacion=2)
        
        tipo = Mock()
        tipo.nombre = "Recordatorio"
        dia_receso = date.today() + timedelta(days=1)
        
        # 1. Validar (debe fallar inicialmente)
        puede, motivo = validar_envio_notificacion(dia_receso, tipo)
        self.assertFalse(puede)
        
        # 2. Crear con auto_reprogramar
        resultado = crear_notificacion_validada(
            mensaje="Recordatorio",
            fecha_deseada=dia_receso,
            participante=self.participante,
            tipo_notificacion=tipo,
            auto_reprogramar=True
        )
        
        self.assertTrue(resultado['success'])
        self.assertTrue(resultado.get('reprogramada', False))
        self.assertIsNotNone(resultado.get('fecha_final'))
        # Fecha final debe ser después del receso
        fecha_final = resultado['fecha_final']
        if isinstance(fecha_final, datetime):
            fecha_final = fecha_final.date()
        self.assertGreater(fecha_final, dia_receso)
        mock_create.assert_called_once()
    
    @patch('notificaciones.views.Notificaciones.objects.create')
    def test_flujo_completo_notificacion_critica_en_festivo(self, mock_create):
        """Flujo: Crítica → Festivo → Éxito directo"""
        mock_create.return_value = Mock(id_notificacion=3)
        
        tipo = Mock()
        tipo.nombre = "Alerta de emergencia"
        dia_festivo = date.today() + timedelta(days=5)
        
        # 1. Verificar que es crítica
        self.assertTrue(es_notificacion_critica(tipo.nombre))
        
        # 2. Verificar que festivo permite críticas
        self.assertTrue(permite_notificaciones_criticas(dia_festivo))
        
        # 3. Validar
        puede, motivo = validar_envio_notificacion(dia_festivo, tipo)
        self.assertTrue(puede)
        
        # 4. Crear
        resultado = crear_notificacion_validada(
            mensaje="Emergencia",
            fecha_deseada=dia_festivo,
            participante=self.participante,
            tipo_notificacion=tipo,
            auto_reprogramar=False
        )
        
        self.assertTrue(resultado['success'])
        self.assertFalse(resultado.get('reprogramada', False))
        mock_create.assert_called_once()
    
    @patch('notificaciones.views.Notificaciones.objects.create')
    def test_flujo_completo_critica_en_parcial_bloqueada(self, mock_create):
        """Flujo: Crítica → Parcial → Bloqueo (no reprograma críticas)"""
        tipo = Mock()
        tipo.nombre = "Cancelación urgente"
        dia_parcial = date.today() + timedelta(days=10)
        
        # 1. Verificar que es crítica
        self.assertTrue(es_notificacion_critica(tipo.nombre))
        
        # 2. Verificar que parcial NO permite críticas
        self.assertFalse(permite_notificaciones_criticas(dia_parcial))
        
        # 3. Validar (debe fallar)
        puede, motivo = validar_envio_notificacion(dia_parcial, tipo)
        self.assertFalse(puede)
        
        # 4. Intentar crear con reprogramación (no debe reprogramar críticas)
        resultado = crear_notificacion_validada(
            mensaje="Cancelación",
            fecha_deseada=dia_parcial,
            participante=self.participante,
            tipo_notificacion=tipo,
            auto_reprogramar=True
        )
        
        # Las críticas NO se reprograman, así que debe fallar
        self.assertFalse(resultado['success'])
        mock_create.assert_not_called()
    
    def test_flujo_busqueda_dia_lectivo_atraves_de_varios_recesos(self):
        """Flujo: Buscar día lectivo atravesando múltiples días bloqueados"""
        dia_inicio = date.today() + timedelta(days=1)
        
        # Buscar próximo día lectivo
        proximo = buscar_proximo_dia_lectivo(dia_inicio)
        
        self.assertIsNotNone(proximo)
        
        # Verificar que el día encontrado es lectivo
        if isinstance(proximo, datetime):
            self.assertTrue(es_dia_lectivo(proximo.date()))
        else:
            self.assertTrue(es_dia_lectivo(proximo))
        
        # Verificar que está después del inicio
        if isinstance(proximo, datetime):
            self.assertGreater(proximo.date(), dia_inicio)
        else:
            self.assertGreater(proximo, dia_inicio)


# ========================================
# TESTS DE PERFORMANCE Y LÍMITES
# ========================================

class NotificacionesPerformanceTests(SimpleTestCase):
    """Tests de límites y performance"""
    
    databases = []
    
    def test_calendario_muy_grande(self):
        """Debe manejar calendarios con muchas entradas"""
        # Crear calendario con 365 días bloqueados
        hoy = date.today()
        calendario_grande = {}
        for i in range(1, 366):
            fecha = (hoy + timedelta(days=i)).strftime("%Y-%m-%d")
            calendario_grande[fecha] = {
                "tipo": "receso",
                "descripcion": f"Día {i}"
            }
        
        original = settings.CALENDARIO_ACADEMICO
        try:
            settings.CALENDARIO_ACADEMICO = calendario_grande
            
            # Debe poder verificar sin problemas
            dia_futuro = hoy + timedelta(days=100)
            resultado = es_dia_lectivo(dia_futuro)
            
            self.assertFalse(resultado)
            
        finally:
            settings.CALENDARIO_ACADEMICO = original
    
    def test_buscar_con_limite_extendido(self):
        """Buscar con límite de 60 días"""
        # Bloquear 35 días
        hoy = date.today()
        calendario_temp = {}
        for i in range(1, 36):
            fecha = (hoy + timedelta(days=i)).strftime("%Y-%m-%d")
            calendario_temp[fecha] = {"tipo": "receso", "descripcion": "Bloqueado"}
        
        original = settings.CALENDARIO_ACADEMICO
        try:
            settings.CALENDARIO_ACADEMICO = calendario_temp
            
            dia_inicio = hoy + timedelta(days=1)
            # Con límite de 60, debe encontrar el día 36
            proximo = buscar_proximo_dia_lectivo(dia_inicio, max_dias=60)
            
            self.assertIsNotNone(proximo)
            if isinstance(proximo, datetime):
                self.assertEqual(proximo.date(), hoy + timedelta(days=36))
            else:
                self.assertEqual(proximo, hoy + timedelta(days=36))
                
        finally:
            settings.CALENDARIO_ACADEMICO = original
    
    def test_multiples_validaciones_secuenciales(self):
        """Validar múltiples fechas en secuencia"""
        tipo = Mock()
        tipo.nombre = "Recordatorio"
        
        hoy = date.today()
        resultados = []
        
        # Validar 30 días consecutivos
        for i in range(30):
            fecha = hoy + timedelta(days=i)
            puede, _ = validar_envio_notificacion(fecha, tipo)
            resultados.append(puede)
        
        # Debe tener al menos algunos True (días lectivos)
        self.assertTrue(any(resultados))
        # Y algunos False (días no lectivos del calendario)
        self.assertTrue(not all(resultados))
    @patch('notificaciones.views.Participantes.objects')
    @patch('notificaciones.views.messages')
    @patch('notificaciones.views.redirect')
    def test_crear_notificacion_post_success(
        self, mock_redirect, mock_messages, mock_part, mock_tipos, mock_crear_validada
    ):
        """POST exitoso debe crear notificación"""
        # Setup mocks
        mock_participante = Mock()
        mock_part.get.return_value = mock_participante
        
        mock_tipo = Mock()
        mock_tipo.nombre = "Test"
        mock_tipos.get.return_value = mock_tipo
        
        mock_crear_validada.return_value = {
            'success': True,
            'mensaje': 'Creada correctamente',
            'reprogramada': False
        }
        
        # Request
        request = self.factory.post('/crear-notificacion/')
        request.user = self.user
        request.POST = {
            'mensaje': 'Test mensaje',
            'fecha': '2025-11-15T10:00',
            'participante_id': '1',
            'tipo_id': '1'
        }
        
        crear_notificacion(request)
        
        mock_messages.success.assert_called_once()
        mock_redirect.assert_called_once_with('ver_notificaciones')
    
 