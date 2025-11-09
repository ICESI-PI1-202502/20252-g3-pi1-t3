from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage

class NotificationsConfigPage(BasePage):
    INPUT_UMBRAL = (By.ID, "umbral_asistencia")
    INPUT_DIAS   = (By.ID, "dias_inactividad")
    BTN_SAVE     = (By.XPATH, "//button[normalize-space()='Guardar Configuración']")

    def _set_value_js(self, locator, val):
        el = self.is_present(locator, timeout=10)
        self.driver.execute_script("""
            arguments[0].value = arguments[1];
            const e1 = new Event('input', {bubbles:true});
            const e2 = new Event('change', {bubbles:true});
            arguments[0].dispatchEvent(e1); arguments[0].dispatchEvent(e2);
        """, el, str(val))
        return el

    def submit_with_zeros_expect_min_warning(self):
        umbral_el = self._set_value_js(self.INPUT_UMBRAL, 0)
        dias_el   = self._set_value_js(self.INPUT_DIAS, 0)

        self.scroll_into_view(self.BTN_SAVE, timeout=10)
        self.retry_click(self.BTN_SAVE, timeout=10)

        # El form debe ser inválido (min=1); tomamos mensajes nativos
        is_valid = self.driver.execute_script("return document.querySelector('form').checkValidity();")
        msg1 = self.driver.execute_script("return arguments[0].validationMessage;", umbral_el) or ""
        msg2 = self.driver.execute_script("return arguments[0].validationMessage;", dias_el) or ""
        return is_valid, msg1.strip(), msg2.strip()
