from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage

class RatePage(BasePage):
    STAR_SELECT = (By.CSS_SELECTOR, 'select#estrellas[name="estrellas"]')
    CONFIRM_BTN = (By.CSS_SELECTOR, 'button.greenBotton_White[type="submit"]')

    def rate_and_confirm(self, stars: int):
        # Seleccionar estrellas
        select_el = self.is_present(self.STAR_SELECT, timeout=10)
        Select(select_el).select_by_value(str(stars))

        # Confirmar
        try:
            self.retry_click(self.CONFIRM_BTN, timeout=10)
        except Exception:
            self.click_js(self.CONFIRM_BTN, timeout=6)

        # Esperar redirección a /search
        WebDriverWait(self.driver, 10).until(EC.url_contains("/search"))
