import time
import psycopg2
from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class RegisterPage(BasePage):
    # --- Localizadores ---
    LINK_REGISTRARSE = (By.XPATH, "//a[contains(., 'Registrarse')]")
    INPUT_CEDULA = (By.NAME, "cedula")
    INPUT_NOMBRE = (By.NAME, "nombre_completo")
    INPUT_EMAIL = (By.NAME, "email")
    INPUT_PASSWORD = (By.NAME, "password")
    BOTON_REGISTRAR = (By.XPATH, "//form//*[contains(., 'Registrarse')]")

    MENSAJE_EXITO = (By.XPATH, "//*[contains(text(), 'Usuario registrado con éxito. Ahora puede iniciar sesión.')]")
    MENSAJE_ERROR = (By.XPATH, "//*[contains(text(), 'This field is required.')]")

    # --- Acciones ---
    def abrir_formulario(self):
        self.click(self.LINK_REGISTRARSE)
        time.sleep(2)

    def registrar_usuario(self, cedula, nombre, email, password):
        self.type(self.INPUT_CEDULA, cedula)
        self.type(self.INPUT_NOMBRE, nombre)
        self.type(self.INPUT_EMAIL, email)
        if password:
            self.type(self.INPUT_PASSWORD, password)
        self.click(self.BOTON_REGISTRAR)
        time.sleep(2)

    # --- Validaciones ---
    def registro_exitoso(self):
        return self.is_visible(self.MENSAJE_EXITO)

    def registro_error(self):
        return self.is_visible(self.MENSAJE_ERROR)

    # --- Limpieza (usa tu misma lógica original) ---
    def eliminar_usuario_existente(self):
        try:
            conn = psycopg2.connect(
                host="aws-1-us-east-2.pooler.supabase.com",
                database="postgres",
                user="postgres.xlknciyujekwbhysmamn",
                password="h9TZan8icTf3hjsn",
                port="5432",
                sslmode="require"
            )
            cur = conn.cursor()
            cur.execute("DELETE FROM participantes WHERE id_participante = %s;", ("1122334455",))
            cur.execute("DELETE FROM auth_user WHERE email = %s;", ("usuario@correo.com",))
            conn.commit()
            cur.close()
            conn.close()
            print(" Usuario de prueba eliminado (si existía).")
        except Exception as e:
            print(f" Error al eliminar usuario: {e}")
