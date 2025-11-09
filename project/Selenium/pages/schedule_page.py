from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class SchedulePage(BasePage):
    BTN_WEEK = (By.ID, "btn-week")  # <button id="btn-week" ...>Semana</button>

    def assert_week_button_visible(self):
        self.is_visible(self.BTN_WEEK, timeout=12)
        return True
