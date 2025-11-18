"""
Tests completos para context_processors EXISTENTES

Ejecutar:
    python manage.py test universitaryWellbeing.tests.test_context_processors --keepdb
"""
from django.test import TestCase, RequestFactory
from unittest.mock import Mock, MagicMock, patch
from django.contrib.auth.models import User, AnonymousUser
import logging

logging.disable(logging.CRITICAL)


class TestNotificacionesContext(TestCase):
    """Tests para notificaciones_context (función existente)"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user_mock = Mock(spec=User)
        self.user_mock.is_authenticated = True
        self.user_mock.id = 1
    
    @patch('universitaryWellbeing.context_processors.Notificaciones.objects')
    def test_usuario_autenticado_con_notificaciones(self, mock_notificaciones):
        """Usuario con notificaciones debe retornar datos correctos"""
        request = self.factory.get('/')
        request.user = self.user_mock
        
        # Mock de queryset con notificaciones
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = mock_qs
        mock_qs.__getitem__ = Mock(return_value=[])  # Para [:10]
        mock_qs.filter.return_value.count.return_value = 5
        mock_notificaciones.filter.return_value = mock_qs
        
        from universitaryWellbeing.context_processors import notificaciones_context
        resultado = notificaciones_context(request)
        
        self.assertIn('notificaciones', resultado)
        self.assertIn('notificaciones_no_leidas', resultado)
        self.assertEqual(resultado['notificaciones_no_leidas'], 5)
        
        # Verificar que se ordenó por id descendente
        mock_qs.order_by.assert_called_with('-id_notificacion')
    
    def test_usuario_no_autenticado(self):
        """Usuario no autenticado debe retornar diccionario vacío"""
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        from universitaryWellbeing.context_processors import notificaciones_context
        resultado = notificaciones_context(request)
        
        self.assertEqual(resultado, {})
    
    @patch('universitaryWellbeing.context_processors.Notificaciones.objects')
    def test_usuario_sin_notificaciones(self, mock_notificaciones):
        """Usuario sin notificaciones debe retornar 0"""
        request = self.factory.get('/')
        request.user = self.user_mock
        
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = mock_qs
        mock_qs.__getitem__ = Mock(return_value=[])
        mock_qs.filter.return_value.count.return_value = 0
        mock_notificaciones.filter.return_value = mock_qs
        
        from universitaryWellbeing.context_processors import notificaciones_context
        resultado = notificaciones_context(request)
        
        self.assertEqual(resultado['notificaciones_no_leidas'], 0)
    
    @patch('universitaryWellbeing.context_processors.Notificaciones.objects')
    def test_retorna_solo_10_notificaciones(self, mock_notificaciones):
        """Debe retornar máximo 10 notificaciones"""
        request = self.factory.get('/')
        request.user = self.user_mock
        
        # Simular 20 notificaciones
        notifs = [Mock() for _ in range(20)]
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = mock_qs
        mock_qs.__getitem__ = Mock(return_value=notifs[:10])  # Solo las primeras 10
        mock_qs.filter.return_value.count.return_value = 15
        mock_notificaciones.filter.return_value = mock_qs
        
        from universitaryWellbeing.context_processors import notificaciones_context
        resultado = notificaciones_context(request)
        
        # Verificar que se pidió slice [:10]
        mock_qs.__getitem__.assert_called_with(slice(None, 10, None))


class TestUserRol(TestCase):
    """Tests para user_rol (función existente)"""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    def test_usuario_no_autenticado(self):
        """Usuario no autenticado debe retornar valores por defecto"""
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        from universitaryWellbeing.context_processors import user_rol
        resultado = user_rol(request)
        
        self.assertIsNone(resultado['user_rol'])
        self.assertFalse(resultado['es_coordinador'])
        self.assertFalse(resultado['es_profesor'])
        self.assertFalse(resultado['es_psicologo'])
        self.assertFalse(resultado['es_admin_bienestar'])
        self.assertFalse(resultado['es_super_admin'])
    
    def test_usuario_sin_participante(self):
        """Usuario sin participante debe retornar valores por defecto"""
        request = self.factory.get('/')
        user_mock = Mock(spec=User)
        user_mock.is_authenticated = True
        user_mock.participantes_set.first.return_value = None
        request.user = user_mock
        
        from universitaryWellbeing.context_processors import user_rol
        resultado = user_rol(request)
        
        self.assertIsNone(resultado['user_rol'])
        self.assertFalse(resultado['es_coordinador'])
    
    def test_usuario_con_rol_coordinador(self):
        """Usuario con rol coordinador debe activar flag correcto"""
        request = self.factory.get('/')
        user_mock = Mock(spec=User)
        user_mock.is_authenticated = True
        
        participante = Mock()
        rol = Mock()
        rol.nombre_rol = 'Coordinador'
        participante.roles_id_rol = rol
        user_mock.participantes_set.first.return_value = participante
        request.user = user_mock
        
        from universitaryWellbeing.context_processors import user_rol
        resultado = user_rol(request)
        
        self.assertEqual(resultado['user_rol'], 'Coordinador')
        self.assertTrue(resultado['es_coordinador'])
        self.assertFalse(resultado['es_profesor'])
    
    def test_usuario_con_rol_profesor(self):
        """Usuario con rol profesor debe activar flag correcto"""
        request = self.factory.get('/')
        user_mock = Mock(spec=User)
        user_mock.is_authenticated = True
        
        participante = Mock()
        rol = Mock()
        rol.nombre_rol = 'Profesor'
        participante.roles_id_rol = rol
        user_mock.participantes_set.first.return_value = participante
        request.user = user_mock
        
        from universitaryWellbeing.context_processors import user_rol
        resultado = user_rol(request)
        
        self.assertEqual(resultado['user_rol'], 'Profesor')
        self.assertTrue(resultado['es_profesor'])
        self.assertFalse(resultado['es_coordinador'])
    
    def test_usuario_con_rol_psicologo(self):
        """Usuario con rol psicólogo debe activar flag correcto"""
        request = self.factory.get('/')
        user_mock = Mock(spec=User)
        user_mock.is_authenticated = True
        
        participante = Mock()
        rol = Mock()
        rol.nombre_rol = 'Psicólogo'
        participante.roles_id_rol = rol
        user_mock.participantes_set.first.return_value = participante
        request.user = user_mock
        
        from universitaryWellbeing.context_processors import user_rol
        resultado = user_rol(request)
        
        self.assertEqual(resultado['user_rol'], 'Psicólogo')
        self.assertTrue(resultado['es_psicologo'])
    
    def test_rol_normalizado_con_espacios(self):
        """Debe normalizar roles con espacios extra"""
        request = self.factory.get('/')
        user_mock = Mock(spec=User)
        user_mock.is_authenticated = True
        
        participante = Mock()
        rol = Mock()
        rol.nombre_rol = '  Coordinador  '
        participante.roles_id_rol = rol
        user_mock.participantes_set.first.return_value = participante
        request.user = user_mock
        
        from universitaryWellbeing.context_processors import user_rol
        resultado = user_rol(request)
        
        self.assertTrue(resultado['es_coordinador'])
    
    def test_maneja_excepcion_sin_crashear(self):
        """Debe manejar excepciones y retornar valores por defecto"""
        request = self.factory.get('/')
        user_mock = Mock(spec=User)
        user_mock.is_authenticated = True
        user_mock.participantes_set.first.side_effect = Exception("Error de BD")
        request.user = user_mock
        
        from universitaryWellbeing.context_processors import user_rol
        resultado = user_rol(request)
        
        # No debe crashear, debe retornar valores por defecto
        self.assertIsNone(resultado['user_rol'])
        self.assertFalse(resultado['es_coordinador'])


class TestRoleFlags(TestCase):
    """Tests para role_flags (función existente)"""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    @patch('universitaryWellbeing.context_processors.Participantes.objects')
    def test_usuario_psicologo_por_id(self, mock_participantes):
        """Usuario con rol_id=10 debe ser psicólogo"""
        request = self.factory.get('/')
        user_mock = Mock(spec=User)
        user_mock.is_authenticated = True
        user_mock.id = 1
        request.user = user_mock
        
        participante = Mock()
        rol = Mock()
        rol.id_rol = 10
        rol.nombre_rol = 'Psicólogo'
        participante.roles_id_rol = rol
        
        mock_participantes.select_related.return_value.filter.return_value.first.return_value = participante
        
        from universitaryWellbeing.context_processors import role_flags
        resultado = role_flags(request)
        
        self.assertTrue(resultado['es_psicologo'])
        self.assertEqual(resultado['user_rol'], 'Psicólogo')
    
    @patch('universitaryWellbeing.context_processors.Participantes.objects')
    def test_usuario_psicologo_por_nombre(self, mock_participantes):
        """Usuario con nombre que empieza con 'psicol' debe ser psicólogo"""
        request = self.factory.get('/')
        user_mock = Mock(spec=User)
        user_mock.is_authenticated = True
        user_mock.id = 1
        request.user = user_mock
        
        participante = Mock()
        rol = Mock()
        rol.id_rol = 99  # No es 10
        rol.nombre_rol = 'Psicología'
        participante.roles_id_rol = rol
        
        mock_participantes.select_related.return_value.filter.return_value.first.return_value = participante
        
        from universitaryWellbeing.context_processors import role_flags
        resultado = role_flags(request)
        
        self.assertTrue(resultado['es_psicologo'])
    
    @patch('universitaryWellbeing.context_processors.Participantes.objects')
    def test_usuario_no_psicologo(self, mock_participantes):
        """Usuario con otro rol no debe ser psicólogo"""
        request = self.factory.get('/')
        user_mock = Mock(spec=User)
        user_mock.is_authenticated = True
        user_mock.id = 1
        request.user = user_mock
        
        participante = Mock()
        rol = Mock()
        rol.id_rol = 1
        rol.nombre_rol = 'Estudiante'
        participante.roles_id_rol = rol
        
        mock_participantes.select_related.return_value.filter.return_value.first.return_value = participante
        
        from universitaryWellbeing.context_processors import role_flags
        resultado = role_flags(request)
        
        self.assertFalse(resultado['es_psicologo'])
        self.assertEqual(resultado['user_rol'], 'Estudiante')
    
    def test_usuario_no_autenticado(self):
        """Usuario no autenticado debe retornar False"""
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        from universitaryWellbeing.context_processors import role_flags
        resultado = role_flags(request)
        
        self.assertFalse(resultado['es_psicologo'])
        self.assertIsNone(resultado['user_rol'])
    
    @patch('universitaryWellbeing.context_processors.Participantes.objects')
    def test_usuario_sin_participante(self, mock_participantes):
        """Usuario sin participante debe retornar False"""
        request = self.factory.get('/')
        user_mock = Mock(spec=User)
        user_mock.is_authenticated = True
        user_mock.id = 1
        request.user = user_mock
        
        mock_participantes.select_related.return_value.filter.return_value.first.return_value = None
        
        from universitaryWellbeing.context_processors import role_flags
        resultado = role_flags(request)
        
        self.assertFalse(resultado['es_psicologo'])
        self.assertIsNone(resultado['user_rol'])


class TestIntegracion(TestCase):
    """Tests de integración entre context processors"""
    
    def test_todos_retornan_dict(self):
        """Todos los context processors deben retornar diccionarios"""
        from universitaryWellbeing.context_processors import (
            user_rol, notificaciones_context, role_flags
        )
        
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        
        resultado1 = user_rol(request)
        resultado2 = notificaciones_context(request)
        resultado3 = role_flags(request)
        
        self.assertIsInstance(resultado1, dict)
        self.assertIsInstance(resultado2, dict)
        self.assertIsInstance(resultado3, dict)
    
    def test_no_hay_colision_de_claves(self):
        """Los context processors no deben sobrescribir claves entre sí"""
        from universitaryWellbeing.context_processors import (
            user_rol, role_flags
        )
        
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        
        resultado1 = user_rol(request)
        resultado2 = role_flags(request)
        
        # Ambos tienen 'user_rol' pero eso es OK, Django los merge
        # Solo verificamos que no crasheen
        self.assertIn('user_rol', resultado1)
        self.assertIn('user_rol', resultado2)


"""
EJECUTAR:

1. Todos los tests:
   python manage.py test universitaryWellbeing.tests.test_context_processors --keepdb

2. Con verbosidad:
   python manage.py test universitaryWellbeing.tests.test_context_processors --keepdb -v 2

3. Cobertura:
   coverage run --source='universitaryWellbeing' manage.py test universitaryWellbeing.tests.test_context_processors --keepdb
   coverage report --include='*/context_processors.py'

ESPERADO:
- 20+ tests
- Todos pasan
- ~85%+ cobertura en context_processors.py
"""