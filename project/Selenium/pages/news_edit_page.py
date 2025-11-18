from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class NewsEditPage(BasePage):

    TITLE = (By.NAME, "titulo")
    SUBMIT = (By.XPATH, "//button[@type='submit']")

    def edit_title(self, new_title):
        self.type(self.TITLE, new_title)
        self.click(self.SUBMIT)
