from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from pages.base_page import BasePage

class LoginPage(BasePage):
    CEDULA   = (By.CSS_SELECTOR, "input[name='cedula']")
    PASSWORD = (By.CSS_SELECTOR, "input[name='password'][type='password']:not([disabled])")
    BTN_LOGIN = (By.ID, "loginButton")


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
    
        if not self.exists_now(self.PANEL_ADMIN_LINK):
            self._abrir_menu()

        try:
            self.is_visible(self.PANEL_ADMIN_LINK, timeout=15)
        except Exception:
            self.is_visible(self.PANEL_ADMIN_TEXT, timeout=10)
        return True

    def error_contrasena(self):
        self.is_visible(self.ERROR_PASS, timeout=20)
        return True

    def error_usuario(self):
        self.is_visible(self.ERROR_USER, timeout=20)
        return True
