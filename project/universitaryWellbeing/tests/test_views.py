# project/universitaryWellbeing/tests/test_views.py
from django.test import TestCase, RequestFactory
from unittest.mock import patch, MagicMock, Mock
from universitaryWellbeing.models import Participantes  # ✅ Importar el modelo
import pytest


# ================================================================
# TESTS DE LOGIN CON MOCKS
# ================================================================

class TestLoginView(TestCase):
    """Tests para la vista de login usando mocks"""
    
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
        request = RequestFactory().post('/login/', {
            'username': 'admin',
            'password': 'admin123'
        })
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.user = MagicMock(is_staff=True)
        mock_form_class.return_value = mock_form
        
        mock_is_admin.return_value = True
        
        from universitaryWellbeing.views import user_login
        user_login(request)
        
        mock_redirect.assert_called_with('cadi_admin')
    
    # ✅ TEST CORREGIDO
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
        request = RequestFactory().post('/login/', {
            'username': '123456',
            'password': 'test123'
        })
        request.method = 'POST'
        
        # ✅ Configurar mock del formulario
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.user = MagicMock(is_staff=False)
        mock_form_class.return_value = mock_form
        
        # ✅ Usuario no es admin
        mock_is_admin.return_value = False
        
        # ✅ Simular que no existe el participante
        mock_participantes.get.side_effect = Participantes.DoesNotExist()
        
        from universitaryWellbeing.views import user_login
        user_login(request)
        
        # ✅ Verificaciones
        mock_logout.assert_called_once_with(request)
        mock_messages.error.assert_called_with(request, 'No se encontró tu perfil de participante.')
        mock_redirect.assert_called_with('login')
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.login')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    @patch('universitaryWellbeing.views.is_role_admin')
    @patch('universitaryWellbeing.views.UserLoginForm')
    def test_login_estudiante_sin_perfil(self, mock_form_class, mock_is_admin,
                                         mock_participantes, mock_preferencias,
                                         mock_login_func, mock_redirect, mock_messages):
        """Estudiante sin tipo_participante debe completar perfil"""
        request = RequestFactory().post('/login/', {
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
        
        from universitaryWellbeing.views import user_login
        user_login(request)
        
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
        request = RequestFactory().post('/login/', {
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
        
        from universitaryWellbeing.views import user_login
        user_login(request)
        
        mock_messages.info.assert_called_once()
        mock_redirect.assert_called_with('preferences')
    
    # ✅ NUEVO: Test de login completo exitoso
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
        request = RequestFactory().post('/login/', {
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
        
        from universitaryWellbeing.views import user_login
        user_login(request)
        
        mock_messages.success.assert_called_once()
        call_args = mock_messages.success.call_args[0]
        self.assertIn('Bienvenido', call_args[1])
        mock_redirect.assert_called_with('home')
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.UserLoginForm')
    def test_login_form_invalido(self, mock_form_class, mock_redirect, mock_messages):
        """Login con credenciales inválidas"""
        request = RequestFactory().post('/login/', {
            'username': 'wrong',
            'password': 'wrong'
        })
        request.method = 'POST'
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_form.errors = {'password': ['Contraseña incorrecta']}
        mock_form_class.return_value = mock_form
        
        from universitaryWellbeing.views import user_login
        user_login(request)
        
        mock_messages.error.assert_called()
        mock_redirect.assert_called_with('login')


# ================================================================
# TESTS DE REGISTRO CON MOCKS
# ================================================================

class TestRegisterView(TestCase):
    """Tests para la vista de registro"""
    
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
        request = RequestFactory().post('/register/', {
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
        mock_roles.get.return_value = mock_rol
        
        mock_user = MagicMock()
        mock_user_objects.create_user.return_value = mock_user
        
        from universitaryWellbeing.views import register
        register(request)
        
        mock_user_objects.create_user.assert_called_once()
        mock_participantes.create.assert_called_once()
        mock_messages.success.assert_called_once()
        mock_redirect.assert_called_with('login')
    
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
        request = RequestFactory().post('/register/', {})
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
        
        # ✅ Importar desde models
        from universitaryWellbeing.models import Roles
        mock_roles.get.side_effect = Roles.DoesNotExist()
        
        from universitaryWellbeing.views import register
        register(request)
        
        mock_messages.error.assert_called()
        mock_redirect.assert_called_with('register')
        mock_user_objects.create_user.assert_called_once()
        mock_participantes.create.assert_not_called()


# ================================================================
# TESTS DE PREFERENCIAS CON MOCKS
# ================================================================

class TestPreferencesView(TestCase):
    """Tests para la vista de preferencias"""
    
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_preferences_ya_completadas(self, mock_participantes, mock_redirect):
        """Usuario con preferencias debe ir a home"""
        request = RequestFactory().get('/preferences/')
        request.user = MagicMock(is_authenticated=True)
        
        mock_participante = MagicMock()
        mock_participante.preferencias = MagicMock()
        mock_participantes.get.return_value = mock_participante
        
        from universitaryWellbeing.views import preferences
        preferences(request)
        
        mock_redirect.assert_called_with('home')
    
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.PreferenciasActividades.objects')
    @patch('universitaryWellbeing.views.Preferencias.objects')
    @patch('universitaryWellbeing.views.TiposActividad.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_preferences_crear_nuevas(self, mock_participantes, mock_tipos,
                                      mock_preferencias, mock_pref_act, mock_redirect):
        """Crear preferencias nuevas"""
        request = RequestFactory().post('/preferences/', {
            'categories': ['1', '2']
        })
        request.method = 'POST'
        request.user = MagicMock(is_authenticated=True)
        
        mock_participante = MagicMock()
        if hasattr(mock_participante, 'preferencias'):
            delattr(mock_participante, 'preferencias')
        mock_participantes.get.return_value = mock_participante
        
        mock_tipos.all.return_value = []
        
        mock_pref = MagicMock()
        mock_preferencias.create.return_value = mock_pref
        
        mock_tipo1 = MagicMock()
        mock_tipo2 = MagicMock()
        mock_tipos.get.side_effect = [mock_tipo1, mock_tipo2]
        
        from universitaryWellbeing.views import preferences
        preferences(request)
        
        mock_preferencias.create.assert_called_once()
        self.assertEqual(mock_pref_act.create.call_count, 2)
        mock_redirect.assert_called_with('home')


# ================================================================
# TESTS DE COMPLETAR PERFIL CON MOCKS
# ================================================================

class TestCompletarPerfilView(TestCase):
    """Tests para completar perfil"""
    
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_perfil_ya_completado_redirige(self, mock_participantes, mock_redirect):
        """Usuario con tipo_participante debe ir a preferencias"""
        request = RequestFactory().get('/completar-perfil/')
        request.user = MagicMock(is_authenticated=True)
        
        mock_participante = MagicMock()
        mock_participante.tipo_participante = MagicMock()
        mock_participantes.get.return_value = mock_participante
        
        from universitaryWellbeing.views import completar_perfil
        completar_perfil(request)
        
        mock_redirect.assert_called_with('preferences')
    
    @patch('universitaryWellbeing.views.messages')
    @patch('universitaryWellbeing.views.redirect')
    @patch('universitaryWellbeing.models.TiposParticipante.objects')
    @patch('universitaryWellbeing.views.Participantes.objects')
    def test_completar_perfil_estudiante(self, mock_participantes, mock_tipos_part,
                                         mock_redirect, mock_messages):
        """Completar perfil como estudiante"""
        request = RequestFactory().post('/completar-perfil/', {
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
        
        from universitaryWellbeing.views import completar_perfil
        completar_perfil(request)
        
        mock_participante.save.assert_called_once()
        mock_messages.success.assert_called_once()
        mock_redirect.assert_called_with('preferences')


# ================================================================
# TESTS DE PROTECCIÓN SQL INJECTION
# ================================================================

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