from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage

class UnifiedSchedulePage(BasePage):
    CALENDAR_CONTAINER = (By.CSS_SELECTOR, "#calendar, .fc")  # fallback
    MODAL_CONTENT = (By.CSS_SELECTOR, ".modal.show .modal-content")

    def _event_title_locator(self, title: str):
        # FullCalendar: título dentro de <div class="fc-event-title ...">
        xpath = f'//div[contains(@class,"fc-event-title") and normalize-space()="{title}"]'
        return (By.XPATH, xpath)

    def open_event_by_title(self, title: str):
        # Espera a que cargue el calendario y el evento
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located(self.CALENDAR_CONTAINER)
        )
        locator = self._event_title_locator(title)
        el = WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located(locator)
        )
        self.scroll_into_view(locator, timeout=10)

        # Click directo → fallback al ancestro clickable → fallback JS
        try:
            self.retry_click(locator, timeout=10)
        except Exception:
            try:
                parent = el.find_element(By.XPATH, './ancestor::*[contains(@class,"fc-event")][1]')
                self.scroll_into_view_webelement(parent)
                self.retry_click_webelement(parent, timeout=6)
            except Exception:
                self.click_js(locator, timeout=6)

        # Esperar apertura de modal
        WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(self.MODAL_CONTENT)
        )

    def assert_modal_title(self, title: str):
        # Verifica la fila con el título dentro del modal
        row_locator = (
            By.XPATH,
            f'//div[contains(@class,"fc-modal-row") and normalize-space()="{title}"]'
        )
        WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(row_locator)
        )
