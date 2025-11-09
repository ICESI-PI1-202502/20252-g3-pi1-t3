from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage

class PSUProjectsPage(BasePage):
    INPUT_Q        = (By.CSS_SELECTOR, 'input[name="q"]')
    BTN_SEARCH     = (By.CSS_SELECTOR, 'button[type="submit"].btn.btn-primary, .btn.btn-primary[type="submit"]')
    RESULT_TITLES  = (By.CSS_SELECTOR, 'article.card-item h3.title')

    def search(self, text: str):
        self.type(self.INPUT_Q, text)
        # Click normal → ENTER fallback
        try:
            self.retry_click(self.BTN_SEARCH, timeout=6)
        except Exception:
            self.is_present(self.INPUT_Q, timeout=5).send_keys(Keys.ENTER)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(self.RESULT_TITLES)
        )

    def assert_result_title_present(self, expected: str):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(self.RESULT_TITLES)
        )
        titles = [el.text.strip() for el in self.driver.find_elements(*self.RESULT_TITLES)]
        assert any(expected.lower() == t.lower() for t in titles), \
            f"No se encontró '{expected}'. Títulos: {titles}"
