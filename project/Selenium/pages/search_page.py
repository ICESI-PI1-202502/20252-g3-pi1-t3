from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage

class SearchPage(BasePage):
    INPUT_Q       = (By.CSS_SELECTOR, "input[name='q']")
    BTN_SUBMIT    = (By.CSS_SELECTOR, "button[type='submit'][title='Buscar'], .input-group-text[title='Buscar']")
    RESULT_TITLES = (By.CSS_SELECTOR, "#search-results .result-title")
    RESULTS_BOX   = (By.CSS_SELECTOR, "#search-results")

    # Modal de filtros
    BTN_OPEN_FILTERS   = (By.CSS_SELECTOR, 'button[data-bs-target="#filterModal"]')
    MODAL              = (By.CSS_SELECTOR, '#filterModal.show, .modal.show#filterModal')
    SELECT_TIPO        = (By.CSS_SELECTOR, '#filterModal select[name="tipo"], #filterModal #id_tipo[name="tipo"]')
    ONLY_AVAILABLE_CHK = (By.CSS_SELECTOR, '#filterModal input#onlyAvailable[name="only"][type="checkbox"][value="1"]')
    BTN_APLICAR        = (By.CSS_SELECTOR, '#filterModal button[type="submit"].yellowBotton_Black')

    CALIFICAR_LINK = (By.CSS_SELECTOR, 'a.yellowBotton_Black.mt-2.d-block[href*="/search/calificar/"]')
    SUCCESS_ALERT  = (By.CSS_SELECTOR, '.alert.alert-success.alert-dismissible')

 
    def search_by_name(self, text: str):
        self.type(self.INPUT_Q, text)
        try:
            self.retry_click(self.BTN_SUBMIT, timeout=6)
        except Exception:
            self.is_present(self.INPUT_Q, timeout=5).send_keys(Keys.ENTER)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(self.RESULT_TITLES)
        )

    def open_filters(self):
        self.scroll_into_view(self.BTN_OPEN_FILTERS, timeout=10)
        try:
            self.retry_click(self.BTN_OPEN_FILTERS, timeout=10)
        except Exception:
            self.click_js(self.BTN_OPEN_FILTERS, timeout=6)
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(self.MODAL)
        )

    def set_tipo_by_text(self, visible_text: str):
        sel = self.is_present(self.SELECT_TIPO, timeout=10)
        try:
            Select(sel).select_by_visible_text(visible_text)
        except Exception:
            mapping = {
                "Actividad Física y Salud": "4",
                "Agenda Cultural y Deportiva": "8",
                "Artes Escénicas": "2",
                "Artes Musicales": "3",
                "Artes Plásticas": "1",
                "Deportes de Conjunto": "5",
                "Deportes Individuales": "6",
                "Talleres Cortos": "7",
            }
            value = mapping.get(visible_text.strip(), "")
            if value:
                Select(sel).select_by_value(value)
            else:
                raise

    def enable_only_available(self, checked: bool = True):
        cb = self.is_present(self.ONLY_AVAILABLE_CHK, timeout=10)
        is_checked = cb.is_selected()
        if checked and not is_checked:
            try:
                self.click(self.ONLY_AVAILABLE_CHK)
            except Exception:
                self.click_js(self.ONLY_AVAILABLE_CHK, timeout=6)
        elif not checked and is_checked:
            try:
                self.click(self.ONLY_AVAILABLE_CHK)
            except Exception:
                self.click_js(self.ONLY_AVAILABLE_CHK, timeout=6)

    def apply_filters(self):
        self.scroll_into_view(self.BTN_APLICAR, timeout=10)
        try:
            self.retry_click(self.BTN_APLICAR, timeout=10)
        except Exception:
            self.click_js(self.BTN_APLICAR, timeout=6)

      
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(self.RESULTS_BOX)
        )


    def assert_result_title_present(self, expected: str):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(self.RESULTS_BOX)
        )
        titles = [el.text.strip() for el in self.driver.find_elements(*self.RESULT_TITLES)]
        assert any(expected.lower() in t.lower() for t in titles), \
            f"No se encontró '{expected}' en resultados: {titles}"

    def assert_result_title_absent(self, banned: str):
      
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(self.RESULTS_BOX)
        )
        titles = [el.text.strip() for el in self.driver.find_elements(*self.RESULT_TITLES)]
        assert all(banned.lower() not in t.lower() for t in titles), \
            f"Se encontró indebidamente '{banned}' en resultados: {titles}"
        

    def click_first_calificar(self):
        
        self.scroll_into_view(self.CALIFICAR_LINK, timeout=10)
        try:
            self.retry_click(self.CALIFICAR_LINK, timeout=10)
        except Exception:
            self.click_js(self.CALIFICAR_LINK, timeout=6)

        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/search/calificar/")
        )

    def assert_rating_success(self):
     
        WebDriverWait(self.driver, 10).until(EC.url_contains("/search"))
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(self.SUCCESS_ALERT)
        )
        alert_text = self.is_present(self.SUCCESS_ALERT, timeout=5).text.strip()
        assert "Tu calificación fue guardada correctamente." in alert_text, \
            f"Mensaje inesperado: {alert_text}"
