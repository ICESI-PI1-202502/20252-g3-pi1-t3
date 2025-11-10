from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage

class PSUProjectFormPage(BasePage):
    INPUT_NOMBRE = (By.CSS_SELECTOR, 'input[name="nombre"]')
    INPUT_AFORO  = (By.CSS_SELECTOR, 'input[name="aforo"]')
    TEXT_DESC    = (By.CSS_SELECTOR, 'textarea[name="descripcion"]')
    INPUT_INICIO = (By.CSS_SELECTOR, 'input[name="fecha_inicio"]')
    INPUT_FIN    = (By.CSS_SELECTOR, 'input[name="fecha_fin"]')
    BTN_CONFIRM  = (By.CSS_SELECTOR, 'button.greenBotton_White')  # "Confirmar"
    ALERT_DANGER = (By.CSS_SELECTOR, '.alert.alert-danger')

 
    def fill_name_capacity_desc(self, name: str, capacity: str, description: str = ""):
        self.type(self.INPUT_NOMBRE, name)
        self.type(self.INPUT_AFORO, str(capacity))
        if description:
            self.type(self.TEXT_DESC, description)

    def set_dates(self, start_yyyy_mm_dd: str, end_yyyy_mm_dd: str):
        ini = self.is_present(self.INPUT_INICIO, timeout=10)
        fin = self.is_present(self.INPUT_FIN, timeout=10)

        self.driver.execute_script("""
            arguments[0].value = arguments[2];
            arguments[1].value = arguments[3];
            const e = new Event('change', {bubbles:true});
            arguments[0].dispatchEvent(e); arguments[1].dispatchEvent(e);
        """, ini, fin, start_yyyy_mm_dd, end_yyyy_mm_dd)

    def submit(self):
        self.scroll_into_view(self.BTN_CONFIRM, timeout=10)
        self.retry_click(self.BTN_CONFIRM, timeout=10)

    def wait_danger_alert_text(self, timeout=10):
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.ALERT_DANGER)
            )
            return el.text.strip()
        except Exception:
            return ""

    def submit_with_negative_aforo_expect_min_error(self, nombre: str, aforo_neg: int = -1):
        self.type(self.INPUT_NOMBRE, nombre)
        aforo_el = self.is_present(self.INPUT_AFORO, timeout=12)
        try: aforo_el.clear()
        except Exception: pass
        aforo_el.send_keys(str(aforo_neg))
        self.scroll_into_view(self.BTN_CONFIRM)
        self.retry_click(self.BTN_CONFIRM, timeout=10)
        is_valid = self.driver.execute_script("return document.querySelector('form').checkValidity();")
        validation_msg = self.driver.execute_script("return arguments[0].validationMessage;", aforo_el) or ""
        return is_valid, validation_msg
