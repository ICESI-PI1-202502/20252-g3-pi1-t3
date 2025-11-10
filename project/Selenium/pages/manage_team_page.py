from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class ManageTeamPage(BasePage):

    H2_TITLE = (By.XPATH, "//h2[contains(normalize-space(),'Gestionar equipo')]")

    def header_contains_team(self, team_visible_text):
        h2 = self.is_visible(self.H2_TITLE, timeout=15)
        return team_visible_text in (h2.text or "")
