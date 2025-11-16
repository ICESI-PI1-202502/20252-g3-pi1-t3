from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class AttendanceManagementPage(BasePage):
    LINK_REGISTER_INDIV = (By.CSS_SELECTOR, 'a[href="/analytics-reports/registrar-asistencia/"]')

    def open_register_individual(self):
        self.scroll_into_view(self.LINK_REGISTER_INDIV, timeout=12)
        self.retry_click(self.LINK_REGISTER_INDIV, timeout=12)
