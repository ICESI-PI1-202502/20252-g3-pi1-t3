from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class Sidebar(BasePage):

    MANAGE_NEWS_LINK = (By.LINK_TEXT, "Gestionar Noticias")

    def go_to_manage_news(self):
        self.click(self.MANAGE_NEWS_LINK)
