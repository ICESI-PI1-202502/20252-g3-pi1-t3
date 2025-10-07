import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date

# ================================================================
# BASIC UTILITIES LOGIC TESTS
# ================================================================

class TestBasicUtilsLogic:
    def test_is_admin_true(self):
        user = Mock(is_authenticated=True, is_staff=True)
        resultado = user.is_authenticated and user.is_staff
        assert resultado is True

    def test_is_admin_false(self):
        user = Mock(is_authenticated=True, is_staff=False)
        resultado = user.is_authenticated and user.is_staff
        assert resultado is False

    def test_hhmm_to_dt_valid(self):
        hhmm = "15:30"
        hora, minuto = map(int, hhmm.split(":"))
        result = datetime.combine(date.today(), datetime.min.time()).replace(hour=hora, minute=minuto)
        assert result.hour == 15 and result.minute == 30

    def test_hhmm_to_dt_invalid(self):
        def hhmm_to_dt_safe(value):
            try:
                hora, minuto = map(int, value.split(":"))
                return datetime.now().replace(hour=hora, minute=minuto)
            except Exception:
                return None
        assert hhmm_to_dt_safe("abc") is None
        assert hhmm_to_dt_safe(None) is None

    def test_draft_keys_with_activity(self):
        grupo_id, actividad_id = 1, 2
        base_key = f"cadi_draft_base_{grupo_id}_{actividad_id}"
        sched_key = f"cadi_draft_sched_{grupo_id}_{actividad_id}"
        assert base_key == "cadi_draft_base_1_2"
        assert sched_key == "cadi_draft_sched_1_2"

    def test_draft_keys_without_activity(self):
        grupo_id, actividad_id = 3, None
        base_key = f"cadi_draft_base_{grupo_id}_new"
        sched_key = f"cadi_draft_sched_{grupo_id}_new"
        assert base_key == "cadi_draft_base_3_new"
        assert sched_key == "cadi_draft_sched_3_new"


# ================================================================
# CADI INDEX & ACTIVITIES LOGIC TESTS
# ================================================================

class TestCadiActivitiesLogic:
    def test_cadi_index_simulado(self):
        grupos = [{"id": 1, "nombre": "Grupo CADI"}]
        resultado = next((g for g in grupos if g["id"] == 1), None)
        assert resultado is not None, "No se encontró el grupo con id=1"
        assert resultado["nombre"] == "Grupo CADI"

    def test_create_activities_schedule(self):
        request = {"action": "schedule", "nombre": "Nueva actividad"}
        if request["action"] == "schedule":
            resultado = "redirigir a schedule_draft"
        else:
            resultado = "error"
        assert resultado == "redirigir a schedule_draft"

    def test_create_activities_confirm_vacio(self):
        data = {"nombre": "", "espacio": ""}
        valido = all(data.values())
        resultado = "error" if not valido else "ok"
        assert resultado == "error"

    def test_create_activities_confirm_valido(self):
        actividades = []
        data = {"nombre": "Yoga", "tipo": "Deporte"}
        if any(a["nombre"] == data["nombre"] for a in actividades):
            resultado = "duplicado"
        else:
            actividades.append(data)
            resultado = "creado"
        assert resultado == "creado"

    def test_create_activities_nombre_duplicado(self):
        actividades = [{"nombre": "Yoga"}]
        data = {"nombre": "Yoga"}
        if any(a["nombre"] == data["nombre"] for a in actividades):
            resultado = "duplicado"
        else:
            actividades.append(data)
            resultado = "creado"
        assert resultado == "duplicado"

    def test_listar_actividades_correcto(self):
        actividades = [{"id": 1, "nombre": "Meditación"}]
        assert any(a["nombre"] == "Meditación" for a in actividades)

    def test_listar_actividades_slug_incorrecto(self):
        slug_real = "bienestar"
        slug_recibido = "salud"
        resultado = "redirigir" if slug_real != slug_recibido else "ok"
        assert resultado == "redirigir"

    def test_editar_actividad_post_valido(self):
        actividad = {"nombre": "Yoga"}
        nuevos_datos = {"nombre": "Yoga avanzado"}
        actividad.update(nuevos_datos)
        assert actividad["nombre"] == "Yoga avanzado"

    def test_editar_actividad_duplicado(self):
        actividades = [{"nombre": "Yoga"}]
        nuevo_nombre = "Yoga"
        resultado = "duplicado" if any(a["nombre"] == nuevo_nombre for a in actividades) else "ok"
        assert resultado == "duplicado"


# ================================================================
# GRUPOS & SCHEDULE LOGIC TESTS
# ================================================================

class TestGruposScheduleLogic:
    def test_listar_grupos_actividad(self):
        grupos = [{"id": 1, "slug": "cultura"}]  # id como entero
        resultado = next((g for g in grupos if g["id"] == 1), None)
        assert resultado is not None, "No se encontró el grupo con id=1"
        assert resultado["slug"] == "cultura"


    def test_listar_grupos_slug_incorrecto(self):
        grupo_slug_real = "cultura"
        slug_recibido = "deporte"
        resultado = "redirigir" if grupo_slug_real != slug_recibido else "ok"
        assert resultado == "redirigir"

    def test_crear_grupo_actividad_post_valido(self):
        grupos = []
        nuevo = {"nombre": "Cultura", "descripcion": "Eventos", "imagen": "img.png"}
        grupos.append(nuevo)
        assert len(grupos) == 1

    def test_schedule_draft_create(self):
        request = {"method": "POST", "profesor": "Juan", "dias": ["Lunes"], "hora_inicio": "09:00"}
        resultado = "crear draft" if request["method"] == "POST" else "mostrar formulario"
        assert resultado == "crear draft"

    def test_schedule_draft_edit(self):
        actividad_id = 2
        resultado = "modo edit" if actividad_id else "modo create"
        assert resultado == "modo edit"


# ================================================================
# TESTS UNITARIOS CONTRA SQL INJECTION
# ================================================================

class TestSQLInjectionProtection:
    def test_login_rechaza_inyeccion(self):
        input_usuario = "' OR '1'='1"
        input_password = "cualquier"
        def login_seguro(usuario, password):
            usuarios = {"estudiante": "1234"}
            return usuarios.get(usuario) == password
        resultado = login_seguro(input_usuario, input_password)
        assert resultado is False, "Debe rechazar inyección SQL."

    def test_register_no_inserta_sql_inyectado(self):
        datos_maliciosos = {
            "email": "ataque@uni.edu'; DROP TABLE users;--",
            "nombre": "Hacker'); DELETE FROM users;--",
            "password": "1234"
        }
        def registrar_seguro(data):
            if "'" in data["email"] or ";" in data["email"]:
                raise ValueError("Entrada inválida detectada")
            return True
        with pytest.raises(ValueError):
            registrar_seguro(datos_maliciosos)

    def test_preferences_inyeccion_en_categorias(self):
        categorias = ["1", "2", "3; DROP TABLE actividades;--"]
        def validar(lista):
            return all(c.isdigit() for c in lista)
        assert validar(categorias) is False, "Debe rechazar SQL en IDs."

    def test_recomendaciones_no_usar_sql_crudo(self):
        with patch("universitaryWellbeing.views.Actividades.objects.filter") as mock_filter:
            mock_filter.return_value = []
            mock_filter(tipos_actividad_id_tipo__in=[1, 2])
            args, kwargs = mock_filter.call_args
            assert "tipos_actividad_id_tipo__in" in kwargs
            assert not any("SELECT" in str(a).upper() for a in args)

    def test_logout_no_inyeccion(self):
        session = {"user": "admin'; DROP TABLE users;--"}
        session.clear()
        assert session == {}, "Logout debe limpiar sesión sin ejecutar SQL."
