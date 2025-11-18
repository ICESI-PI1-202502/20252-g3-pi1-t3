from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class NewsDetailPage(BasePage):

    TITLE = (By.TAG_NAME, "h1")

    def get_title(self):
        return self.get_text(self.TITLE)
