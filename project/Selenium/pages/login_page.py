from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from pages.base_page import BasePage

class LoginPage(BasePage):
    CEDULA   = (By.CSS_SELECTOR, "input[name='cedula']")
    PASSWORD = (By.CSS_SELECTOR, "input[name='password'][type='password']:not([disabled])")
    BTN_LOGIN = (By.ID, "loginButton")
    PANEL_ADMIN_LINK  = (By.CSS_SELECTOR, "#sidebar a[href^='/admin']")   # ^ empieza con /admin
    PANEL_ADMIN_TEXT  = (By.XPATH, "//*[@id='sidebar']//a[contains(normalize-space(),'Admin') or contains(normalize-space(),'Administrador')]")


    CALENDARIO_BTN = (
        By.XPATH,
        "//button[contains(@class,'accordion-button') and contains(normalize-space(),'Calendario')]"
    )

    MENU_BTN          = (By.ID, "menu-btn")  
    SIDEBAR_PANEL     = (By.ID, "sidebar")  
    PANEL_ADMIN_LINK  = (By.CSS_SELECTOR, "#sidebar a[href='/admin/']")
  
    PANEL_ADMIN_TEXT  = (By.LINK_TEXT, "Panel de Administrador")

    ERROR_PASS = (By.XPATH, "//*[contains(text(),'Contraseña incorrecta.')]")
    ERROR_USER = (By.XPATH, "//*[contains(text(),'El usuario con esa cédula no existe.')]")


    def iniciar_sesion(self, cedula, password):
        self.type(self.CEDULA, cedula)
        self.type(self.PASSWORD, password)
        self.click(self.BTN_LOGIN)

 
    def login_exitoso(self):
  
        self.driver.execute_script("window.scrollTo(0, 0);")
        self.is_present(self.CALENDARIO_BTN, timeout=20)
        self.is_visible(self.CALENDARIO_BTN, timeout=20)
        return True

    def _abrir_menu(self):
   
        try:
            sidebar = self.is_present(self.SIDEBAR_PANEL, timeout=5)
            classes = sidebar.get_attribute("class") or ""
            if "open" in classes:
                return
        except Exception:
            pass

     
        try:
            self.retry_click(self.MENU_BTN, timeout=12)
        except Exception:
     
            self.click_js(self.MENU_BTN, timeout=10)

        WebDriverWait(self.driver, 10).until(
            lambda d: "open" in (d.find_element(*self.SIDEBAR_PANEL).get_attribute("class") or "")
        )

    def login_admin_exitoso(self):
        # Asegura menú abierto
        self._abrir_menu()

        # Intenta localizar el enlace de admin por href o por texto
        admin_el = None
        try:
            admin_el = self.is_visible(self.PANEL_ADMIN_LINK, timeout=10)
        except Exception:
            try:
                admin_el = self.is_visible(self.PANEL_ADMIN_TEXT, timeout=6)
            except Exception:
                pass

        if not admin_el:
            # Último intento: si ya estás dentro del admin por redirección, valida por URL
            if "/admin" in (self.driver.current_url or ""):
                return True
            # No se halló el enlace: probablemente el usuario no es admin o el texto/href cambió.
            return False

        # Click al enlace de admin y valida que carga
        try:
            admin_el.click()
        except Exception:
            self.click_js(self.PANEL_ADMIN_LINK, timeout=4)

        # Espera llegada al admin (URL y algún encabezado típico)
        WebDriverWait(self.driver, 15).until(EC.url_contains("/admin"))
        # Encabezados típicos (ajusta si tienes branding personalizado)
        possible_admin_headers = [
            (By.CSS_SELECTOR, "#header"),                            # Django admin default
            (By.CSS_SELECTOR, "h1, .breadcrumbs, .dashboard-title"), # genéricos
        ]
        found_any = False
        for loc in possible_admin_headers:
            try:
                self.is_present(loc, timeout=3)
                found_any = True
                break
            except Exception:
                continue

        return found_any

    def error_contrasena(self):
        self.is_visible(self.ERROR_PASS, timeout=20)
        return True

    def error_usuario(self):
        self.is_visible(self.ERROR_USER, timeout=20)
        return True
