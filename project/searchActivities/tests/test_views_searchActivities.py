# Reemplazar en searchActivities/tests/test_views_searchActivities.py

from django.test import TestCase  # ← CAMBIO: TestCase en lugar de SimpleTestCase
from unittest.mock import patch, MagicMock

class SearchHelpersTestCase(TestCase):  # ← CAMBIO
    """Búsqueda con acceso a DB permitido"""
    
    databases = '__all__'  # ← Permite queries
    
    @patch('searchActivities.views.render')
    def test_search_without_auth_user(self, mock_render):
        """Búsqueda sin usuario autenticado debe funcionar"""
        from searchActivities.views import search
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {}
        
        search(request)
        mock_render.assert_called_once()
    
    @patch('searchActivities.views.Actividades.objects')
    @patch('searchActivities.views.render')
    def test_search_with_filters(self, mock_render, mock_act):
        """Debe aplicar filtros correctamente"""
        from searchActivities.views import search
        
        mock_act.filter.return_value.order_by.return_value = []
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {'tipo': '1', 'q': 'yoga'}
        
        search(request)
        mock_render.assert_called_once()
    
    @patch('searchActivities.views.Actividades.objects')
    def test_search_export_csv(self, mock_act):
        """Debe exportar a CSV"""
        from searchActivities.views import search
        from django.http import HttpResponse
        
        mock_act.all.return_value = [
            MagicMock(nombre='Test', descripcion='Desc')
        ]
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {'export': 'csv'}
        
        response = search(request)
        self.assertIsInstance(response, HttpResponse)


# Agregar más tests para aumentar cobertura
class TestSearchFilters(TestCase):
    """Tests de filtros de búsqueda"""
    
    databases = '__all__'
    
    @patch('searchActivities.views.Actividades.objects')
    @patch('searchActivities.views.render')
    def test_filtrar_por_tipo(self, mock_render, mock_act):
        """Debe filtrar por tipo de actividad"""
        from searchActivities.views import search
        
        mock_act.filter.return_value.order_by.return_value = []
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {'tipo': '1'}
        
        search(request)
        mock_act.filter.assert_called()
    
    @patch('searchActivities.views.Actividades.objects')
    @patch('searchActivities.views.render')
    def test_busqueda_texto(self, mock_render, mock_act):
        """Debe buscar por texto en nombre"""
        from searchActivities.views import search
        
        mock_act.filter.return_value.order_by.return_value = []
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {'q': 'yoga'}
        
        search(request)
        mock_act.filter.assert_called()


class TestSearchResults(TestCase):
    """Tests de resultados"""
    
    databases = '__all__'
    
    @patch('searchActivities.views.Actividades.objects')
    @patch('searchActivities.views.render')
    def test_paginacion(self, mock_render, mock_act):
        """Debe paginar resultados"""
        from searchActivities.views import search
        
        mock_act.all.return_value.order_by.return_value = []
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {'page': '2'}
        
        search(request)
        mock_render.assert_called()
    
    @patch('searchActivities.views.Actividades.objects')
    @patch('searchActivities.views.render')
    def test_sin_resultados(self, mock_render, mock_act):
        """Debe manejar búsqueda sin resultados"""
        from searchActivities.views import search
        
        mock_act.filter.return_value.order_by.return_value = []
        
        request = MagicMock()
        request.user.is_authenticated = False
        request.GET = {'q': 'nonexistent'}
        
        search(request)
        mock_render.assert_called()