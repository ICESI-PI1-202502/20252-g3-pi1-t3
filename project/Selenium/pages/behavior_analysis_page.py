import unicodedata
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage

def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode("ascii").strip().lower()

class BehaviorAnalysisPage(BasePage):
    SELECT_TIPO  = (By.CSS_SELECTOR, 'select[name="tipo_actividad"]')
    BTN_BUSCAR   = (By.CSS_SELECTOR, 'button.btn.btn-primary.w-100')
    COL_TIPO_TDS = (By.CSS_SELECTOR, 'table.table tbody tr td:nth-child(5)')  

    def choose_tipo(self, visible_text: str):
        sel = self.is_present(self.SELECT_TIPO, timeout=12)
        try:
            Select(sel).select_by_visible_text(visible_text)
        except Exception:
        
            Select(sel).select_by_value("2")

    def search(self):
   
        try:
            self.retry_click(self.BTN_BUSCAR, timeout=10)
        except Exception:
            self.click_js(self.BTN_BUSCAR, timeout=6)

       
        WebDriverWait(self.driver, 12).until(
            EC.presence_of_all_elements_located(self.COL_TIPO_TDS)
        )

    def assert_any_row_tipo(self, expected: str):
        tds = self.driver.find_elements(*self.COL_TIPO_TDS)
        tipos = [td.text.strip() for td in tds]
        exp = _norm(expected)
        ok = any(exp == _norm(t) for t in tipos)
        assert ok, f"No se encontró una fila con tipo '{expected}'. Tipos visibles: {tipos}"
