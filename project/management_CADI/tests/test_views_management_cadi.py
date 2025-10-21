import datetime as dt
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.test.utils import override_settings

from management_CADI.tests.models import (
    Grupos, GruposActividad,
    TiposActividad, Actividades, ActividadesGrupos,
    HorariosBloque, HorariosActividad,
    CalificacionesActividad, Participantes, Roles,
)
##PORFAVOR CORRER LOS TEST CON python manage.py test management_CADI --keepdb
@override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
class TestListarActividades(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("alice", password="x")
        self.client.login(username="alice", password="x")
        rol = Roles.objects.create(nombre_rol="Estudiante")
        self.part = Participantes.objects.create(user=self.user, roles_id_rol=rol, correo="alice@ex.com")

        self.grupo = Grupos.objects.create(nombre="CADI")
        self.ga = GruposActividad.objects.create(grupos_id_grupo=self.grupo, nombre="Baile")

        self.tipo = TiposActividad.objects.create(id_tipo=1, nombre_tipo="Danza")
        self.act = Actividades.objects.create(nombre="Salsa 1", tipos_actividad_id_tipo=self.tipo)
        ActividadesGrupos.objects.create(grupos_actividad=self.ga, actividad=self.act)

        b1 = HorariosBloque.objects.create(
            actividades_id_actividad=self.act,
            hora_inicio=dt.time(8, 0), hora_fin=dt.time(9, 0),
            profesor="Profe X", lugar="Gimnasio"
        )
        HorariosActividad.objects.create(actividades_id_actividad=self.act, horario_bloque=b1, dia_semana=0)
        HorariosActividad.objects.create(actividades_id_actividad=self.act, horario_bloque=b1, dia_semana=2)

    def _url(self, slug="cadi"):
        return reverse("management_cadi:listar_actividades",
                       args=[slug, self.grupo.id_grupo, self.ga.id_grupo_actividad])
    

      # Verifica que si el slug es incorrecto, la vista redirige al slug canónico "cadi".
    def test_slug_redirect_to_canonical(self):
        resp = self.client.get(self._url(slug="slug-erroneo"), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any("cadi" in url for url, _ in resp.redirect_chain))

     # Construye la lista agrupada por día y, sin calificaciones, muestra promedio=0 y la imagen rating_0_0.
    def test_list_builds_daywise_and_zero_rating(self):
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)
        acts = resp.context["actividades"]
        self.assertEqual(len(acts), 1)
        a = acts[0]

        dias = [i["dia"] for i in a["items_dia"]]
        self.assertIn("Lunes", dias)
        self.assertIn("Miércoles", dias)
        for item in a["items_dia"]:
            self.assertIn("08:00–09:00", item["horario"])
            self.assertEqual(item["espacio"], "Gimnasio")
            self.assertEqual(item["profesor"], "Profe X")

        self.assertEqual(a["promedio_calificacion"], 0)
        self.assertEqual(a["rating_image"], "rating_0_0.png")
        self.assertFalse(a["user_has_calificado"])

     # Calcula correctamente el promedio (4.5), el bucket de imagen (rating_4_5) y detecta si el usuario ya calificó.
    def test_rating_bucket_and_user_has_calificado(self):
        u2 = User.objects.create_user("bob", password="x")
        p2 = Participantes.objects.create(user=u2, roles_id_rol=self.part.roles_id_rol, correo="bob@ex.com")
        CalificacionesActividad.objects.create(actividades_id_actividad=self.act, participantes_id_participante=self.part, estrellas=5)
        CalificacionesActividad.objects.create(actividades_id_actividad=self.act, participantes_id_participante=p2, estrellas=4)

        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)
        a = resp.context["actividades"][0]
        self.assertEqual(round(a["promedio_calificacion"], 1), 4.5)
        self.assertEqual(a["rating_image"], "rating_4_5.png")
        self.assertTrue(a["user_has_calificado"])
