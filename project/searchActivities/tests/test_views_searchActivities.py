from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from datetime import time

from searchActivities.tests.models import (
    Actividades, TiposActividad,
    HorariosBloque, HorariosActividad,
    CalificacionesActividad, Participantes, Roles
)
##PORFAVOR CORRER LOS TEST CON python manage.py test searchActivites --keepdb
##PORFAVOR CORRER LOS TEST CON python manage.py test searchActivites --keepdb

class TestSearchActivitiesViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Usuario + Rol + Participante (una sola vez)
        cls.user = User.objects.create_user(username="alice", password="pass123")
        cls.rol = Roles.objects.create(nombre_rol="Estudiante")
        cls.part = Participantes.objects.create(
            correo="alice@uni.edu",
            user=cls.user,
            roles_id_rol=cls.rol,
        )

        # Tipos
        cls.tipo_dep = TiposActividad.objects.create(id_tipo=1, nombre_tipo="Deporte")
        cls.tipo_art = TiposActividad.objects.create(id_tipo=2, nombre_tipo="Arte")

        # Actividades
        cls.act1 = Actividades.objects.create(
            nombre="Yoga Avanzado", descripcion="Respiración y estiramiento",
            tipos_actividad_id_tipo=cls.tipo_dep
        )
        cls.act2 = Actividades.objects.create(
            nombre="Pintura libre", descripcion="Acrílico",
            tipos_actividad_id_tipo=cls.tipo_art
        )
        cls.act3 = Actividades.objects.create(
            nombre="Yogur casero", descripcion="Cocina",
            tipos_actividad_id_tipo=cls.tipo_art
        )

        # Bloques + días
        b1 = HorariosBloque.objects.create(
            actividades_id_actividad=cls.act1, hora_inicio=time(9, 0), hora_fin=time(10, 0),
            profesor="Ana", lugar="Gimnasio"
        )
        HorariosActividad.objects.create(
            actividades_id_actividad=cls.act1, horario_bloque=b1, dia_semana=0
        )

        b2 = HorariosBloque.objects.create(
            actividades_id_actividad=cls.act2, hora_inicio=time(14, 0), hora_fin=time(15, 0),
            profesor="Luis", lugar="Sala 2"
        )
        HorariosActividad.objects.create(
            actividades_id_actividad=cls.act2, horario_bloque=b2, dia_semana=2
        )

        # Calificación previa del mismo participante para act2
        CalificacionesActividad.objects.create(
            actividades_id_actividad=cls.act2,
            participantes_id_participante=cls.part,
            estrellas=4
        )

    def setUp(self):
        self.client.login(username="alice", password="pass123")

    def _url(self, **params):
        url = reverse("searchActivities:search")
        if params:
            from urllib.parse import urlencode
            return f"{url}?{urlencode(params)}"
        return url

    def test_search_text_builds_daywise_and_zero_rating(self):
        """Busca 'yoga' y arma items_dia; act1 tiene horario y rating 0 si el usuario no ha calificado ahí."""
        resp = self.client.get(self._url(q="yog"))
        self.assertEqual(resp.status_code, 200)
        acts = resp.context["actividades"]
        names = [a["nombre"] for a in acts]
        self.assertIn("Yoga Avanzado", names)
        # Act3 (Yogur casero) también coincide por substring pero sin horarios
        self.assertIn("Yogur casero", names)

        # Daywise para act1
        a1 = next(a for a in acts if a["nombre"] == "Yoga Avanzado")
        self.assertTrue(a1["items_dia"])
        self.assertEqual(a1["items_dia"][0]["dia"], "Lunes")
        # Como no hay calificación previa del usuario para act1, promedio 0 => imagen 0_0
        self.assertEqual(a1["promedio_calificacion"], 0)
        self.assertEqual(a1["rating_image"], "rating_0_0.png")
        self.assertIn("user_has_calificado", a1)
        self.assertFalse(a1["user_has_calificado"])

    def test_filter_by_tipo_and_only_available_and_user_has_calificado(self):
        """Filtra por tipo=Arte y only=1. act2 cumple, act3 (sin horario) queda fuera.
           Además, para act2 el usuario ya calificó (flag True) y el bucket de imagen es correcto."""
        resp = self.client.get(self._url(q="", tipo=self.tipo_art.id_tipo, only="1"))
        self.assertEqual(resp.status_code, 200)
        acts = resp.context["actividades"]
        self.assertEqual([a["nombre"] for a in acts], ["Pintura libre"])

        a2 = acts[0]
        self.assertTrue(a2["items_dia"])                # tiene horario
        self.assertTrue(a2["user_has_calificado"])      # ya había calificado
        # Promedio 4 => cae en bucket 3.5 < x <= 4 => 'rating_4_0.png'
        self.assertEqual(a2["rating_image"], "rating_4_0.png")

        # Selected tipo name presente
        self.assertEqual(resp.context["selected_tipo_name"], "Arte")

    def test_calificar_actividad_create_and_update(self):
        """Crea/actualiza calificación via POST y redirige a search."""
        url = reverse("searchActivities:calificar_actividad", args=[self.act1.id_actividad])  # ← nombre corregido
        # Crear
        resp = self.client.post(url, {"estrellas": 5, "comentario": "Top"}, follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("searchActivities:search"), resp["Location"])

        cal = CalificacionesActividad.objects.get(
            actividades_id_actividad=self.act1,
            participantes_id_participante=self.part
        )
        self.assertEqual(cal.estrellas, 5)
        self.assertEqual(cal.comentario, "Top")

        # Update
        resp2 = self.client.post(
            url + "?next=" + reverse("searchActivities:search"),
            {"estrellas": 3, "comentario": "Ok"},
            follow=False
        )
        self.assertEqual(resp2.status_code, 302)
        self.assertIn(reverse("searchActivities:search"), resp2["Location"])

        cal.refresh_from_db()
        self.assertEqual(cal.estrellas, 3)
        self.assertEqual(cal.comentario, "Ok")
