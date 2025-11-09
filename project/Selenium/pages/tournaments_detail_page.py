from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from selenium.webdriver.support.ui import WebDriverWait
import time
from selenium.webdriver.support import expected_conditions as EC

class TournamentDetailPage(BasePage):
    BTN_CREATE_TEAM = (By.XPATH, "//a[contains(@class,'btn') and contains(@href,'/teams/create')]")
    # Título/encabezado de la sección (útil para esperar tras submit)
    TEAMS_SECTION = (By.XPATH, "//*[contains(normalize-space(), 'Equipos registrados')]")
    BTN_JOIN_TEAM     = (By.XPATH, "//a[contains(@class,'btn') and contains(@href,'/teams/join')]")
    BTN_MANAGE_MYTEAM = (By.XPATH, "//a[contains(@class,'btn') and contains(@href,'/teams/') and contains(@href,'/manage/')]")
    BTN_REGISTER_MATCH = (By.XPATH, "//a[contains(@class,'btn') and contains(@href,'/matches/create/')]")
    MATCH_TABLE = (By.CSS_SELECTOR, "table tbody")

    def go_to_create_team(self):
        self.click(self.BTN_CREATE_TEAM)

    def go_to_join_team(self):
        self.click(self.BTN_JOIN_TEAM)

    def go_to_manage_my_team(self):
        self.click(self.BTN_MANAGE_MYTEAM)

    def go_to_register_match(self):
        self.click(self.BTN_REGISTER_MATCH)


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
    
     # Verifica una fila con "Equipo A vs Equipo B" y el lugar
    def match_is_listed(self, team_a, team_b, place, timeout=25):
        """Retorna True si aparece una fila con ambos equipos y el lugar."""
        # Espera a que exista la tabla
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(self.MATCH_TABLE)
        )
        ta = team_a.lower()
        tb = team_b.lower()
        pl = place.lower()

        # Polling: por si el render tarda un poco tras el redirect
        end = time.time() + timeout
        while time.time() < end:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            for row in rows:
                txt = row.text.lower()
                # No dependemos del orden exacto ni de acentos/capitalización
                if (ta in txt) and (tb in txt) and (pl in txt):
                    return True
            time.sleep(0.4)
        return False
