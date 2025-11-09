from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage
import unicodedata

class AnalyticsComparisonsPage(BasePage):
    SELECT_TIEMPO   = (By.ID, "tiempo")
    INPUT_INICIO    = (By.ID, "inicio")
    SELECT_SEMESTRE = (By.ID, "semestre_filtro")
    INPUT_FIN       = (By.ID, "fin")
    SELECT_AGRUP    = (By.ID, "agrupacion")
    BTN_APLICAR     = (By.XPATH, "//button[normalize-space()='Aplicar fechas']")
    ALERT_INFO      = (By.CSS_SELECTOR, ".alert.alert-info")
    BTN_ACTUALIZAR  = (By.XPATH, "//button[normalize-space()='Actualizar']")
    H3_RESULT       = (By.CSS_SELECTOR, "h3")

    def choose_custom_period(self):
        sel = self.is_present(self.SELECT_TIEMPO, timeout=12)
        Select(sel).select_by_value("periodo")
        self.is_visible(self.INPUT_INICIO, timeout=12)
        self.is_visible(self.INPUT_FIN, timeout=12)

    def set_dates(self, inicio_yyyy_mm_dd, fin_yyyy_mm_dd):
        ini = self.is_present(self.INPUT_INICIO, timeout=10)
        fin = self.is_present(self.INPUT_FIN, timeout=10)
        self.driver.execute_script("""
            arguments[0].value = arguments[2];
            arguments[1].value = arguments[3];
            const e1 = new Event('input', {bubbles:true});
            const e2 = new Event('change', {bubbles:true});
            arguments[0].dispatchEvent(e1); arguments[0].dispatchEvent(e2);
            arguments[1].dispatchEvent(e1); arguments[1].dispatchEvent(e2);
        """, ini, fin, inicio_yyyy_mm_dd, fin_yyyy_mm_dd)

    def set_grouping(self, value="facultad"):
        sel = self.is_present(self.SELECT_AGRUP, timeout=10)
        try:
            Select(sel).select_by_value(value)
        except Exception:
            Select(sel).select_by_visible_text("Facultad")

    def apply(self):
        self.scroll_into_view(self.BTN_APLICAR, timeout=10)
        self.retry_click(self.BTN_APLICAR, timeout=10)

    def wait_info_alert_and_get_text(self):
        el = WebDriverWait(self.driver, 12).until(
            EC.visibility_of_element_located(self.ALERT_INFO)
        )
        return el.text.strip()

    def choose_semester_specific(self):
        sel = self.is_present(self.SELECT_TIEMPO, timeout=12)
        Select(sel).select_by_value("semestre")
        WebDriverWait(self.driver, 12).until(
            EC.presence_of_element_located(self.SELECT_SEMESTRE)
        )

    def pick_semester(self, value="2"):
        sel = self.is_present(self.SELECT_SEMESTRE, timeout=12)
        try:
            Select(sel).select_by_value(value)
        except Exception:
            Select(sel).select_by_visible_text(f"Semestre {value}")

    def set_grouping_facultad(self):
        sel = self.is_present(self.SELECT_AGRUP, timeout=10)
        try:
            Select(sel).select_by_value("facultad")
        except Exception:
            Select(sel).select_by_visible_text("Facultad")

    def click_update(self):
        self.scroll_into_view(self.BTN_ACTUALIZAR, timeout=10)
        self.retry_click(self.BTN_ACTUALIZAR, timeout=10)

    def get_results_heading(self):
        el = WebDriverWait(self.driver, 12).until(
            EC.visibility_of_element_located(self.H3_RESULT)
        )
        return el.text.strip()

    @staticmethod
    def _norm(s: str) -> str:
        s = unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode("ascii")
        return " ".join(s.lower().strip().split())

    def assert_results_sem2_group_facultad(self):
        h = self._norm(self.get_results_heading())
        ok = ("resultados:" in h) and ("estudiantes de 2 semestre" in h) and ("agrupado por facultad" in h)
        assert ok, f"Encabezado inesperado: '{h}'"
