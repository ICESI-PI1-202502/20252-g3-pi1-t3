from unittest.mock import MagicMock, patch, Mock
from django.test import SimpleTestCase, RequestFactory
from django.http import Http404
from management_CADI.views import manage_news, news_detail, edit_news, delete_news

class TestNewsViewsMocked(SimpleTestCase):
    """Tests de vistas completamente mockeadas sin tocar la BD"""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = Mock(is_authenticated=True)

        # Fake noticia para usar en varios tests
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
        """Debe borrar la noticia sin tocar BD ni context processors"""

    # Fake noticia
        fake = self.fake_noticia
        mock_get.return_value = fake

    # Fake redirect result
        mock_redirect.return_value = Mock()

    # Evitar que el context processor acceda a la BD real
        mock_notif.objects.filter.return_value = []

    # request POST
        request = self.factory.post("/")
        request.user = Mock(id=1)

        response = delete_news(request, id=10)

    # Comprobar que borró
        fake.delete.assert_called_once()

    # Comprobar que redireccionó
        self.assertEqual(response, mock_redirect.return_value)

    # -------------------------------------------------------------
    # Caso 1 — No existe la noticia → get_object_or_404 lanza 404
    # -------------------------------------------------------------
    @patch("management_CADI.views.get_object_or_404")
    def test_delete_news_not_exists(self, mock_get):
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
        request = self.factory.post("/news/delete/10/")
        request.user = MagicMock(is_authenticated=True)

        fake_news = MagicMock()
        mock_get.return_value = fake_news

        response = delete_news(request, id=10)

        fake_news.delete.assert_called_once()
        mock_redirect.assert_called_once_with("management_cadi:gestionar_noticias")
        self.assertEqual(response, mock_redirect.return_value)
