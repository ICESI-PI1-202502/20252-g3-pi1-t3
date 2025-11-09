from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage

class SearchPage(BasePage):
    INPUT_Q       = (By.CSS_SELECTOR, "input[name='q']")
    BTN_SUBMIT    = (By.CSS_SELECTOR, "button[type='submit'][title='Buscar'], .input-group-text[title='Buscar']")
    RESULT_TITLES = (By.CSS_SELECTOR, "#search-results .result-title")

    def search_by_name(self, text: str):
        self.type(self.INPUT_Q, text)
        # click normal → fallback ENTER
        try:
            self.retry_click(self.BTN_SUBMIT, timeout=6)
        except Exception:
            self.is_present(self.INPUT_Q, timeout=5).send_keys(Keys.ENTER)

        # espera a que salgan resultados
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(self.RESULT_TITLES)
        )

    def assert_result_title_present(self, expected: str):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(self.RESULT_TITLES)
        )
        titles = [el.text.strip() for el in self.driver.find_elements(*self.RESULT_TITLES)]
        assert any(expected.lower() in t.lower() for t in titles), \
            f"No se encontró '{expected}' en resultados: {titles}"
