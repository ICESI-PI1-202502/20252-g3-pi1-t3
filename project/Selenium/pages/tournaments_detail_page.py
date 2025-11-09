from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class TournamentDetailPage(BasePage):
    BTN_CREATE_TEAM = (By.XPATH, "//a[contains(@class,'btn') and contains(@href,'/teams/create')]")
    # Título/encabezado de la sección (útil para esperar tras submit)
    TEAMS_SECTION = (By.XPATH, "//*[contains(normalize-space(), 'Equipos registrados')]")
    BTN_JOIN_TEAM     = (By.XPATH, "//a[contains(@class,'btn') and contains(@href,'/teams/join')]")
    BTN_MANAGE_MYTEAM = (By.XPATH, "//a[contains(@class,'btn') and contains(@href,'/teams/') and contains(@href,'/manage/')]")

    def go_to_create_team(self):
        self.click(self.BTN_CREATE_TEAM)

    def go_to_join_team(self):
        self.click(self.BTN_JOIN_TEAM)

    def go_to_manage_my_team(self):
        self.click(self.BTN_MANAGE_MYTEAM)


    def team_name_is_listed(self, team_name):
        # Asegura que estamos en la vista de detalles (por si hubo redirect)
        try:
            self.is_visible(self.TEAMS_SECTION, timeout=15)
        except Exception:
            pass

        # Busca ambas variantes: “Equipo - X” y “X” a pelo
        prefixed = (By.XPATH, f"//li[contains(normalize-space(),'Equipo - {team_name}')]")
        plain    = (By.XPATH, f"//*[contains(normalize-space(), '{team_name}')]")

        try:
            self.is_visible(prefixed, timeout=8)
            return True
        except Exception:
            try:
                self.is_visible(plain, timeout=5)
                return True
            except Exception:
                return False
