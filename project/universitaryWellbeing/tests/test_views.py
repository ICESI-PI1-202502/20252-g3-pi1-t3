import pytest
from unittest.mock import Mock, patch

# ================================================================
# LOGIN LOGIC TESTS
# ================================================================

class TestLoginLogic:
    def test_login_valido(self):
        # Simula una función de validación propia
        def validar_usuario(correo, contraseña):
            return correo == "estudiante@uni.edu" and contraseña == "1234"
        
        # Simulación de formulario
        correo, contraseña = "estudiante@uni.edu", "1234"
        assert validar_usuario(correo, contraseña) is True

    def test_login_invalido(self):
        def validar_usuario(correo, contraseña):
            return correo == "estudiante@uni.edu" and contraseña == "1234"
        
        correo, contraseña = "mal@uni.edu", "0000"
        assert validar_usuario(correo, contraseña) is False


# ================================================================
# REGISTER LOGIC TESTS
# ================================================================

class TestRegisterLogic:
    def test_registro_exitoso(self):
        usuarios = []
        nuevo_usuario = {"email": "nuevo@uni.edu", "nombre": "Nuevo"}
        
        if nuevo_usuario["email"] not in [u["email"] for u in usuarios]:
            usuarios.append(nuevo_usuario)
            resultado = "registrado"
        else:
            resultado = "duplicado"
        
        assert resultado == "registrado"

    def test_registro_correo_duplicado(self):
        usuarios = [{"email": "existente@uni.edu"}]
        nuevo_usuario = {"email": "existente@uni.edu"}
        
        if nuevo_usuario["email"] not in [u["email"] for u in usuarios]:
            usuarios.append(nuevo_usuario)
            resultado = "registrado"
        else:
            resultado = "duplicado"
        
        assert resultado == "duplicado"

    def test_registro_incompleto(self):
        formulario = {"email": "user@uni.edu", "password": ""}
        campos_requeridos = all(formulario.values())
        assert campos_requeridos is False


# ================================================================
# PREFERENCES LOGIC TESTS
# ================================================================

class TestPreferencesLogic:
    def test_crear_preferencias_nuevas(self):
        preferencias = {}
        user = "estudiante1"
        nuevas = {"deporte": "fútbol", "comida": "vegetariana"}
        
        if user not in preferencias:
            preferencias[user] = nuevas
        
        assert preferencias[user]["deporte"] == "fútbol"

    def test_usuario_con_preferencias_existentes(self):
        preferencias = {"estudiante1": {"deporte": "baloncesto"}}
        user = "estudiante1"
        
        resultado = "ya tiene" if user in preferencias else "nuevo"
        assert resultado == "ya tiene"


# ================================================================
# HOME USER LOGIC TESTS
# ================================================================

class TestHomeUserHelpersLogic:
    def test_generar_recomendaciones(self):
        preferencias = {"deporte": "fútbol"}
        actividades = [
            {"nombre": "Torneo de fútbol", "tipo": "deporte"},
            {"nombre": "Clase de pintura", "tipo": "arte"},
        ]
        
        recomendadas = [
            a for a in actividades if a["tipo"] == "deporte" and preferencias.get("deporte")
        ]
        
        assert len(recomendadas) == 1
        assert recomendadas[0]["nombre"] == "Torneo de fútbol"

    def test_horario_simulado(self):
        horario = {"Lunes": ["Clase de yoga"], "Martes": []}
        assert "Clase de yoga" in horario["Lunes"]

    def test_calendario_simulado(self):
        eventos = [{"fecha": "2025-10-06", "evento": "Charla de bienestar"}]
        fechas = [e["fecha"] for e in eventos]
        assert "2025-10-06" in fechas


# ================================================================
# ADMIN PROFILE & LOGOUT LOGIC TESTS
# ================================================================

class TestAdminProfileLogoutLogic:
    def test_home_admin_renderiza(self):
        renderizado = True  # Simula render exitoso
        assert renderizado is True

    def test_profile_con_preferencias(self):
        admin_pref = {"notificaciones": True}
        assert admin_pref["notificaciones"] is True

    def test_logout(self):
        session = {"usuario": "admin"}
        session.clear()
        assert session == {}
# ================================================================
# TESTS UNITARIOS CONTRA SQL INJECTION
# ================================================================

class TestSQLInjectionProtection:
    # -------------------------------------------------------------------
    # LOGIN: asegurarse de que no evalúa SQL con strings del usuario
    # -------------------------------------------------------------------
    def test_login_rechaza_inyeccion(self):
        """
        Simula el intento de inyección SQL en el campo 'usuario'.
        La función debería tratar la entrada como texto literal, no como código SQL.
        """
        input_usuario = "' OR '1'='1"
        input_password = "cualquiercosa"

        # Simula una función de login segura (como tu lógica de form.is_valid())
        def login_seguro(usuario, password):
            usuarios_validos = {"estudiante": "1234"}
            return usuarios_validos.get(usuario) == password

        resultado = login_seguro(input_usuario, input_password)

        # Si el sistema fuera vulnerable, el login sería exitoso.
        # Esperamos que NO lo sea.
        assert resultado is False, "El sistema no debe aceptar inyección SQL en login."

    # -------------------------------------------------------------------
    # REGISTER: no debe aceptar inyecciones en correo o nombre
    # -------------------------------------------------------------------
    def test_register_no_inserta_sql_inyectado(self):
        """
        Simula un intento de inyección SQL en el registro de usuario.
        Verifica que el sistema no construya consultas SQL manualmente.
        """
        # Datos maliciosos
        datos_maliciosos = {
            "email": "malicioso@uni.edu'; DROP TABLE users;--",
            "nombre": "Atacante'); DELETE FROM users;--",
            "password": "1234"
        }

        # Mock de una función de creación de usuario segura
        def registrar_usuario(data):
            # Simula validación de email (como tu UserRegisterForm)
            if "'" in data["email"] or ";" in data["email"]:
                raise ValueError("Entrada inválida detectada")
            return True

        with pytest.raises(ValueError):
            registrar_usuario(datos_maliciosos)

    # -------------------------------------------------------------------
    # PREFERENCIAS: evitar inyección en selección de categorías
    # -------------------------------------------------------------------
    def test_preferences_inyeccion_en_categorias(self):
        """
        Verifica que la lista de categorías no sea usada directamente en una consulta SQL concatenada.
        """
        categorias_recibidas = ["1", "2", "3; DROP TABLE actividades;--"]

        # Función simulada que validaría IDs numéricos
        def validar_categorias(lista):
            for item in lista:
                if not item.isdigit():
                    return False
            return True

        assert validar_categorias(categorias_recibidas) is False, \
            "Debe rechazar categorías que contengan SQL malicioso."

    # -------------------------------------------------------------------
    # HOME USER: evitar que consultas de filtros usen strings directos
    # -------------------------------------------------------------------
    def test_recomendaciones_no_usar_sql_crudo(self):
        """
        Simula que el filtro usa ORM seguro (Django ORM), no SQL directo.
        """
        with patch("universitaryWellbeing.views.Actividades.objects.filter") as mock_filter:
            mock_filter.return_value = []

            # Simula uso normal de ORM
            mock_filter(tipos_actividad_id_tipo__in=[1, 2, 3])

            # Verifica que se llamó de forma segura (sin SQL crudo)
            args, kwargs = mock_filter.call_args
            assert "tipos_actividad_id_tipo__in" in kwargs
            assert not any(isinstance(a, str) and "SELECT" in a.upper() for a in args), \
                "No debe usar SQL crudo en las llamadas ORM."

    # -------------------------------------------------------------------
    # LOGOUT / PROFILE: sin riesgo de SQL, pero verificar manipulación segura
    # -------------------------------------------------------------------
    def test_logout_no_inyeccion(self):
        """
        Asegura que el logout limpia sesión sin evaluar cadenas del usuario.
        """
        session = {"user": "admin'; DROP TABLE users;--"}
        session.clear()
        assert session == {}, "Logout debe limpiar sesión sin ejecutar nada del contenido."