# searchActivities/tests/test_views_searchActivities.py

from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock, Mock
from django.test import Client

# ===================================
# TESTS UNITARIOS CON MOCKS CORRECTOS
# ===================================

class SearchHelpersTestCase(TestCase):
    """Tests de búsqueda con mocks apropiados"""
    
    databases = '__all__'
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.render')
    def test_search_without_auth_user(
        self, mock_render, mock_act, mock_tipos, mock_bloques, mock_horarios, mock_calif
    ):
        """Búsqueda sin usuario autenticado debe funcionar"""
        from searchActivities.views import search
        
        # Mock QuerySet encadenado correctamente
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.values.return_value = []
        
        mock_act.objects = mock_qs
        mock_tipos.objects.annotate.return_value.values.return_value.order_by.return_value = []
        mock_bloques.objects.filter.return_value.values.return_value = []
        mock_horarios.objects.filter.return_value.values.return_value = []
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 0}
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {}
        
        search(request)
        mock_render.assert_called_once()
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.render')
    def test_search_with_filters(
        self, mock_render, mock_act, mock_tipos, mock_bloques, mock_horarios, mock_calif
    ):
        """Debe aplicar filtros correctamente"""
        from searchActivities.views import search
        
        # Mock QuerySet
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.values.return_value = []
        
        mock_act.objects = mock_qs
        mock_tipos.objects.annotate.return_value.values.return_value.order_by.return_value = []
        mock_bloques.objects.filter.return_value.values.return_value = []
        mock_horarios.objects.filter.return_value.values.return_value = []
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 0}
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {'tipo': '1', 'q': 'yoga'}
        
        search(request)
        
        # Verificar que se llamó filter (por el tipo y búsqueda)
        self.assertTrue(mock_qs.filter.called)
        mock_render.assert_called_once()


class TestSearchFilters(TestCase):
    """Tests de filtros de búsqueda"""
    
    databases = '__all__'
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.render')
    def test_filtrar_por_tipo(
        self, mock_render, mock_act, mock_tipos, mock_bloques, mock_horarios, mock_calif
    ):
        """Debe filtrar por tipo de actividad"""
        from searchActivities.views import search
        
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.values.return_value = []
        
        mock_act.objects = mock_qs
        mock_tipos.objects.annotate.return_value.values.return_value.order_by.return_value = []
        mock_bloques.objects.filter.return_value.values.return_value = []
        mock_horarios.objects.filter.return_value.values.return_value = []
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 0}
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {'tipo': '1'}
        
        search(request)
        
        # Verificar que se llamó filter para el tipo
        mock_qs.filter.assert_called()
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.render')
    def test_busqueda_texto(
        self, mock_render, mock_act, mock_tipos, mock_bloques, mock_horarios, mock_calif
    ):
        """Debe buscar por texto en nombre"""
        from searchActivities.views import search
        
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.values.return_value = []
        
        mock_act.objects = mock_qs
        mock_tipos.objects.annotate.return_value.values.return_value.order_by.return_value = []
        mock_bloques.objects.filter.return_value.values.return_value = []
        mock_horarios.objects.filter.return_value.values.return_value = []
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 0}
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {'q': 'yoga'}
        
        search(request)
        
        # Verificar que se usaron anotaciones y filtros
        self.assertTrue(mock_qs.annotate.called)
        self.assertTrue(mock_qs.filter.called)


class TestSearchResults(TestCase):
    """Tests de resultados"""
    
    databases = '__all__'
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.render')
    def test_sin_resultados(
        self, mock_render, mock_act, mock_tipos, mock_bloques, mock_horarios, mock_calif
    ):
        """Debe manejar búsqueda sin resultados"""
        from searchActivities.views import search
        
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.values.return_value = []  # Sin resultados
        
        mock_act.objects = mock_qs
        mock_tipos.objects.annotate.return_value.values.return_value.order_by.return_value = []
        mock_bloques.objects.filter.return_value.values.return_value = []
        mock_horarios.objects.filter.return_value.values.return_value = []
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 0}
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {'q': 'nonexistent'}
        
        search(request)
        
        # Verificar que se renderizó con lista vacía
        mock_render.assert_called_once()
        call_args = mock_render.call_args
        context = call_args[0][2]  # Tercer argumento es el contexto
        self.assertEqual(context['actividades'], [])


# ===================================
# TESTS ADICIONALES (Cubrir más casos)
# ===================================

class TestSearchEdgeCases(TestCase):
    """Tests de casos extremos"""
    
    databases = '__all__'
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.render')
    def test_search_with_empty_query(
        self, mock_render, mock_act, mock_tipos, mock_bloques, mock_horarios, mock_calif
    ):
        """Búsqueda vacía debe retornar todas las actividades"""
        from searchActivities.views import search
        
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.values.return_value = []
        
        mock_act.objects = mock_qs
        mock_tipos.objects.annotate.return_value.values.return_value.order_by.return_value = []
        mock_bloques.objects.filter.return_value.values.return_value = []
        mock_horarios.objects.filter.return_value.values.return_value = []
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 0}
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {'q': ''}
        
        search(request)
        
        # Sin query, debe listar todo
        mock_qs.all.assert_called()
        mock_render.assert_called_once()
    
    @patch('searchActivities.views.CalificacionesActividad')
    @patch('searchActivities.views.HorariosActividad')
    @patch('searchActivities.views.HorariosBloque')
    @patch('searchActivities.views.TiposActividad')
    @patch('searchActivities.views.Actividades')
    @patch('searchActivities.views.render')
    def test_search_with_invalid_tipo(
        self, mock_render, mock_act, mock_tipos, mock_bloques, mock_horarios, mock_calif
    ):
        """Tipo inválido debe ser ignorado"""
        from searchActivities.views import search
        
        mock_qs = MagicMock()
        mock_qs.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.values.return_value = []
        
        mock_act.objects = mock_qs
        mock_tipos.objects.annotate.return_value.values.return_value.order_by.return_value = []
        mock_bloques.objects.filter.return_value.values.return_value = []
        mock_horarios.objects.filter.return_value.values.return_value = []
        mock_calif.objects.filter.return_value.aggregate.return_value = {'estrellas__avg': 0}
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {'tipo': 'invalid'}  # Tipo inválido
        
        search(request)
        
        # Debe renderizar sin errores
        mock_render.assert_called_once()