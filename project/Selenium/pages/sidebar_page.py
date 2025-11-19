from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class Sidebar(BasePage):

    MANAGE_NEWS_LINK = (By.LINK_TEXT, "Gestionar Noticias")

    def go_to_manage_news(self):
        # Ensure sidebar/menu is open before clicking the manage news link
        try:
            from pages.navbar_page import NavBar
            NavBar(self.driver).open_menu()
        except Exception:
            pass

        # Click the link (BasePage.click will wait until visible/clickable)
        self.click(self.MANAGE_NEWS_LINK)
