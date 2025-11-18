from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class PSUProjectsAdminPage(BasePage):
    BTN_CREATE = (By.CSS_SELECTOR, 'a[href*="/psu/proyectos/crear"]')

    def open_create_form(self):
        self.scroll_into_view(self.BTN_CREATE, timeout=12)
        self.retry_click(self.BTN_CREATE, timeout=12)
