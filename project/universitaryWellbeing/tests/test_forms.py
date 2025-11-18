# ✅ NUEVO ARCHIVO: tests/test_forms.py
from django.test import TestCase
from universitaryWellbeing.forms import UserLoginForm, UserRegisterForm
from django.contrib.auth.models import User

class TestUserLoginForm(TestCase):
    def test_form_valido(self):
        """Form válido con credenciales correctas"""
        user = User.objects.create_user(username='test', password='test123')
        form = UserLoginForm(data={
            'username': 'test',
            'password': 'test123'
        })
        self.assertTrue(form.is_valid())
    
    def test_form_password_incorrecto(self):
        """Form inválido con contraseña incorrecta"""
        User.objects.create_user(username='test', password='test123')
        form = UserLoginForm(data={
            'username': 'test',
            'password': 'wrong'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

class TestUserRegisterForm(TestCase):
    def test_email_duplicado(self):
        """No permitir emails duplicados"""
        User.objects.create_user(username='111', email='test@uni.edu', password='pass')
        form = UserRegisterForm(data={
            'cedula': '222',
            'nombre_completo': 'Test User',
            'email': 'test@uni.edu',  # ← Email duplicado
            'password': 'newpass123'
        })
        self.assertFalse(form.is_valid())