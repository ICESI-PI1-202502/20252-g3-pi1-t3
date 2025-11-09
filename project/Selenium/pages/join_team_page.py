from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage

class JoinTeamPage(BasePage):
    SELECT_TEAM = (By.ID, "team_id")
    BTN_SUBMIT  = (By.XPATH, "//button[@type='submit' and contains(.,'Unirme')]")

    def select_team_by_name(self, team_visible_text):
        sel = self.is_visible(self.SELECT_TEAM, timeout=10)
        s = Select(sel)
        # tolera " (máx: N)"
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

        # Asegura que el <select> quede vacío y con foco (esto ayuda a que el navegador muestre el tooltip)
        self.driver.execute_script("""
            const el = arguments[0];
            el.value = '';
            el.focus();
            el.dispatchEvent(new Event('change', {bubbles:true}));
        """, sel)

        # Intentar enviar vacío
        self.click(self.BTN_SUBMIT)

        # El form NO debe ser válido
        is_valid = self.driver.execute_script("return document.querySelector('form').checkValidity();")

        # Forzar el tooltip nativo (como en el create)
        self.driver.execute_script("document.querySelector('form').reportValidity();")

        # Mensaje nativo del <select required>
        validation_msg = self.driver.execute_script("return arguments[0].validationMessage || '';", sel)

        return is_valid, (validation_msg or "")
