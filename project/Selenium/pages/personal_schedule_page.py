from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage

class PersonalSchedulePage(BasePage):
    CALENDAR_CONTAINER = (By.CSS_SELECTOR, "#calendar, .fc")          # FullCalendar contenedor
    MODAL_CONTENT      = (By.CSS_SELECTOR, ".modal.show .modal-content")

    BTN_MONTH          = (By.CSS_SELECTOR, '#btn-month.btn.btn-view')

    # Botón eliminar del primer modal (detalle del evento)
    DELETE_BTN         = (By.CSS_SELECTOR, '.modal.show #btn-delete-event.btn.btn-danger')

    # Modal de confirmación y su botón
    CONFIRM_HEADER     = (By.CSS_SELECTOR, '.modal.show #confirmDeleteLabel, .modal.show .modal-title')
    CONFIRM_DELETE_BTN = (By.CSS_SELECTOR, '.modal.show #btn-confirm-delete.btn.btn-danger')

    # Toast
    TOAST_BODY         = (By.CSS_SELECTOR, '.toast-body')

    def _event_title_locator(self, title: str):
        xpath = f'//div[contains(@class,"fc-event-title") and normalize-space()="{title}"]'
        return (By.XPATH, xpath)

    def open_event_by_title(self, title: str):
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located(self.CALENDAR_CONTAINER)
        )
        locator = self._event_title_locator(title)
        el = WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located(locator)
        )
        self.scroll_into_view(locator, timeout=10)
        try:
            self.retry_click(locator, timeout=10)
        except Exception:
            try:
                parent = el.find_element(By.XPATH, './ancestor::*[contains(@class,"fc-event")][1]')
                self.scroll_into_view_webelement(parent)
                self.retry_click_webelement(parent, timeout=6)
            except Exception:
                self.click_js(locator, timeout=6)

        # Esperar apertura del modal de detalle
        WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(self.MODAL_CONTENT)
        )

    def assert_modal_title_detail(self, title: str):
        row_label = (
            By.XPATH,
            '//div[@class="modal-body"]//div[@id="event-details"]'
            '//div[contains(@class,"event-detail-item")]'
            '[div[contains(@class,"event-detail-label")][normalize-space()="Título"]]'
        )
        row_value_strong = (
            By.XPATH,
            '//div[@class="modal-body"]//div[@id="event-details"]'
            '//div[contains(@class,"event-detail-item")]'
            '[div[contains(@class,"event-detail-label")][normalize-space()="Título"]]'
            '//div[contains(@class,"event-detail-value")]//strong[normalize-space()="'+title+'"]'
        )
        WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located(row_label))
        WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located(row_value_strong))

    def _click_delete_button(self, locator):
        WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable(locator))
        try:
            self.retry_click(locator, timeout=10)
        except Exception:
            self.click_js(locator, timeout=6)

    def delete_opened_event_with_confirmation(self):
        """
        Flujo real:
        1) Modal de detalle → botón #btn-delete-event
        2) Modal de confirmación → botón #btn-confirm-delete
        """
        # 1) Click en "Eliminar Evento" del primer modal
        self._click_delete_button(self.DELETE_BTN)

        # 2) Esperar el modal de confirmación y su botón
        WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located(self.CONFIRM_HEADER))
        WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located(self.CONFIRM_DELETE_BTN))

        # 3) Confirmar eliminación
        self._click_delete_button(self.CONFIRM_DELETE_BTN)

    def assert_deletion_toast_for_title(self, title: str):
        toast = WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(self.TOAST_BODY)
        )
        text = toast.text.strip()
        expected = f'Evento "{title}" eliminado correctamente'
        assert expected in text, f'Toast inesperado.\nEsperado: {expected}\nRecibido: {text}'

    # (Opcional) útil si quieres comprobar que ya no está en el calendario:
    def assert_event_absent_in_calendar(self, title: str):
        locator = self._event_title_locator(title)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(self.CALENDAR_CONTAINER))
        elems = self.driver.find_elements(*locator)
        assert len(elems) == 0, f'El evento "{title}" sigue presente en el calendario.'

    def click_month_view(self):
        # Click robusto al botón "Mes"
        WebDriverWait(self.driver, 15).until(EC.presence_of_element_located(self.CALENDAR_CONTAINER))
        try:
            self.retry_click(self.BTN_MONTH, timeout=8)
        except Exception:
            self.click_js(self.BTN_MONTH, timeout=6)
        # opcional: pequeña espera a que FullCalendar termine de pintar
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(self.CALENDAR_CONTAINER))

        
    def assert_modal_source_automatic(self):
        # Valida "Fuente" → <span class="event-badge badge-automatica">Creado automáticamente</span>
        fuente_row = (
            By.XPATH,
            '//div[@class="modal-body"]//div[@id="event-details"]'
            '//div[contains(@class,"event-detail-item")]'
            '[div[contains(@class,"event-detail-label")][normalize-space()="Fuente"]]'
        )
        badge_automatica = (
            By.XPATH,
            '//div[@class="modal-body"]//div[@id="event-details"]'
            '//div[contains(@class,"event-detail-item")]'
            '[div[contains(@class,"event-detail-label")][normalize-space()="Fuente"]]'
            '//span[contains(@class,"event-badge") and contains(@class,"badge-automatica")'
            ' and normalize-space()="Creado automáticamente"]'
        )
        WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located(fuente_row))
        WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located(badge_automatica))