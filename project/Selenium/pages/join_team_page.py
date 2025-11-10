from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage

class JoinTeamPage(BasePage):
    SELECT_TEAM = (By.ID, "team_id")
    BTN_SUBMIT  = (By.XPATH, "//button[@type='submit' and contains(.,'Unirme')]")

    def select_team_by_name(self, team_visible_text):
        sel = self.is_visible(self.SELECT_TEAM, timeout=10)
        s = Select(sel)
      
        for o in s.options:
            if team_visible_text in (o.text or ""):
                s.select_by_visible_text(o.text)
                return
        raise AssertionError(f"No se encontró una opción que contenga: {team_visible_text}")

    def submit(self):
        self.click(self.BTN_SUBMIT)

    def submit_expect_required_errors(self):
        """
        Gemelo del TeamCreatePage.submit_expect_required_errors(), adaptado al <select required>.
        Intenta enviar vacío y lee la validación nativa.
        """
        sel = self.is_present(self.SELECT_TEAM, timeout=10)

       
        self.driver.execute_script("""
            const el = arguments[0];
            el.value = '';
            el.focus();
            el.dispatchEvent(new Event('change', {bubbles:true}));
        """, sel)

        self.click(self.BTN_SUBMIT)

        is_valid = self.driver.execute_script("return document.querySelector('form').checkValidity();")

    
        self.driver.execute_script("document.querySelector('form').reportValidity();")

        validation_msg = self.driver.execute_script("return arguments[0].validationMessage || '';", sel)

        return is_valid, (validation_msg or "")
