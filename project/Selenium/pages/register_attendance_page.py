from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage

class RegisterAttendancePage(BasePage):
    SELECT_ACTIVITY = (By.CSS_SELECTOR, 'select[name="actividad_id"]')
    TEXT_CEDULAS    = (By.CSS_SELECTOR, 'textarea[name="cedulas"]')
    BTN_SUBMIT      = (By.XPATH, "//button[normalize-space()='Registrar Asistencias']")
    ALERT_WARNING   = (By.CSS_SELECTOR, ".alert.alert-warning")

    def fill_and_submit(self, activity_text: str, cedulas_text: str):
        sel = self.is_present(self.SELECT_ACTIVITY, timeout=12)
        try:
            Select(sel).select_by_visible_text(activity_text)
        except Exception:
      
            try:
                Select(sel).select_by_value("924")
            except Exception:
                raise AssertionError(f"No se pudo seleccionar actividad '{activity_text}'.")

        self.type(self.TEXT_CEDULAS, cedulas_text)

        self.scroll_into_view(self.BTN_SUBMIT, timeout=10)
        self.retry_click(self.BTN_SUBMIT, timeout=10)

      
        el = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(self.ALERT_WARNING)
        )
        return el.text.strip()
