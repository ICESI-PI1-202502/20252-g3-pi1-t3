from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class TournamentsPage(BasePage):
    # Card con título y botón "Detalles"
    # article.tournament-card -> h3.title == <tournament_title> y dentro un <a class="btn">Detalles</a>
    def open_details_for_title(self, title_text):
        card = (
            By.XPATH,
            f"//article[contains(@class,'tournament-card')][.//h3[normalize-space()='{title_text}']]//a[contains(@class,'btn') and normalize-space()='Detalles']"
        )
        self.click(card)
