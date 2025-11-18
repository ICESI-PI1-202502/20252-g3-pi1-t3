# ✅ NUEVO: tests/test_context_processors.py
from django.test import TestCase, RequestFactory
from unittest.mock import patch, MagicMock
from universitaryWellbeing.context_processors import notificaciones_no_leidas

class TestContextProcessors(TestCase):
    @patch('universitaryWellbeing.context_processors.Notificaciones.objects')
    @patch('universitaryWellbeing.context_processors.Participantes.objects')
    def test_notificaciones_no_leidas(self, mock_participantes, mock_notificaciones):
        """Context processor cuenta notificaciones correctamente"""
        request = RequestFactory().get('/')
        request.user = MagicMock(is_authenticated=True)
        
        mock_participante = MagicMock()
        mock_participantes.get.return_value = mock_participante
        
        mock_notificaciones.filter.return_value.filter.return_value.count.return_value = 5
        
        resultado = notificaciones_no_leidas(request)
        
        self.assertEqual(resultado['notificaciones_no_leidas'], 5)