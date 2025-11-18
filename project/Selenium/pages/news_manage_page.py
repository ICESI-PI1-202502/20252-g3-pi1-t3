from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class NewsManagePage(BasePage):

    CREATE_BUTTON = (By.LINK_TEXT, "Crear Nueva Noticia")
    FIRST_NEWS_TITLE = (By.CSS_SELECTOR, "tbody tr td a")

    def click_create_news(self):
        self.click(self.CREATE_BUTTON)

    def open_news_by_title(self, title):
        locator = (By.XPATH, f"//a[text()='{title}']")
        self.click(locator)

    def open_edit_form(self, title):
        locator = (By.XPATH, f"//a[text()='{title}']/../../td/a[contains(@class,'btn-primary')]")
        self.click(locator)

    def open_delete_modal(self, title):
        locator = (By.XPATH, f"//a[text()='{title}']/../../td/button")
        self.click(locator)

    def confirm_delete(self, title):
        modal_button = (By.XPATH, f"//form[contains(@action,'{title}')]/button[@type='submit']")
        self.click(modal_button)

