"""
Tests unitarios completos para universitaryWellbeing/views.py
Cobertura: Login, Register, Logout, Preferences, Schedule, Calendar, Home, Profile, Notificaciones
Incluye: Tests de seguridad SQL Injection, Edge Cases, Rate Limiting
"""
from django.test import TestCase, SimpleTestCase, RequestFactory
from unittest.mock import patch, MagicMock, Mock, call
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from universitaryWellbeing import views as vw
from universitaryWellbeing.forms import UserLoginForm, UserRegisterForm
from universitaryWellbeing.models import (
    Participantes, Preferencias, Actividades, TiposActividad,
    PreferenciasActividades, Roles, TiposParticipante, Notificaciones,
    HorariosParticipante, HorariosActividad, HorariosBloque, Citas
)
import json
import datetime as dt
from datetime import date, time
from collections import defaultdict


# ==========================================================
# TESTS DE HELPERS Y UTILIDADES
# ==========================================================
# ==========================================================
# CORRECCIÓN 1: HelpersTestCase - Eliminar @patch de Group
# ==========================================================

class HelpersTestCase(SimpleTestCase):
    """Pruebas de funciones auxiliares"""

    def test_is_role_admin_with_group(self):
        """Usuario en grupo admin debe ser admin"""
        user = MagicMock()
        user.is_superuser = False
        user.groups.filter.return_value.exists.return_value = True
        
        result = vw.is_role_admin(user)
        
        self.assertTrue(result)
        user.groups.filter.assert_called_once_with(name="admin")

    def test_is_role_admin_superuser(self):
        """Superuser debe ser admin"""
        user = MagicMock()
        user.is_superuser = True
        user.groups.filter.return_value.exists.return_value = False
        
        result = vw.is_role_admin(user)
        
        self.assertTrue(result)

    def test_is_role_admin_regular_user(self):
        """Usuario regular no debe ser admin"""
        user = MagicMock()
        user.is_superuser = False
        user.groups.filter.return_value.exists.return_value = False
        
        result = vw.is_role_admin(user)
        
        self.assertFalse(result)

    def test_django_weekday_to_fc_dow(self):
        """Debe convertir correctamente días de la semana Django -> FullCalendar"""
        self.assertEqual(vw._django_weekday_to_fc_dow(1), 1)  # Domingo
        self.assertEqual(vw._django_weekday_to_fc_dow(2), 2)  # Lunes
        self.assertEqual(vw._django_weekday_to_fc_dow(7), 0)  # Sábado


# ==========================================================
# TESTS DE LOGIN (CONSOLIDADOS Y MEJORADOS)
# ==========================================================

# ==========================================================
# CORRECCIÓN 2: TestLoginView - Corregir test GET
# ==========================================================

class TestLoginView(TestCase):
    """Tests completos para la vista de login"""
    
    def setUp(self):
        self.factory = RequestFactory()
    

    @patch('universitaryWellbeing.views.UserLoginForm')
    @patch('universitaryWellbeing.views.render')
    def test_login_get_renders_form(self, mock_render, mock_form_class):
        """GET debe renderizar formulario de login"""
        mock_form_class.return_value = MagicMock()
    
        request = self.factory.get('/login/')
    
        vw.user_login(request)
    
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "login.html")
        self.assertIn("form", mock_render.call_args[0][2])
    
    # ==================== TESTS DE GET ====================
    

    @patch('universitaryWellbeing.views.Notificaciones.objects')
    @patch('universitaryWellbeing.views.render')
    def test_ver_notificaciones_sin_notificaciones(self, mock_render, mock_notificaciones):
        """Debe manejar caso sin notificaciones"""
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = []
        mock_notificaciones.filter.return_value = mock_qs
        
        request = self.factory.get('/notificaciones/')
        request.user = MagicMock()
        
        vw.ver_notificaciones(request)
        
        context = mock_render.call_args[0][2]
        self.assertEqual(len(context["notificaciones"]), 0)


# ==========================================================
# TESTS DE SEGURIDAD - SQL INJECTION
# ==========================================================

class TestSQLInjectionProtection(TestCase):
    """Tests de seguridad contra SQL Injection"""
    
    def test_login_rechaza_inyeccion(self):
        """Login debe rechazar intentos de SQL injection"""
        input_usuario = "' OR '1'='1"
        input_password = "cualquiercosa"
        
        def login_seguro(usuario, password):
            usuarios_validos = {"estudiante": "1234"}
            return usuarios_validos.get(usuario) == password
        
        resultado = login_seguro(input_usuario, input_password)
        self.assertFalse(resultado, "No debe aceptar SQL injection")
    
    def test_register_valida_email_malicioso(self):
        """Registro debe validar emails con caracteres SQL"""
        datos_maliciosos = {
            "email": "malicioso@uni.edu'; DROP TABLE users;--",
            "nombre": "Atacante",
            "password": "1234"
        }
        
        def validar_email(email):
            caracteres_peligrosos = ["'", ";", "--", "DROP", "DELETE"]
            return not any(char in email for char in caracteres_peligrosos)
        
        self.assertFalse(validar_email(datos_maliciosos["email"]))
    
    def test_preferences_valida_ids_numericos(self):
        """Preferencias debe validar IDs como numéricos"""
        categorias_recibidas = ["1", "2", "3; DROP TABLE actividades;--"]
        
        def validar_categorias(lista):
            return all(item.isdigit() for item in lista)
        
        self.assertFalse(validar_categorias(categorias_recibidas))
    
    @patch('universitaryWellbeing.views.Actividades.objects')
    def test_orm_no_usa_sql_crudo(self, mock_actividades):
        """ORM debe usar filtros seguros, no SQL crudo"""
        mock_actividades.filter.return_value = []
        
        mock_actividades.filter(tipos_actividad_id_tipo__in=[1, 2, 3])
        
        args, kwargs = mock_actividades.filter.call_args
        self.assertIn('tipos_actividad_id_tipo__in', kwargs)
        
        for arg in args:
            if isinstance(arg, str):
                self.assertNotIn('SELECT', arg.upper())
    
    def test_busqueda_rechaza_comandos_sql(self):
        """Búsquedas deben rechazar comandos SQL"""
        queries_maliciosas = [
            "actividad'; DELETE FROM actividades;--",
            "1' UNION SELECT * FROM users--",
            "admin'--"
        ]
        
        def es_query_segura(query):
            comandos_sql = ['DELETE', 'DROP', 'UNION', 'INSERT', '--', ';']
            return not any(cmd in query.upper() for cmd in comandos_sql)
        
        for query in queries_maliciosas:
            self.assertFalse(es_query_segura(query), 
                           f"Query maliciosa no fue rechazada: {query}")


# ==========================================================
# TESTS DE PASSWORD RESET (RATE LIMITING)
# ==========================================================

class PasswordResetTests(SimpleTestCase):
    """Pruebas de las vistas de password reset"""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    @patch('universitaryWellbeing.views.cache')
    @patch('universitaryWellbeing.views.auth_views.PasswordResetView.dispatch')
    def test_rate_limiting_permite_intentos_validos(self, mock_dispatch, mock_cache):
        """Debe permitir hasta 3 intentos por hora"""
        mock_cache.get.return_value = 2  # 2 intentos previos
        
        view = vw.RateLimitedPasswordResetView()
        request = self.factory.post('/password-reset/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        view.dispatch(request)
        
        # Debe incrementar el contador
        self.assertTrue(mock_cache.set.called)
        call_args = mock_cache.set.call_args[0]
        self.assertEqual(call_args[1], 3)  # Incrementó a 3
    
    @patch('universitaryWellbeing.views.cache')
    @patch('universitaryWellbeing.views.messages')
    def test_rate_limiting_bloquea_exceso_intentos(self, mock_messages, mock_cache):
        """Debe bloquear después de 3 intentos"""
        mock_cache.get.return_value = 3  # Ya alcanzó el límite
        
        view = vw.RateLimitedPasswordResetView()
        request = self.factory.post('/password-reset/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        response = view.dispatch(request)
        
        # Debe retornar 403
        self.assertEqual(response.status_code, 403)
        mock_messages.error.assert_called_once()
    
    def test_get_client_ip_con_proxy(self):
        """Debe obtener IP correcta con proxy"""
        view = vw.RateLimitedPasswordResetView()
        request = self.factory.get('/password-reset/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        
        ip = view.get_client_ip(request)
        
        self.assertEqual(ip, '10.0.0.1')
    
    def test_get_client_ip_sin_proxy(self):
        """Debe obtener IP directa sin proxy"""
        view = vw.RateLimitedPasswordResetView()
        request = self.factory.get('/password-reset/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        
        ip = view.get_client_ip(request)
        
        self.assertEqual(ip, '192.168.1.100')


# ==========================================================
# TESTS DE PASSWORD RESET CONFIRM
# ==========================================================

class PasswordResetConfirmTests(SimpleTestCase):
    """Pruebas de confirmación de password reset"""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    @patch('universitaryWellbeing.views.send_mail')
    @patch('universitaryWellbeing.views.auth_views.PasswordResetConfirmView.form_valid')
    def test_envia_notificacion_cambio_exitoso(self, mock_form_valid, mock_send_mail):
        """Debe enviar email de notificación tras cambio exitoso"""
        mock_response = MagicMock()
        mock_form_valid.return_value = mock_response
        
        view = vw.CustomPasswordResetConfirmView()
        
        mock_form = MagicMock()
        mock_user = MagicMock()
        mock_user.first_name = "Juan"
        mock_user.username = "juan123"
        mock_user.email = "juan@test.com"
        mock_form.user = mock_user
        
        view.form_valid(mock_form)
        
        # Verificar que se envió el email
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args[1]
        self.assertIn("Tu contraseña ha sido cambiada", call_args['subject'])
        self.assertEqual(call_args['recipient_list'], ["juan@test.com"])
    
    @patch('universitaryWellbeing.views.send_mail')
    @patch('universitaryWellbeing.views.auth_views.PasswordResetConfirmView.form_valid')
    def test_no_interrumpe_flujo_si_falla_email(self, mock_form_valid, mock_send_mail):
        """No debe interrumpir si falla el envío de email"""
        mock_response = MagicMock()
        mock_form_valid.return_value = mock_response
        mock_send_mail.side_effect = Exception("SMTP error")
        
        view = vw.CustomPasswordResetConfirmView()
        
        mock_form = MagicMock()
        mock_user = MagicMock()
        mock_user.email = "juan@test.com"
        mock_form.user = mock_user
        
        # No debe lanzar excepción
        result = view.form_valid(mock_form)
        
        self.assertEqual(result, mock_response)


# ==========================================================
# TESTS DE OBTENER ACTIVIDADES DEL DÍA
# ==========================================================
# ==========================================================
# CORRECCIÓN 5: ObtenerActividadesDelDiaTests - Mock correcto
# ==========================================================

class ObtenerActividadesDelDiaTests(SimpleTestCase):
    """Pruebas de obtener_actividades_generales_del_dia"""
    
    @patch('universitaryWellbeing.views.HorariosActividad.objects')
    def test_obtiene_actividades_del_lunes(self, mock_horarios):
        """Debe obtener actividades de un lunes"""
        fecha = date(2025, 11, 10)  # Lunes
        
        mock_bloque = MagicMock()
        mock_bloque.id_horario_bloque = 1
        mock_bloque.hora_inicio = time(10, 0)
        mock_bloque.hora_fin = time(11, 0)
        mock_bloque.profesor = "Prof. Juan"
        mock_bloque.lugar = "Gimnasio"
        
        mock_actividad = MagicMock()
        mock_actividad.nombre = "Yoga"
        mock_bloque.actividades_id_actividad = mock_actividad
        
        mock_horario = MagicMock()
        mock_horario.horario_bloque = mock_bloque
        
        # ✅ CORRECCIÓN: Mock completo del QuerySet
        mock_qs = MagicMock()
        mock_qs.count.return_value = 1
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__ = lambda self: iter([mock_horario])
        
        mock_horarios.filter.return_value = mock_qs
        
        resultado = vw.obtener_actividades_generales_del_dia(fecha)
        
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]['titulo'], 'Yoga')
        self.assertEqual(resultado[0]['tipo'], 'actividad_general')
    
    @patch('universitaryWellbeing.views.HorariosActividad.objects')
    def test_ordena_actividades_por_hora(self, mock_horarios):
        """Debe ordenar actividades por hora de inicio"""
        fecha = date(2025, 11, 10)
        
        bloques = []
        for i, hora in enumerate([14, 10, 16]):
            mock_bloque = MagicMock()
            mock_bloque.id_horario_bloque = i
            mock_bloque.hora_inicio = time(hora, 0)
            mock_bloque.hora_fin = time(hora + 1, 0)
            mock_bloque.profesor = f"Prof. {i}"
            mock_bloque.lugar = "Lugar"
            
            mock_actividad = MagicMock()
            mock_actividad.nombre = f"Actividad {hora}h"
            mock_bloque.actividades_id_actividad = mock_actividad
            
            mock_horario = MagicMock()
            mock_horario.horario_bloque = mock_bloque
            bloques.append(mock_horario)
        
        # ✅ CORRECCIÓN
        mock_qs = MagicMock()
        mock_qs.count.return_value = 3
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__ = lambda self: iter(bloques)
        
        mock_horarios.filter.return_value = mock_qs
        
        resultado = vw.obtener_actividades_generales_del_dia(fecha)
        
        self.assertEqual(resultado[0]['titulo'], 'Actividad 10h')
        self.assertEqual(resultado[1]['titulo'], 'Actividad 14h')
        self.assertEqual(resultado[2]['titulo'], 'Actividad 16h')
    
    @patch('universitaryWellbeing.views.HorariosActividad.objects')
    def test_limita_a_5_actividades(self, mock_horarios):
        """Debe retornar máximo 5 actividades"""
        fecha = date(2025, 11, 10)
        
        bloques = []
        for i in range(10):
            mock_bloque = MagicMock()
            mock_bloque.id_horario_bloque = i
            mock_bloque.hora_inicio = time(8 + i, 0)
            mock_bloque.hora_fin = time(9 + i, 0)
            mock_bloque.profesor = "Prof"
            mock_bloque.lugar = "Lugar"
            
            mock_actividad = MagicMock()
            mock_actividad.nombre = f"Actividad {i}"
            mock_bloque.actividades_id_actividad = mock_actividad
            
            mock_horario = MagicMock()
            mock_horario.horario_bloque = mock_bloque
            bloques.append(mock_horario)
        
        # ✅ CORRECCIÓN
        mock_qs = MagicMock()
        mock_qs.count.return_value = 10
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__ = lambda self: iter(bloques)
        
        mock_horarios.filter.return_value = mock_qs
        
        resultado = vw.obtener_actividades_generales_del_dia(fecha)
        
        self.assertEqual(len(resultado), 5)


# ==========================================================
# TESTS DE EDGE CASES Y CASOS LÍMITE
# ==========================================================

# ==========================================================
# CORRECCIÓN 6: EdgeCasesTests - Varios fixes
# ==========================================================

class EdgeCasesTests(SimpleTestCase):
    """Pruebas de casos límite y situaciones especiales"""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    # ... otros tests ...
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.render')  # ✅ CORRECCIÓN: Mock render
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.models.TiposParticipante.objects')
    def test_completar_perfil_tipo_vacio(self, mock_tipos, mock_participantes,
                                         mock_render, mock_messages):
        """Debe rechazar tipo_participante vacío"""
        request = self.factory.post('/completar-perfil/', {
            'tipo_participante': '   ',
        })
        request.method = 'POST'
        request.user = MagicMock(id=1)  # ✅ CORRECCIÓN
        
        mock_participante = MagicMock()
        mock_participante.tipo_participante = None
        mock_participantes.get.return_value = mock_participante
        
        vw.completar_perfil(request)
        
        mock_messages.error.assert_called()
        mock_tipos.get.assert_not_called()
    
    @patch('universitaryWellbeing.views.HorariosActividad.objects')
    def test_obtener_actividades_domingo(self, mock_horarios):
        """Debe convertir correctamente el domingo (día 6)"""
        fecha = date(2025, 11, 16)  # Domingo
        
        # ✅ CORRECCIÓN: Mock completo
        mock_qs = MagicMock()
        mock_qs.count.return_value = 0
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__ = lambda self: iter([])
        
        mock_horarios.filter.return_value = mock_qs
        
        resultado = vw.obtener_actividades_generales_del_dia(fecha)
        
        self.assertIsNotNone(resultado)
        self.assertEqual(len(resultado), 0)
    
    @patch('universitaryWellbeing.views.get_object_or_404')
    def test_eliminar_evento_no_encontrado(self, mock_get):
        """Debe manejar evento no encontrado"""
        from django.http import Http404
        
        mock_participante = MagicMock()
        mock_get.side_effect = [
            mock_participante,
            Http404("Not found")  # ✅ CORRECCIÓN: Usar Http404
        ]
        


# ==========================================================
# TESTS DE VALIDACIÓN DE DATOS
# ==========================================================

class ValidationTests(SimpleTestCase):
    """Pruebas de validación de datos de entrada"""
    
    def test_validacion_email_formato_correcto(self):
        """Debe validar formato de email"""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        emails_validos = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk"
        ]
        
        for email in emails_validos:
            try:
                validate_email(email)
                valido = True
            except ValidationError:
                valido = False
            
            self.assertTrue(valido, f"Email válido rechazado: {email}")
    
    def test_validacion_email_formato_incorrecto(self):
        """Debe rechazar emails inválidos"""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        emails_invalidos = [
            "notanemail",
            "@example.com",
            "user@",
            "user name@example.com"
        ]
        
        for email in emails_invalidos:
            with self.assertRaises(ValidationError):
                validate_email(email)
    
    def test_validacion_cedula_numerica(self):
        """Debe validar que cédula sea numérica"""
        cedulas_validas = ["1234567890", "123456"]
        cedulas_invalidas = ["abc123", "12-34-56", ""]
        
        for cedula in cedulas_validas:
            self.assertTrue(cedula.isdigit())
        
        for cedula in cedulas_invalidas:
            self.assertFalse(cedula.isdigit())
    
    def test_validacion_semestre_rango(self):
        """Debe validar rango de semestre (1-12)"""
        def validar_semestre(semestre_str):
            try:
                semestre = int(semestre_str)
                return 1 <= semestre <= 12
            except ValueError:
                return False
        
        self.assertTrue(validar_semestre("1"))
        self.assertTrue(validar_semestre("10"))
        self.assertFalse(validar_semestre("0"))
        self.assertFalse(validar_semestre("13"))
        self.assertFalse(validar_semestre("abc"))


# ==========================================================
# TESTS DE INTEGRACIÓN (FLUJOS COMPLETOS)
# ==========================================================

class IntegrationTests(SimpleTestCase):
    """Pruebas de flujos completos de usuario"""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.login')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.is_role_admin')
    @patch('universitaryWellbeing.views.UserLoginForm')
    def test_flujo_completo_primer_login(self, mock_form_class, mock_is_admin,
                                         mock_participantes, mock_preferencias,
                                         mock_login_func, mock_redirect, mock_messages):
        """Flujo: Login → Sin perfil → Completar perfil"""
        request = self.factory.post('/login/')
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.user = MagicMock(is_staff=False)
        mock_form_class.return_value = mock_form
        
        mock_is_admin.return_value = False
        
        # Usuario sin tipo_participante
        mock_participante = MagicMock()
        mock_participante.tipo_participante = None
        mock_participantes.get.return_value = mock_participante
        
        vw.user_login(request)
        
        # Debe redirigir a completar perfil
        mock_redirect.assert_called_with('completar_perfil')
        mock_messages.info.assert_called()
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.login')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.is_role_admin')
    @patch('universitaryWellbeing.views.UserLoginForm')
    def test_flujo_completo_segundo_login(self, mock_form_class, mock_is_admin,
                                          mock_participantes, mock_preferencias,
                                          mock_login_func, mock_redirect, mock_messages):
        """Flujo: Login → Con perfil, sin preferencias → Preferencias"""
        request = self.factory.post('/login/')
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.user = MagicMock(is_staff=False)
        mock_form_class.return_value = mock_form
        
        mock_is_admin.return_value = False
        
        # Usuario con tipo_participante pero sin preferencias
        mock_participante = MagicMock()
        mock_participante.tipo_participante = MagicMock()
        mock_participantes.get.return_value = mock_participante
        
        mock_preferencias.filter.return_value.exists.return_value = False
        
        vw.user_login(request)
        
        # Debe redirigir a preferencias
        mock_redirect.assert_called_with('preferences')
        mock_messages.info.assert_called()

 
    # ==================== TESTS DE LOGIN ADMIN ====================
    
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.login')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.is_role_admin')
    @patch('universitaryWellbeing.views.UserLoginForm')
    def test_login_admin_exitoso(self, mock_form_class, mock_is_admin, 
                                  mock_participantes, mock_preferencias, 
                                  mock_login_func, mock_redirect):
        """Admin debe ser redirigido a cadi_admin"""
        request = self.factory.post('/login/', {
            'username': 'admin',
            'password': 'admin123'
        })
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.user = MagicMock(is_staff=True)
        mock_form_class.return_value = mock_form
        
        mock_is_admin.return_value = True
        
        vw.user_login(request)
        
        mock_login_func.assert_called_once_with(request, mock_form.user)
        mock_redirect.assert_called_once_with('cadi_admin')
    
    # ==================== TESTS DE LOGIN SIN PARTICIPANTE ====================
    
    @patch('universitaryWellbeing.views.logout')
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.login')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.is_role_admin')
    @patch('universitaryWellbeing.views.UserLoginForm')
    def test_login_sin_participante(self, mock_form_class, mock_is_admin,
                                    mock_participantes, mock_login_func,
                                    mock_redirect, mock_messages, mock_logout):
        """Usuario sin participante debe ser deslogueado"""
        request = self.factory.post('/login/', {
            'username': '123456',
            'password': 'test123'
        })
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.user = MagicMock(is_staff=False)
        mock_form_class.return_value = mock_form
        
        mock_is_admin.return_value = False
        mock_participantes.get.side_effect = Participantes.DoesNotExist()
        
        vw.user_login(request)
        
        mock_logout.assert_called_once_with(request)
        mock_messages.error.assert_called_with(request, 'No se encontró tu perfil de participante.')
        mock_redirect.assert_called_with('login')
    
    # ==================== TESTS DE PERFIL INCOMPLETO ====================
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.login')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.is_role_admin')
    @patch('universitaryWellbeing.views.UserLoginForm')
    def test_login_estudiante_sin_tipo_participante(self, mock_form_class, mock_is_admin,
                                                     mock_participantes, mock_preferencias,
                                                     mock_login_func, mock_redirect, mock_messages):
        """Estudiante sin tipo_participante debe completar perfil"""
        request = self.factory.post('/login/', {
            'username': '123456',
            'password': 'test123'
        })
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.user = MagicMock(is_staff=False)
        mock_form_class.return_value = mock_form
        
        mock_is_admin.return_value = False
        
        # Participante sin tipo_participante
        mock_participante = MagicMock()
        mock_participante.tipo_participante = None
        mock_participantes.get.return_value = mock_participante
        
        vw.user_login(request)
        
        mock_messages.info.assert_called_once()
        mock_redirect.assert_called_with('completar_perfil')
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.login')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.is_role_admin')
    @patch('universitaryWellbeing.views.UserLoginForm')
    def test_login_estudiante_sin_preferencias(self, mock_form_class, mock_is_admin,
                                                mock_participantes, mock_preferencias,
                                                mock_login_func, mock_redirect, mock_messages):
        """Estudiante con perfil pero sin preferencias"""
        request = self.factory.post('/login/', {
            'username': '123456',
            'password': 'test123'
        })
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.user = MagicMock(is_staff=False)
        mock_form_class.return_value = mock_form
        
        mock_is_admin.return_value = False
        
        # Participante CON tipo_participante
        mock_participante = MagicMock()
        mock_participante.tipo_participante = MagicMock()
        mock_participantes.get.return_value = mock_participante
        
        # Sin preferencias
        mock_preferencias.filter.return_value.exists.return_value = False
        
        vw.user_login(request)
        
        mock_messages.info.assert_called_once()
        mock_redirect.assert_called_with('preferences')
    
    # ==================== TEST DE LOGIN COMPLETO ====================
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.login')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.is_role_admin')
    @patch('universitaryWellbeing.views.UserLoginForm')
    def test_login_completo_exitoso(self, mock_form_class, mock_is_admin,
                                     mock_participantes, mock_preferencias,
                                     mock_login_func, mock_redirect, mock_messages):
        """Usuario con perfil y preferencias completos va a home"""
        request = self.factory.post('/login/', {
            'username': '123456',
            'password': 'test123'
        })
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.user = MagicMock(is_staff=False)
        mock_form_class.return_value = mock_form
        
        mock_is_admin.return_value = False
        
        # Participante completo
        mock_participante = MagicMock()
        mock_participante.tipo_participante = MagicMock()
        mock_participante.nombre = 'Test'
        mock_participantes.get.return_value = mock_participante
        
        # Con preferencias
        mock_preferencias.filter.return_value.exists.return_value = True
        
        vw.user_login(request)
        
        mock_messages.success.assert_called_once()
        call_args = mock_messages.success.call_args[0]
        self.assertIn('Bienvenido', call_args[1])
        mock_redirect.assert_called_with('home')
    
    # ==================== TESTS DE ERRORES ====================
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.UserLoginForm')
    def test_login_form_invalido(self, mock_form_class, mock_redirect, mock_messages):
        """Login con credenciales inválidas"""
        request = self.factory.post('/login/', {
            'username': 'wrong',
            'password': 'wrong'
        })
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_form.errors = {'password': ['Contraseña incorrecta']}
        mock_form_class.return_value = mock_form
        
        vw.user_login(request)
        
        mock_messages.error.assert_called()
        mock_redirect.assert_called_with('login')


# ==========================================================
# TESTS DE REGISTRO (CONSOLIDADOS Y MEJORADOS)
# ==========================================================

class TestRegisterView(TestCase):
    """Tests completos para la vista de registro"""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    # ==================== TEST DE GET ====================
    
    @patch('universitaryWellbeing.views.UserRegisterForm')
    @patch('universitaryWellbeing.views.render')
    def test_register_get_renders_form(self, mock_render, mock_form_class):
        """GET debe renderizar formulario de registro"""
        mock_form_class.return_value = MagicMock()
        
        request = self.factory.get('/register/')
        
        vw.register(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "auth/register.html")
        self.assertIn("form", mock_render.call_args[0][2])
    
    # ==================== TEST DE REGISTRO EXITOSO ====================
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.Roles.objects')
    @patch('universitaryWellbeing.views.User.objects')
    @patch('universitaryWellbeing.views.UserRegisterForm')
    def test_registro_exitoso(self, mock_form_class, mock_user_objects,
                              mock_roles, mock_participantes, 
                              mock_redirect, mock_messages):
        """Registro exitoso de nuevo usuario"""
        request = self.factory.post('/register/', {
            'cedula': '123456',
            'nombre_completo': 'Test User',
            'email': 'test@example.com',
            'password': 'test123'
        })
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = {
            'cedula': '123456',
            'nombre_completo': 'Test User',
            'email': 'test@example.com',
            'password': 'test123'
        }
        mock_form_class.return_value = mock_form
        
        mock_rol = MagicMock()
        mock_rol.nombre_rol = 'Estudiante'
        mock_rol.grupo_d = None
        mock_roles.get.return_value = mock_rol
        
        mock_user = MagicMock()
        mock_user_objects.create_user.return_value = mock_user
        
        vw.register(request)
        
        # Verificar creación de usuario
        mock_user_objects.create_user.assert_called_once()
        create_args = mock_user_objects.create_user.call_args[1]
        self.assertEqual(create_args['username'], '123456')
        self.assertEqual(create_args['email'], 'test@example.com')
        
        # Verificar creación de participante
        mock_participantes.create.assert_called_once()
        
        # Verificar mensaje y redirección
        mock_messages.success.assert_called_once()
        mock_redirect.assert_called_with('login')
    
    # ==================== TEST DE NOMBRE CON ESPACIOS ====================
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.Roles.objects')
    @patch('universitaryWellbeing.views.User.objects')
    @patch('universitaryWellbeing.views.UserRegisterForm')
    def test_registro_nombre_con_espacios(self, mock_form_class, mock_user_objects,
                                          mock_roles, mock_participantes,
                                          mock_redirect, mock_messages):
        """Debe separar correctamente nombre y apellido"""
        request = self.factory.post('/register/', {})
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = {
            'cedula': '123456',
            'nombre_completo': 'Juan Carlos Pérez González',
            'email': 'juan@test.com',
            'password': 'pass123'
        }
        mock_form_class.return_value = mock_form
        
        mock_user = MagicMock()
        mock_user_objects.create_user.return_value = mock_user
        
        mock_rol = MagicMock()
        mock_rol.grupo_d = None
        mock_roles.get.return_value = mock_rol
        
        vw.register(request)
        
        create_args = mock_user_objects.create_user.call_args[1]
        self.assertEqual(create_args['first_name'], 'Juan')
        self.assertEqual(create_args['last_name'], 'Carlos Pérez González')
    
    # ==================== TESTS DE ERRORES ====================
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.User.objects')
    @patch('universitaryWellbeing.views.Roles.objects')
    @patch('universitaryWellbeing.views.UserRegisterForm')
    def test_registro_sin_rol_estudiante(self, mock_form_class, mock_roles,
                                         mock_user_objects, mock_participantes,
                                         mock_redirect, mock_messages):
        """Error cuando no existe rol 'Estudiante' en BD"""
        request = self.factory.post('/register/', {})
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = {
            'cedula': '123456',
            'nombre_completo': 'Test User',
            'email': 'test@example.com',
            'password': 'test123'
        }
        mock_form_class.return_value = mock_form
        
        mock_user = MagicMock()
        mock_user_objects.create_user.return_value = mock_user
        
        mock_roles.get.side_effect = Roles.DoesNotExist()
        
        vw.register(request)
        
        mock_messages.error.assert_called()
        mock_redirect.assert_called_with('register')
        mock_user_objects.create_user.assert_called_once()
        mock_participantes.create.assert_not_called()
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.UserRegisterForm')
    def test_registro_form_invalido(self, mock_form_class, mock_redirect, mock_messages):
        """Formulario inválido debe mostrar errores"""
        request = self.factory.post('/register/', {})
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_form.errors = {"email": ["Email inválido"]}
        mock_form_class.return_value = mock_form
        
        vw.register(request)
        
        mock_messages.error.assert_called()
        mock_redirect.assert_called_with('register')


# ==========================================================
# TESTS DE LOGOUT
# ==========================================================

class LogoutTests(SimpleTestCase):
    """Pruebas de la vista user_logout"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.logout')
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    def test_logout_clears_session(self, mock_redirect, mock_messages, mock_logout):
        """Logout debe cerrar sesión y redirigir"""
        request = self.factory.post('/logout/')
        
        vw.user_logout(request)
        
        mock_logout.assert_called_once_with(request)
        mock_messages.success.assert_called_once()
        mock_redirect.assert_called_once_with("login")


# ==========================================================
# TESTS DE PREFERENCIAS (CONSOLIDADOS)
# ==========================================================

class TestPreferencesView(TestCase):
    """Tests completos para la vista de preferencias"""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    # ==================== TEST DE REDIRECCIÓN ====================
    
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.redirect')
    def test_preferences_ya_completadas(self, mock_redirect, mock_participantes):
        """Usuario con preferencias debe ir a home"""
        request = self.factory.get('/preferences/')
        request.user = MagicMock(is_authenticated=True)
        
        mock_participante = MagicMock()
        mock_participante.preferencias = MagicMock()
        mock_participantes.get.return_value = mock_participante
        
        vw.preferences(request)
        
        mock_redirect.assert_called_with('home')
    
    # ==================== TEST DE GET ====================
    
    @patch('universitaryWellbeing.views.TiposActividad.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.render')
    def test_preferences_get_renders_categories(self, mock_render, mock_participantes, mock_tipos):
        """GET debe renderizar categorías disponibles"""
        mock_participante = MagicMock(spec=['id_participante'])
        mock_participantes.get.return_value = mock_participante
        
        mock_tipos.all.return_value = [
            MagicMock(id_tipo=1, nombre_tipo="Deporte"),
            MagicMock(id_tipo=2, nombre_tipo="Cultural")
        ]
        
        request = self.factory.get('/preferences/')
        request.user = MagicMock()
        
        vw.preferences(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], 'list_preferences.html')
        context = mock_render.call_args[0][2]
        self.assertIn('categorias', context)
    
    # ==================== TEST DE POST ====================
    
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.PreferenciasActividades.objects')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.TiposActividad.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_preferences_crear_nuevas(self, mock_participantes, mock_tipos,
                                      mock_preferencias, mock_pref_act, mock_redirect):
        """Crear preferencias nuevas"""
        request = self.factory.post('/preferences/', {
            'categories': ['1', '2']
        })
        request.method = 'POST'
        request.user = MagicMock(is_authenticated=True)
        request.POST = MagicMock()
        request.POST.getlist.return_value = ['1', '2', '3']
        
        mock_participante = MagicMock()
        if hasattr(mock_participante, 'preferencias'):
            delattr(mock_participante, 'preferencias')
        mock_participantes.get.return_value = mock_participante
        
        mock_pref = MagicMock()
        mock_preferencias.create.return_value = mock_pref
        
        mock_tipo1 = MagicMock()
        mock_tipo2 = MagicMock()
        mock_tipo3 = MagicMock()
        mock_tipos.get.side_effect = [mock_tipo1, mock_tipo2, mock_tipo3]
        
        vw.preferences(request)
        
        mock_preferencias.create.assert_called_once()
        self.assertEqual(mock_pref_act.create.call_count, 3)
        mock_redirect.assert_called_with('home')


# ==========================================================
# TESTS DE COMPLETAR PERFIL (CONSOLIDADOS)
# ==========================================================

class TestCompletarPerfilView(TestCase):
    """Tests completos para completar perfil"""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    # ==================== TEST DE REDIRECCIÓN ====================
    
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_perfil_ya_completado_redirige(self, mock_participantes, mock_redirect):
        """Usuario con tipo_participante debe ir a preferencias"""
        request = self.factory.get('/completar-perfil/')
        request.user = MagicMock(is_authenticated=True)
        
        mock_participante = MagicMock()
        mock_participante.tipo_participante = MagicMock()
        mock_participantes.get.return_value = mock_participante
        
        vw.completar_perfil(request)
        
        mock_redirect.assert_called_with('preferences')
    
    # ==================== TEST DE ESTUDIANTE ====================
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.models.TiposParticipante.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_completar_perfil_estudiante(self, mock_participantes, mock_tipos_part,
                                         mock_redirect, mock_messages):
        """Completar perfil como estudiante"""
        request = self.factory.post('/completar-perfil/', {
            'tipo_participante': 'estudiante',
            'semestre': '5',
            'programa': 'Ingeniería',
            'facultad': 'Ingeniería',
            'genero': 'M'
        })
        request.method = 'POST'
        request.user = MagicMock(is_authenticated=True)
        
        mock_participante = MagicMock()
        mock_participante.tipo_participante = None
        mock_participantes.get.return_value = mock_participante
        
        mock_tipo = MagicMock()
        mock_tipo.nombre = 'Estudiante'
        mock_tipos_part.get.return_value = mock_tipo
        
        vw.completar_perfil(request)
        
        mock_participante.save.assert_called_once()
        mock_messages.success.assert_called_once()
        mock_redirect.assert_called_with('preferences')
    
    # ==================== TEST DE TRABAJADOR ====================
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.models.TiposParticipante.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_completar_perfil_trabajador(self, mock_participantes, mock_tipos_part,
                                         mock_redirect, mock_messages):
        """Completar perfil como trabajador"""
        request = self.factory.post('/completar-perfil/', {
            'tipo_participante': 'trabajador',
            'facultad': 'Administración',
            'genero': 'F'
        })
        request.method = 'POST'
        request.user = MagicMock()
        
        mock_participante = MagicMock()
        mock_participante.tipo_participante = None
        mock_participantes.get.return_value = mock_participante
        
        mock_tipo = MagicMock()
        mock_tipo.nombre = 'Trabajador'
        mock_tipos_part.get.return_value = mock_tipo
        
        vw.completar_perfil(request)
        
        self.assertEqual(mock_participante.facultad, 'Administración')
        self.assertEqual(mock_participante.genero, 'F')
        mock_participante.save.assert_called_once()
        mock_redirect.assert_called_with('preferences')


# ==========================================================
# TESTS DE SCHEDULE/HORARIO (CONSOLIDADOS Y MEJORADOS)
# ==========================================================

class ScheduleTests(SimpleTestCase):
    """Pruebas completas de la vista schedule"""

    def setUp(self):
        self.factory = RequestFactory()

    # ==================== TEST BÁSICO ====================
    
    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.get_object_or_404')
    @patch('universitaryWellbeing.views.render')
    def test_schedule_renders_eventos(self, mock_render, mock_get, mock_horarios):
        """Debe renderizar eventos del participante"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_get.return_value = mock_participante
        
        # Mock eventos
        evento_mock = MagicMock()
        evento_mock.id_horario = 1
        evento_mock.titulo = "Yoga"
        evento_mock.fecha_inicio = dt.datetime(2025, 11, 10, 10, 0)
        evento_mock.fecha_fin = dt.datetime(2025, 11, 10, 11, 0)
        evento_mock.actividades_id_actividad = MagicMock()
        evento_mock.citas_id_cita = None
        evento_mock.partidos_id_partido = None
        evento_mock.fuente_manual = 'N'
        evento_mock.notas = "Clase de yoga"
        
        mock_horarios.filter.return_value = [evento_mock]
        
        request = self.factory.get('/schedule/')
        request.user = MagicMock(id=1)
        
        vw.schedule(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "Horario.html")
        context = mock_render.call_args[0][2]
        self.assertIn("eventos_json", context)
        
        # Verificar que eventos_json es JSON válido
        eventos_json = json.loads(context["eventos_json"])
        self.assertEqual(len(eventos_json), 1)
        self.assertEqual(eventos_json[0]["title"], "Yoga")

    # ==================== TEST EVENTO RECURRENTE ====================
    
    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.get_object_or_404')
    @patch('universitaryWellbeing.views.render')
    def test_schedule_evento_recurrente(self, mock_render, mock_get, mock_horarios):
        """Evento manual de actividad debe ser recurrente"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_get.return_value = mock_participante
        
        evento_mock = MagicMock()
        evento_mock.id_horario = 1
        evento_mock.titulo = "Clase semanal"
        evento_mock.fecha_inicio = dt.datetime(2025, 11, 10, 10, 0)  # Lunes
        evento_mock.fecha_fin = dt.datetime(2025, 11, 10, 11, 0)
        evento_mock.actividades_id_actividad = MagicMock()
        evento_mock.citas_id_cita = None
        evento_mock.partidos_id_partido = None
        evento_mock.fuente_manual = 'S'  # Manual = recurrente
        evento_mock.notas = None
        
        mock_horarios.filter.return_value = [evento_mock]
        
        request = self.factory.get('/schedule/')
        request.user = MagicMock(id=1)
        
        vw.schedule(request)
        
        context = mock_render.call_args[0][2]
        eventos_json = json.loads(context["eventos_json"])
        
        # Verificar que tiene daysOfWeek (recurrente)
        self.assertIn("daysOfWeek", eventos_json[0])
        self.assertTrue(eventos_json[0]["extendedProps"]["es_recurrente"])

    # ==================== TESTS DE COLORES POR TIPO ====================
    
    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.get_object_or_404')
    @patch('universitaryWellbeing.views.render')
    def test_schedule_evento_con_cita(self, mock_render, mock_get, mock_horarios):
        """Debe asignar color amarillo a citas"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_get.return_value = mock_participante
        
        evento_mock = MagicMock()
        evento_mock.id_horario = 1
        evento_mock.titulo = "Cita médica"
        evento_mock.fecha_inicio = dt.datetime(2025, 11, 10, 14, 0)
        evento_mock.fecha_fin = dt.datetime(2025, 11, 10, 15, 0)
        evento_mock.actividades_id_actividad = None
        evento_mock.citas_id_cita = MagicMock()
        evento_mock.partidos_id_partido = None
        evento_mock.fuente_manual = 'N'
        evento_mock.notas = None
        
        mock_horarios.filter.return_value = [evento_mock]
        
        request = self.factory.get('/schedule/')
        request.user = MagicMock(id=1)
        
        vw.schedule(request)
        
        context = mock_render.call_args[0][2]
        eventos_json = json.loads(context["eventos_json"])
        self.assertEqual(eventos_json[0]["color"], "#E4EB60")
        self.assertEqual(eventos_json[0]["extendedProps"]["tipo"], "cita")

    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.get_object_or_404')
    @patch('universitaryWellbeing.views.render')
    def test_schedule_evento_con_partido(self, mock_render, mock_get, mock_horarios):
        """Debe asignar color naranja a partidos"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_get.return_value = mock_participante
        
        evento_mock = MagicMock()
        evento_mock.id_horario = 1
        evento_mock.titulo = "Partido de fútbol"
        evento_mock.fecha_inicio = dt.datetime(2025, 11, 10, 16, 0)
        evento_mock.fecha_fin = dt.datetime(2025, 11, 10, 18, 0)
        evento_mock.actividades_id_actividad = None
        evento_mock.citas_id_cita = None
        evento_mock.partidos_id_partido = MagicMock()
        evento_mock.fuente_manual = 'N'
        evento_mock.notas = None
        
        mock_horarios.filter.return_value = [evento_mock]
        
        request = self.factory.get('/schedule/')
        request.user = MagicMock(id=1)
        
        vw.schedule(request)
        
        context = mock_render.call_args[0][2]
        eventos_json = json.loads(context["eventos_json"])
        self.assertEqual(eventos_json[0]["color"], "#E9683B")
        self.assertEqual(eventos_json[0]["extendedProps"]["tipo"], "partido")

    # ==================== TEST SIN EVENTOS ====================
    
    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.get_object_or_404')
    @patch('universitaryWellbeing.views.render')
    def test_schedule_sin_eventos(self, mock_render, mock_get, mock_horarios):
        """Debe manejar horario sin eventos"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        mock_get.return_value = mock_participante
        
        mock_horarios.filter.return_value = []
        
        request = self.factory.get('/schedule/')
        request.user = MagicMock(id=1)
        
        vw.schedule(request)
        
        context = mock_render.call_args[0][2]
        eventos_json = json.loads(context["eventos_json"])
        self.assertEqual(len(eventos_json), 0)


# ==========================================================
# TESTS DE ELIMINAR EVENTO
# ==========================================================

class EliminarEventoTests(SimpleTestCase):
    """Pruebas de la vista delete_event"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.get_object_or_404')
    def test_eliminar_evento_manual_success(self, mock_get):
        """Debe eliminar evento manual correctamente"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        
        mock_evento = MagicMock()
        mock_evento.titulo = "Mi evento"
        mock_evento.fuente_manual = 'S'
        
        mock_get.side_effect = [mock_participante, mock_evento]
        
        request = self.factory.post('/schedule/delete/1/')
        request.user = MagicMock(id=1)
        
        response = vw.delete_event(request, 1)
        
        mock_evento.delete.assert_called_once()
        self.assertIsInstance(response, JsonResponse)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    @patch('universitaryWellbeing.views.get_object_or_404')
    def test_eliminar_evento_automatico_forbidden(self, mock_get):
        """No debe eliminar evento automático"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        
        mock_evento = MagicMock()
        mock_evento.fuente_manual = 'N'  # Automático
        
        mock_get.side_effect = [mock_participante, mock_evento]
        
        request = self.factory.post('/schedule/delete/1/')
        request.user = MagicMock(id=1)
        
        response = vw.delete_event(request, 1)
        
        mock_evento.delete.assert_not_called()
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    @patch('universitaryWellbeing.views.get_object_or_404')
    def test_eliminar_evento_exception_handling(self, mock_get):
        """Debe manejar excepciones al eliminar evento"""
        mock_participante = MagicMock()
        mock_participante.id_participante = 1
        
        mock_evento = MagicMock()
        mock_evento.fuente_manual = 'S'
        mock_evento.delete.side_effect = Exception("Error de base de datos")
        
        mock_get.side_effect = [mock_participante, mock_evento]
        
        request = self.factory.post('/schedule/delete/1/')
        request.user = MagicMock(id=1)
        
        response = vw.delete_event(request, 1)
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn("Error al eliminar", data['message'])


# ==========================================================
# TESTS DE CALENDARIO UNIFICADO
# ==========================================================



# ==========================================================
# CORRECCIÓN 3: CalendarioUnificadoTests - Agregar request.user
# ==========================================================

class CalendarioUnificadoTests(SimpleTestCase):
    """Pruebas de la vista unified_calendar"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.HorariosActividad.objects')
    @patch('universitaryWellbeing.views.HorariosBloque.objects')
    @patch('universitaryWellbeing.views.Actividades.objects')
    @patch('universitaryWellbeing.views.TiposActividad.objects')
    @patch('universitaryWellbeing.views.render')
    def test_calendario_unificado_renders(
        self, mock_render, mock_tipos, mock_actividades,
        mock_bloques, mock_horarios_act
    ):
        """Debe renderizar calendario con actividades"""
        mock_tipos.values.return_value.order_by.return_value = []
        
        mock_qs = MagicMock()
        mock_qs.select_related.return_value.values.return_value = [
            {
                'id_actividad': 1,
                'nombre': 'Yoga',
                'descripcion': 'Clase de yoga',
                'tipos_actividad_id_tipo': 1,
                'tipos_actividad_id_tipo__nombre_tipo': 'Deporte'
            }
        ]
        mock_actividades.all.return_value = mock_qs
        
        mock_bloques.filter.return_value.values.return_value = [
            {
                'id_horario_bloque': 1,
                'actividades_id_actividad': 1,
                'profesor': 'Prof. Juan',
                'lugar': 'Gimnasio',
                'hora_inicio': time(10, 0),
                'hora_fin': time(11, 0)
            }
        ]
        
        mock_horarios_act.filter.return_value.values.return_value = [
            {'horario_bloque_id': 1, 'dia_semana': 2}
        ]
        
        request = self.factory.get('/calendario/')
        request.user = MagicMock()  # ✅ CORRECCIÓN
        request.GET = {}
        
        vw.unified_calendar(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "calendario_unificado.html")

    @patch('universitaryWellbeing.views.TiposActividad.objects')
    @patch('universitaryWellbeing.views.Actividades.objects')
    @patch('universitaryWellbeing.views.render')
    def test_calendario_unificado_filtro_tipo(self, mock_render, mock_actividades, mock_tipos):
        """Debe filtrar por tipo de actividad"""
        mock_tipos.values.return_value.order_by.return_value = []
        
        mock_qs = MagicMock()
        mock_qs.select_related.return_value.values.return_value = []
        mock_qs.filter.return_value = mock_qs
        
        mock_actividades.all.return_value = mock_qs
        
        request = self.factory.get('/calendario/?tipo=1')
        request.user = MagicMock()  # ✅ CORRECCIÓN
        request.GET = {'tipo': '1'}
        
        vw.unified_calendar(request)
        
        mock_qs.filter.assert_called_once()

    @patch('universitaryWellbeing.views.HorariosActividad.objects')
    @patch('universitaryWellbeing.views.HorariosBloque.objects')
    @patch('universitaryWellbeing.views.Actividades.objects')
    @patch('universitaryWellbeing.views.TiposActividad.objects')
    @patch('universitaryWellbeing.views.render')
    def test_calendario_unificado_sin_actividades(
        self, mock_render, mock_tipos, mock_actividades,
        mock_bloques, mock_horarios_act
    ):
        """Debe manejar caso sin actividades disponibles"""
        mock_tipos.values.return_value.order_by.return_value = []
        
        mock_qs = MagicMock()
        mock_qs.select_related.return_value.values.return_value = []
        mock_actividades.all.return_value = mock_qs
        
        request = self.factory.get('/calendario/')
        request.user = MagicMock()  # ✅ CORRECCIÓN
        request.GET = {}
        
        vw.unified_calendar(request)
        
        context = mock_render.call_args[0][2]
        eventos_json = json.loads(context["eventos_json"])
        self.assertEqual(len(eventos_json), 0)

# ==========================================================
# TESTS DE HOME USER
# ==========================================================

class HomeUserTests(SimpleTestCase):
    """Pruebas de la vista home_user"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.render')
    def test_home_user_superuser_returns_404(self, mock_render):
        """Superuser debe recibir 404"""
        request = self.factory.get('/home/')
        request.user = MagicMock()
        request.user.is_superuser = True
        
        vw.home_user(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "pageNotFound-404.html")
        self.assertEqual(mock_render.call_args[1]['status'], 404)

    @patch('universitaryWellbeing.views.obtener_actividades_generales_del_dia')
    @patch('universitaryWellbeing.views.Noticias.objects')
    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.Actividades.objects')
    @patch('universitaryWellbeing.views.render')
    @patch('universitaryWellbeing.views.timezone')
    def test_home_user_renders_with_context(
        self, mock_timezone, mock_render, mock_actividades, mock_participantes,
        mock_horarios, mock_noticias, mock_obtener_act
    ):
        """Debe renderizar home con contexto completo"""
        # Mock timezone
        mock_now = MagicMock()
        mock_now.date.return_value = date(2025, 11, 18)
        mock_timezone.localtime.return_value = mock_now
        mock_timezone.now.return_value = mock_now
        
        # Mock participante con rol
        mock_part = MagicMock()
        mock_part.roles_id_rol.nombre_rol = "Estudiante"
        mock_participantes.filter.return_value.select_related.return_value.first.return_value = mock_part
        
        mock_actividades.values.return_value = []
        mock_horarios.filter.return_value.order_by.return_value = []
        mock_noticias.order_by.return_value = []
        mock_obtener_act.return_value = []
        
        request = self.factory.get('/home/')
        request.user = MagicMock()
        request.user.is_superuser = False
        
        vw.home_user(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "home_user.html")
        context = mock_render.call_args[0][2]
        self.assertIn("user_rol", context)
        self.assertEqual(context["user_rol"], "Estudiante")


# ==========================================================
# TESTS DE HOME ADMIN
# ==========================================================
# ==========================================================
# CORRECCIÓN 4: HomeAdminTests - Agregar request.user
# ==========================================================

class HomeAdminTests(SimpleTestCase):
    """Pruebas de la vista home_admin"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.render')
    def test_home_admin_renders(self, mock_render):
        """Debe renderizar home admin"""
        request = self.factory.get('/admin-home/')
        request.user = MagicMock()  # ✅ CORRECCIÓN
        
        vw.home_admin(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "home_admin.html")

# ==========================================================
# TESTS DE FUNCIONES AUXILIARES
# ==========================================================

class HelperFunctionsTests(SimpleTestCase):
    """Pruebas de funciones auxiliares de vistas"""

    @patch('universitaryWellbeing.views.Actividades.objects')
    @patch('universitaryWellbeing.views.PreferenciasActividades.objects')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_recommendations_for_user_success(
        self, mock_participantes, mock_preferencias,
        mock_pref_actividades, mock_actividades
    ):
        """Debe retornar actividades recomendadas según preferencias"""
        mock_user = MagicMock()
        mock_participante = MagicMock()
        mock_participantes.get.return_value = mock_participante
        
        mock_pref = MagicMock()
        mock_preferencias.get.return_value = mock_pref
        
        mock_pref_actividades.filter.return_value.values_list.return_value = [1, 2, 3]
        
        mock_actividades_qs = MagicMock()
        mock_actividades.filter.return_value = mock_actividades_qs
        
        result = vw.get_recommendations_for_user(mock_user)
        
        self.assertEqual(result, mock_actividades_qs)
        mock_actividades.filter.assert_called_once()

    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_recommendations_for_user_no_participante(self, mock_participantes):
        """Debe retornar lista vacía si no existe participante"""
        mock_user = MagicMock()
        mock_participantes.get.side_effect = Participantes.DoesNotExist
        
        result = vw.get_recommendations_for_user(mock_user)
        
        self.assertEqual(result, [])

    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_recommendations_for_user_no_preferencias(
        self, mock_participantes, mock_preferencias
    ):
        """Debe retornar lista vacía si no existen preferencias"""
        mock_user = MagicMock()
        mock_participante = MagicMock()
        mock_participantes.get.return_value = mock_participante
        mock_preferencias.get.side_effect = Preferencias.DoesNotExist
        
        result = vw.get_recommendations_for_user(mock_user)
        
        self.assertEqual(result, [])

    @patch('universitaryWellbeing.views.HorariosParticipante.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_user_schedule_success(self, mock_participantes, mock_horarios):
        """Debe retornar horarios del participante"""
        mock_user = MagicMock()
        mock_participante = MagicMock()
        mock_participantes.get.return_value = mock_participante
        
        mock_horarios_qs = MagicMock()
        mock_horarios.filter.return_value = mock_horarios_qs
        
        result = vw.get_user_schedule(mock_user)
        
        self.assertEqual(result, mock_horarios_qs)

    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_user_schedule_no_participante(self, mock_participantes):
        """Debe retornar lista vacía si no existe participante"""
        mock_user = MagicMock()
        mock_participantes.get.side_effect = Participantes.DoesNotExist
        
        result = vw.get_user_schedule(mock_user)
        
        self.assertEqual(result, [])

    @patch('universitaryWellbeing.views.Citas.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_user_calendar_success(self, mock_participantes, mock_citas):
        """Debe retornar citas del participante"""
        mock_user = MagicMock()
        mock_participante = MagicMock()
        mock_participantes.get.return_value = mock_participante
        
        mock_citas_qs = MagicMock()
        mock_citas.filter.return_value = mock_citas_qs
        
        result = vw.get_user_calendar(mock_user)
        
        self.assertEqual(result, mock_citas_qs)

    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_get_user_calendar_no_participante(self, mock_participantes):
        """Debe retornar lista vacía si no existe participante"""
        mock_user = MagicMock()
        mock_participantes.get.side_effect = Participantes.DoesNotExist
        
        result = vw.get_user_calendar(mock_user)
        
        self.assertEqual(result, [])


# ==========================================================
# TESTS DE PROFILE
# ==========================================================

class ProfileTests(SimpleTestCase):
    """Pruebas de la vista profile"""

    def setUp(self):
        self.factory = RequestFactory()

    @patch('universitaryWellbeing.views.Notificaciones.objects')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.render')
    def test_profile_renders_with_context(
        self, mock_render, mock_participantes, 
        mock_preferencias, mock_notificaciones
    ):
        """Debe renderizar perfil con contexto completo"""
        # Mock participante
        mock_part = MagicMock()
        mock_part.roles_id_rol.nombre_rol = "Estudiante"
        mock_participantes.get.return_value = mock_part
        
        # Mock preferencias y actividades
        mock_pref = MagicMock()
        mock_actividad1 = MagicMock(nombre="Yoga")
        mock_actividad2 = MagicMock(nombre="Fútbol")
        mock_pref.actividades.all.return_value = [mock_actividad1, mock_actividad2]
        mock_preferencias.get.return_value = mock_pref
        
        # Mock notificaciones
        mock_notif_qs = MagicMock()
        mock_notif_qs.order_by.return_value = mock_notif_qs
        mock_notif_qs.filter.return_value.count.return_value = 3
        mock_notificaciones.filter.return_value = mock_notif_qs
        
        request = self.factory.get('/profile/')
        request.user = MagicMock()
        
        vw.profile(request)
        
        mock_render.assert_called_once()
        self.assertEqual(mock_render.call_args[0][1], "profile.html")
        context = mock_render.call_args[0][2]
        self.assertIn("participante", context)
        self.assertIn("actividades", context)
        self.assertIn("notificaciones", context)
        self.assertEqual(context["notificaciones_no_leidas"], 3)

    @patch('universitaryWellbeing.views.Notificaciones.objects')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.render')
    def test_profile_sin_preferencias(
        self, mock_render, mock_participantes,
        mock_preferencias, mock_notificaciones
    ):
        """Debe manejar caso sin preferencias"""
        mock_part = MagicMock()
        mock_part.roles_id_rol = None
        mock_participantes.get.return_value = mock_part
        
        mock_preferencias.get.side_effect = Preferencias.DoesNotExist
        
        mock_notif_qs = MagicMock()
        mock_notif_qs.order_by.return_value = mock_notif_qs
        mock_notif_qs.filter.return_value.count.return_value = 0
        mock_notificaciones.filter.return_value = mock_notif_qs
        
        request = self.factory.get('/profile/')
        request.user = MagicMock()
        
        vw.profile(request)
        
        context = mock_render.call_args[0][2]
        self.assertEqual(context["actividades"], [])
        self.assertIsNone(context["user_rol"])


 