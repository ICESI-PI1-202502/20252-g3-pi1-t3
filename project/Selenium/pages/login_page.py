from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from pages.base_page import BasePage

class LoginPage(BasePage):
    # --- Login ---
    CEDULA   = (By.CSS_SELECTOR, "input[name='cedula']")
    PASSWORD = (By.CSS_SELECTOR, "input[name='password'][type='password']:not([disabled])")
    BTN_LOGIN = (By.ID, "loginButton")

    # --- Usuario normal: botón del acordeón "Calendario" ---
    CALENDARIO_BTN = (
        By.XPATH,
        "//button[contains(@class,'accordion-button') and contains(normalize-space(),'Calendario')]"
    )

    # --- Menú hamburguesa y panel admin (locators exactos del HTML que enviaste) ---
    MENU_BTN          = (By.ID, "menu-btn")  # <a id="menu-btn" ...>
    SIDEBAR_PANEL     = (By.ID, "sidebar")   # <div id="sidebar" class="sidebar open">
    PANEL_ADMIN_LINK  = (By.CSS_SELECTOR, "#sidebar a[href='/admin/']")
    # Alternativas, por si cambian clases:
    PANEL_ADMIN_TEXT  = (By.LINK_TEXT, "Panel de Administrador")

    # --- Errores ---
    ERROR_PASS = (By.XPATH, "//*[contains(text(),'Contraseña incorrecta.')]")
    ERROR_USER = (By.XPATH, "//*[contains(text(),'El usuario con esa cédula no existe.')]")

    # --- Acciones ---
    def iniciar_sesion(self, cedula, password):
        self.type(self.CEDULA, cedula)
        self.type(self.PASSWORD, password)
        self.click(self.BTN_LOGIN)

    # --- Validaciones ---
    def login_exitoso(self):
        # Asegura que aparezca el acordeón con "Calendario"
        self.driver.execute_script("window.scrollTo(0, 0);")
        self.is_present(self.CALENDARIO_BTN, timeout=20)
        self.is_visible(self.CALENDARIO_BTN, timeout=20)
        return True

    def _abrir_menu(self):
        # Si ya está abierto #sidebar con la clase "open", no hacer nada
        try:
            sidebar = self.is_present(self.SIDEBAR_PANEL, timeout=5)
            classes = sidebar.get_attribute("class") or ""
            if "open" in classes:
                return
        except Exception:
            pass

        # Clic robusto en el <a id="menu-btn">
        try:
            self.retry_click(self.MENU_BTN, timeout=12)
        except Exception:
            # último recurso: JS click
            self.click_js(self.MENU_BTN, timeout=10)

        # Espera a que el sidebar esté abierto
        WebDriverWait(self.driver, 10).until(
            lambda d: "open" in (d.find_element(*self.SIDEBAR_PANEL).get_attribute("class") or "")
        )

    def login_admin_exitoso(self):
        # Abre menú si aún no se ve el enlace del panel
        if not self.exists_now(self.PANEL_ADMIN_LINK):
            self._abrir_menu()

        # Espera el link /admin/ visible
        try:
            self.is_visible(self.PANEL_ADMIN_LINK, timeout=15)
        except Exception:
            # fallback por texto visible
            self.is_visible(self.PANEL_ADMIN_TEXT, timeout=10)
        return True

    def error_contrasena(self):
        self.is_visible(self.ERROR_PASS, timeout=20)
        return True

    def error_usuario(self):
        self.is_visible(self.ERROR_USER, timeout=20)
        return True
