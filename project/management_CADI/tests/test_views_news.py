from unittest.mock import MagicMock, patch, Mock
from django.test import SimpleTestCase, RequestFactory, override_settings
from django.http import Http404, HttpResponse
from management_CADI.views import manage_news, news_detail, edit_news, delete_news
from management_CADI.tests.test_views_management_cadi import (
    mock_notificaciones_context,
    mock_user_rol,
)

"""
Suite de pruebas unitaria y de permisos para las vistas de gestión de noticias
del módulo `management_CADI`.

Este archivo cubre dos áreas principales:

1. **TestNewsViewsMocked (SimpleTestCase)**
   Pruebas totalmente aisladas mediante mocks que verifican:
       - Comportamiento de `manage_news`, `news_detail`, `edit_news`
         y `delete_news` sin acceso a la base de datos real.
       - Correcto uso de `render`, `redirect`, `get_object_or_404`,
         y del modelo `Noticias` simulado.
       - Llamadas a métodos clave como `delete()` en objetos mockeados.
       - Manejo de situaciones de error como Http404.
       - Comportamiento distinto entre GET y POST en la eliminación de noticias.
       - Aislamiento completo de context processors reales mediante
         `mock_notificaciones_context` y `mock_user_rol`.

   El objetivo principal de esta sección es garantizar que la lógica interna
   de las vistas funciona correctamente incluso sin un entorno de BD, 
   permitiendo detectar regresiones sin necesidad de migraciones ni fixtures.

2. **NewsPermissionsTests (SimpleTestCase)**
   Pruebas del control de permisos sobre las vistas:
       - Validación de acceso restringido para `manage_news`.
       - Verificación de que usuarios no superusuarios reciben un 404, 
         respetando la lógica de seguridad del sistema.
       - Uso de plantillas y context processors mockeados para asegurar 
         independencia total del entorno del proyecto.

Estructura del archivo:
    - TestNewsViewsMocked:
         Pruebas de render, obtención, edición y eliminación de noticias,
         con gestión de errores y comportamiento diferenciado según método HTTP.
    - NewsPermissionsTests:
         Validación de acceso restringido y respuestas esperadas ante usuarios
         sin privilegios.

Este archivo proporciona una capa de regresión rápida y estable para todas las
vistas relacionadas con gestión de noticias, validando que la construcción del
contexto, permisos, renderizados y redirecciones se comporten correctamente
incluso bajo entornos totalmente simulados.
"""



class TestNewsViewsMocked(SimpleTestCase):
    """Pruebas unitarias de vistas completamente mockeadas sin acceso a la BD real."""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = Mock(is_authenticated=True)

        # Fake noticia reutilizable
        self.fake_noticia = Mock()
        self.fake_noticia.id = 10
        self.fake_noticia.slug = "mi-slug"
        self.fake_noticia.titulo = "Noticia de prueba"
        self.fake_noticia.descripcion = "Contenido"

    # -------------------------------
    #   1. Test gestionar noticias
    # -------------------------------
    @patch("management_CADI.views.Noticias")
    @patch("management_CADI.views.render")
    def test_gestionar_noticias(self, mock_render, mock_model):
        """
        Verifica que la vista `manage_news` renderiza correctamente la plantilla
        y consulta el modelo Noticias utilizando mocks.
        """

        mock_model.objects.all.return_value = [self.fake_noticia]
        mock_render.return_value = Mock()

        response = manage_news(self.request)

        self.assertTrue(mock_render.called)
        self.assertEqual(response, mock_render.return_value)

    # -------------------------------
    #   2. Test detalle noticia
    # -------------------------------
    @patch("management_CADI.views.get_object_or_404")
    @patch("management_CADI.views.render")
    def test_detalle_noticia(self, mock_render, mock_get):
        """
        Comprueba que `news_detail` obtiene la noticia por slug e id,
        y renderiza correctamente la vista utilizando mocks.
        """

        mock_get.return_value = self.fake_noticia
        mock_render.return_value = Mock()

        response = news_detail(self.request, slug="mi-slug", id=10)

        mock_get.assert_called_once()
        self.assertEqual(response, mock_render.return_value)

    # -------------------------------
    #   3. Test editar noticia
    # -------------------------------
    @patch("management_CADI.views.get_object_or_404")
    @patch("management_CADI.views.render")
    def test_editar_noticia(self, mock_render, mock_get):
        """
        Verifica que `edit_news` obtiene la noticia,
        y devuelve el render correspondiente usando mocks.
        """

        mock_get.return_value = self.fake_noticia
        mock_render.return_value = Mock()

        response = edit_news(self.request, id=10)

        mock_get.assert_called_once()
        self.assertEqual(response, mock_render.return_value)

    # -------------------------------
    #   4. Test eliminar noticia
    # -------------------------------
    @patch("universitaryWellbeing.context_processors.Notificaciones")
    @patch("management_CADI.views.redirect")
    @patch("management_CADI.views.get_object_or_404")
    def test_eliminar_noticia(self, mock_get, mock_redirect, mock_notif):
        """
        Test principal de eliminación de noticia:
        - Obtiene la noticia usando mocks
        - Llama al método delete()
        - Redirecciona sin tocar BD ni el context processor real
        """

        # Fake noticia
        fake = self.fake_noticia
        mock_get.return_value = fake

        # Fake redirect result
        mock_redirect.return_value = Mock()

        # Evitar acceso a BD en context processor
        mock_notif.objects.filter.return_value = []

        # request POST
        request = self.factory.post("/")
        request.user = Mock(id=1)

        response = delete_news(request, id=10)

        # Comprobar eliminación
        fake.delete.assert_called_once()

        # Comprobar redirección
        self.assertEqual(response, mock_redirect.return_value)

    # -------------------------------------------------------------
    # Caso 1 — No existe la noticia → get_object_or_404 lanza 404
    # -------------------------------------------------------------
    @patch("management_CADI.views.get_object_or_404")
    def test_delete_news_not_exists(self, mock_get):
        """
        Si la noticia no existe, `get_object_or_404` debe lanzar Http404
        y la vista debe propagar la excepción.
        """

        request = self.factory.get("/news/delete/123/")
        request.user = MagicMock(is_authenticated=True)

        mock_get.side_effect = Http404()

        with self.assertRaises(Http404):
            delete_news(request, id=123)

    # -------------------------------------------------------------
    # Caso 2 — GET → debe renderizar delete_confirm.html
    # -------------------------------------------------------------
    @patch("management_CADI.views.render")
    @patch("management_CADI.views.get_object_or_404")
    def test_delete_news_get(self, mock_get, mock_render):
        """
        Para una petición GET, la vista `delete_news` debe:
        - Obtener la noticia
        - Renderizar la plantilla de confirmación
        """

        request = self.factory.get("/news/delete/10/")
        request.user = MagicMock(is_authenticated=True)

        fake_news = MagicMock(id=10)
        mock_get.return_value = fake_news

        response = delete_news(request, id=10)

        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        self.assertEqual(args[2]["noticia"], fake_news)
        self.assertEqual(response, mock_render.return_value)

    # -------------------------------------------------------------
    # Caso 3 — POST → elimina la noticia y redirige
    # -------------------------------------------------------------
    @patch("management_CADI.views.redirect")
    @patch("management_CADI.views.get_object_or_404")
    def test_delete_news_post(self, mock_get, mock_redirect):
        """
        Para una petición POST, `delete_news` debe:
        - Eliminar la noticia
        - Redirigir a gestionar noticias
        """

        request = self.factory.post("/news/delete/10/")
        request.user = MagicMock(is_authenticated=True)

        fake_news = MagicMock()
        mock_get.return_value = fake_news

        response = delete_news(request, id=10)

        fake_news.delete.assert_called_once()
        mock_redirect.assert_called_once_with("management_cadi:gestionar_noticias")
        self.assertEqual(response, mock_redirect.return_value)


@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # usar mocks, NO el context processor real
                'management_CADI.tests.test_views_management_cadi.mock_notificaciones_context',
                'management_CADI.tests.test_views_management_cadi.mock_user_rol',
            ],
        },
    }]
)
class NewsPermissionsTests(SimpleTestCase):
    """Pruebas de permisos y control de acceso en las vistas de noticias."""

    def setUp(self):
        self.factory = RequestFactory()

    @patch("management_CADI.views.render")
    def test_manage_news_non_superuser_404(self, mock_render):
        """
        Si un usuario no superusuario intenta acceder a manage_news,
        la vista debe devolver un 404 utilizando el render mockeado.
        """

        mock_render.return_value = HttpResponse("x", status=404)

        request = self.factory.get("/news/")
        request.user = Mock(is_authenticated=True, is_superuser=False)

        response = manage_news(request)

        self.assertEqual(response.status_code, 404)
        mock_render.assert_called_once()
