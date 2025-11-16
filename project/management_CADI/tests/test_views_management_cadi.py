#\20252-g3-pi1-t3\project\management_CADI\tests\test_views_management_cadi.py

import datetime as dt
from django.test import SimpleTestCase, TestCase, Client, TransactionTestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock, Mock


# CORRECCIÓN: Importa desde management_CADI.tests.models, NO desde .models
from management_CADI.tests.models import (
    Grupos,
    GruposActividad,
    TiposActividad,
    Actividades,
    ActividadesGrupos,
    HorariosBloque,
    HorariosActividad,
    Roles,
    TiposParticipante,
    Participantes,
    RolesParticipacion,
    EstadosParticipacion,
    Participaciones,
    HorariosParticipante,  # ✅ NUEVO
    CalificacionesActividad,
)

# ==========================================================
# TESTS UNITARIOS CON MOCKS (SimpleTestCase)
# ==========================================================

class HelpersTestCase(SimpleTestCase):
    """Pruebas unitarias para helpers simples"""

    def test_is_admin_true_for_staff(self):
        from management_CADI.views import is_admin
        user = MagicMock(is_authenticated=True, is_staff=True)
        self.assertTrue(is_admin(user))

    def test_is_admin_false_for_anonymous(self):
        from management_CADI.views import is_admin
        user = MagicMock(is_authenticated=False, is_staff=False)
        self.assertFalse(is_admin(user))

    def test_hhmm_to_dt_valid(self):
        from management_CADI.views import hhmm_to_dt
        result = hhmm_to_dt("15:30")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 15)
        self.assertEqual(result.minute, 30)

    def test_hhmm_to_dt_invalid(self):
        from management_CADI.views import hhmm_to_dt
        self.assertIsNone(hhmm_to_dt(""))
        self.assertIsNone(hhmm_to_dt("invalid"))

    def test_date_input_to_dt_valid(self):
        from management_CADI.views import date_input_to_dt
        result = date_input_to_dt("2025-10-13")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 10)
        self.assertEqual(result.day, 13)

    def test_date_input_to_dt_invalid(self):
        from management_CADI.views import date_input_to_dt
        self.assertIsNone(date_input_to_dt(""))
        self.assertIsNone(date_input_to_dt("invalid"))


class DraftKeysTestCase(SimpleTestCase):
    """Pruebas para generación de llaves de sesión"""

    def test_draft_keys_new_activity(self):
        from management_CADI.views import _draft_keys
        base, sched_list, sched_last = _draft_keys(123)
        self.assertEqual(base, "cadi_draft_base_123_new")
        self.assertEqual(sched_list, "cadi_sched_list_123_new")
        self.assertEqual(sched_last, "cadi_sched_last_123_new")

    def test_draft_keys_edit_activity(self):
        from management_CADI.views import _draft_keys
        base, sched_list, sched_last = _draft_keys(123, 456)
        self.assertEqual(base, "cadi_draft_base_123_456")
        self.assertEqual(sched_list, "cadi_sched_list_123_456")
        self.assertEqual(sched_last, "cadi_sched_last_123_456")


# ==========================================================
# TESTS DE VISTAS CON BASE DE DATOS (TransactionTestCase)
# ==========================================================

# Mock de los context_processors para evitar errores de BD
def mock_notificaciones_context(request):
    """Context processor mockeado que no accede a la base de datos"""
    return {
        'notificaciones_no_leidas': [],
        'notificaciones_count': 0,
    }

def mock_user_rol(request):
    """Context processor mockeado para user_rol"""
    return {
        'user_rol': None,
        'es_estudiante': False,
        'es_coordinador': False,
        'es_profesor': False,
    }

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
                # ✅ Usa los context processors mockeados
                'management_CADI.tests.test_views_management_cadi.mock_notificaciones_context',
                'management_CADI.tests.test_views_management_cadi.mock_user_rol',
            ],
        },
    }]
)
# ✅ CLAVE: Mockear universitaryWellbeing.models, NO management_CADI.views
@patch('universitaryWellbeing.models.Grupos', Grupos)
@patch('universitaryWellbeing.models.GruposActividad', GruposActividad)
class TestShowGroupActivities(TransactionTestCase):
    """Pruebas para showGroupActivities"""
    
    # Resetea secuencias para evitar conflictos de PK
    reset_sequences = True
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("alice", password="testpass")
        self.client.login(username="alice", password="testpass")
        
        self.grupo = Grupos.objects.create(nombre="CADI")
        self.ga1 = GruposActividad.objects.create(
            grupos_id_grupo=self.grupo, 
            nombre="Deportes"
        )
        self.ga2 = GruposActividad.objects.create(
            grupos_id_grupo=self.grupo, 
            nombre="Arte"
        )

    def test_slug_redirect_to_canonical(self):
        """Debe redirigir slugs incorrectos al slug canónico"""
        url = reverse("management_cadi:listar_grupos_actividad", 
                     args=["slug-incorrecto", self.grupo.id_grupo])
        resp = self.client.get(url, follow=True)
        
        self.assertEqual(resp.status_code, 200)
        # Verifica que hubo redirección
        self.assertTrue(len(resp.redirect_chain) > 0)

    def test_list_grupos_actividad_renders_correctly(self):
        """Debe listar todos los grupos de actividad del grupo"""
        url = reverse("management_cadi:listar_grupos_actividad", 
                     args=["cadi", self.grupo.id_grupo])
        resp = self.client.get(url)
        
        self.assertEqual(resp.status_code, 200)
        grupos_act = resp.context["grupos_actividad"]
        self.assertEqual(len(grupos_act), 2)


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
                # ✅ Usa los context processors mockeados
                'management_CADI.tests.test_views_management_cadi.mock_notificaciones_context',
                'management_CADI.tests.test_views_management_cadi.mock_user_rol',
            ],
        },
    }]
)
# ✅ CLAVE: Mockear universitaryWellbeing.models
@patch('universitaryWellbeing.models.Grupos', Grupos)
@patch('universitaryWellbeing.models.GruposActividad', GruposActividad)
@patch('universitaryWellbeing.models.TiposActividad', TiposActividad)
@patch('universitaryWellbeing.models.Actividades', Actividades)
@patch('universitaryWellbeing.models.ActividadesGrupos', ActividadesGrupos)
@patch('universitaryWellbeing.models.HorariosBloque', HorariosBloque)
@patch('universitaryWellbeing.models.HorariosActividad', HorariosActividad)
@patch('universitaryWellbeing.models.CalificacionesActividad', CalificacionesActividad)
@patch('universitaryWellbeing.models.Participantes', Participantes)
@patch('universitaryWellbeing.models.TiposParticipante', TiposParticipante)
@patch('universitaryWellbeing.models.RolesParticipacion', RolesParticipacion)  # ✅ NUEVO
@patch('universitaryWellbeing.models.EstadosParticipacion', EstadosParticipacion)  # ✅ NUEVO
@patch('universitaryWellbeing.models.Participaciones', Participaciones)  # ✅ NUEVO
class TestShowActivities(TransactionTestCase):
    """Pruebas para showActivities (listar_actividades)"""
    
    # Resetea secuencias para evitar conflictos de PK
    reset_sequences = True
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("alice", password="x")
        self.client.login(username="alice", password="x")
        
        # ✅ Crear tipo de participante
        self.tipo_participante = TiposParticipante.objects.create(
            nombre_tipo="Estudiante Regular"
        )
        
        rol = Roles.objects.create(nombre_rol="Estudiante")
        self.part = Participantes.objects.create(
            user=self.user, 
            roles_id_rol=rol, 
            correo="alice@ex.com",
            tipo_participante=self.tipo_participante  # ✅ Asignar tipo
        )

        self.grupo = Grupos.objects.create(nombre="CADI")
        self.ga = GruposActividad.objects.create(
            grupos_id_grupo=self.grupo, 
            nombre="Baile"
        )

        self.tipo = TiposActividad.objects.create(id_tipo=1, nombre_tipo="Danza")
        self.act = Actividades.objects.create(
            nombre="Salsa 1", 
            tipos_actividad_id_tipo=self.tipo
        )
        ActividadesGrupos.objects.create(grupos_actividad=self.ga, actividad=self.act)

        b1 = HorariosBloque.objects.create(
            actividades_id_actividad=self.act,
            hora_inicio=dt.time(8, 0), 
            hora_fin=dt.time(9, 0),
            profesor="Profe X", 
            lugar="Gimnasio"
        )
        HorariosActividad.objects.create(
            actividades_id_actividad=self.act, 
            horario_bloque=b1, 
            dia_semana=0
        )
        HorariosActividad.objects.create(
            actividades_id_actividad=self.act, 
            horario_bloque=b1, 
            dia_semana=2
        )

    def _url(self, slug="cadi"):
        return reverse("management_cadi:listar_actividades",
                      args=[slug, self.grupo.id_grupo, self.ga.id_grupo_actividad])

    def test_slug_redirect_to_canonical(self):
        """Debe redirigir slugs incorrectos al slug canónico"""
        resp = self.client.get(self._url(slug="slug-erroneo"), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any("cadi" in url for url, _ in resp.redirect_chain))

    def test_list_builds_daywise_and_zero_rating(self):
        """Debe construir items_dia correctamente y mostrar rating 0"""
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

    def test_rating_bucket_and_user_has_calificado(self):
        """Debe calcular promedio correcto y detectar si usuario calificó"""
        u2 = User.objects.create_user("bob", password="x")
        p2 = Participantes.objects.create(
            user=u2, 
            roles_id_rol=self.part.roles_id_rol, 
            correo="bob@ex.com",
            tipo_participante=self.tipo_participante  # ✅ Asignar tipo
        )
        
        CalificacionesActividad.objects.create(
            actividades_id_actividad=self.act, 
            participantes_id_participante=self.part, 
            estrellas=5
        )
        CalificacionesActividad.objects.create(
            actividades_id_actividad=self.act, 
            participantes_id_participante=p2, 
            estrellas=4
        )

        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)
        
        a = resp.context["actividades"][0]
        self.assertEqual(round(a["promedio_calificacion"], 1), 4.5)
        self.assertEqual(a["rating_image"], "rating_4_5.png")
        self.assertTrue(a["user_has_calificado"])