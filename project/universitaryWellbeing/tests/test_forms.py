from django.test import TestCase
from universitaryWellbeing.forms import UserLoginForm, UserRegisterForm
from django.contrib.auth.models import User


# ============================================
#   TESTS DEL FORMULARIO DE LOGIN
# ============================================
class TestUserLoginForm(TestCase):

    def test_form_valido(self):
        """
        Verifica que el formulario sea válido cuando se proporciona una cédula
        y contraseña correctas. El formulario debe autenticar exitosamente al usuario.
        """
        User.objects.create_user(username='123', password='test123')

        form = UserLoginForm(data={
            'cedula': '123',
            'password': 'test123'
        })

        self.assertTrue(form.is_valid())
        self.assertTrue(hasattr(form, 'user'))

    def test_form_password_incorrecto(self):
        """
        Verifica que el formulario sea inválido cuando la contraseña es incorrecta.
        Debe generarse un error general de validación indicando que la contraseña
        no coincide con la del usuario.
        """
        User.objects.create_user(username='123', password='test123')

        form = UserLoginForm(data={
            'cedula': '123',
            'password': 'wrong'
        })

        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)  # se lanza desde clean()

    def test_cedula_no_numerica(self):
        """
        Verifica que el formulario rechace cédulas que no sean numéricas.
        """
        form = UserLoginForm(data={
            'cedula': 'ABC123',
            'password': 'pass'
        })

        self.assertFalse(form.is_valid())
        self.assertIn('cedula', form.errors)

    def test_cedula_no_existente(self):
        """
        Verifica que el formulario rechace cédulas que no correspondan
        a un usuario existente en la base de datos.
        """
        form = UserLoginForm(data={
            'cedula': '999',
            'password': 'pass'
        })

        self.assertFalse(form.is_valid())
        self.assertIn('cedula', form.errors)


# ============================================
#   TESTS DEL FORMULARIO DE REGISTRO
# ============================================
class TestUserRegisterForm(TestCase):

    def test_email_duplicado(self):
        """
        Verifica que no se permita registrar un usuario con un correo electrónico
        que ya exista en la base de datos.
        """
        User.objects.create_user(username='111', email='test@uni.edu', password='pass')

        form = UserRegisterForm(data={
            'cedula': '222',
            'nombre_completo': 'Test User',
            'email': 'test@uni.edu',
            'password': 'newpass123'
        })

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_cedula_duplicada(self):
        """
        Verifica que el formulario no permita registrar una cédula ya existente.
        """
        User.objects.create_user(username='123', email='otro@uni.edu', password='pass')

        form = UserRegisterForm(data={
            'cedula': '123',
            'nombre_completo': 'Nuevo Usuario',
            'email': 'new@uni.edu',
            'password': 'pass123'
        })

        self.assertFalse(form.is_valid())
        self.assertIn('cedula', form.errors)

    def test_nombre_con_numeros(self):
        """
        Verifica que el formulario rechace nombres completos que contengan números.
        """
        form = UserRegisterForm(data={
            'cedula': '456',
            'nombre_completo': 'Juan 123',
            'email': 'juan@uni.edu',
            'password': 'pass123'
        })

        self.assertFalse(form.is_valid())
        self.assertIn('nombre_completo', form.errors)

    def test_form_registro_valido(self):
        """
        Verifica que el formulario sea válido cuando todos los datos son correctos.
        """
        form = UserRegisterForm(data={
            'cedula': '789',
            'nombre_completo': 'Juan Perez',
            'email': 'juanp@uni.edu',
            'password': 'pass123'
        })

        self.assertTrue(form.is_valid())
