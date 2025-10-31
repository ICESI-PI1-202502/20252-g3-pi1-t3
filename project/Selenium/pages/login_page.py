import time
from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class LoginPage(BasePage):
    # --- Localizadores ---
    CEDULA = (By.NAME, "cedula")
    PASSWORD = (By.NAME, "password")
    BTN_LOGIN = (By.ID, "loginButton")

    # --- Elementos esperados ---
    CALENDARIO = (By.XPATH, "//*[contains(text(),'Calendario')]")
    ERROR_PASS = (By.XPATH, "//*[contains(text(),'Contraseña incorrecta.')]")
    ERROR_USER = (By.XPATH, "//*[contains(text(),'El usuario con esa cédula no existe.')]")
    PANEL_ADMIN = (By.XPATH, "//*[contains(text(), 'Gestionar actividades')]")

    # --- Acciones ---
    def iniciar_sesion(self, cedula, password):
        self.type(self.CEDULA, cedula)
        time.sleep(1)
        self.type(self.PASSWORD, password)
        self.click(self.BTN_LOGIN)
        time.sleep(2)

    # --- Validaciones ---
    def login_exitoso(self):
        return self.is_visible(self.CALENDARIO)

    def login_admin_exitoso(self):
        return self.is_visible(self.PANEL_ADMIN)

    def error_contrasena(self):
        return self.is_visible(self.ERROR_PASS)

    def error_usuario(self):
        return self.is_visible(self.ERROR_USER)
