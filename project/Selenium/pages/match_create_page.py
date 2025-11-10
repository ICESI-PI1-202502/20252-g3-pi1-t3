from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage

class MatchCreatePage(BasePage):
    SELECT_A   = (By.NAME, "equipo_a")
    SELECT_B   = (By.NAME, "equipo_b")
    INPUT_INI  = (By.NAME, "inicio") 
    INPUT_FIN  = (By.NAME, "fin")
    INPUT_LUGAR= (By.NAME, "lugar")
    BTN_SUBMIT = (By.XPATH, "//button[@type='submit' and contains(.,'Aprobar y publicar')]")

    def _to_datetime_local(self, dt_str):
     
        return dt_str.replace(" ", "T")

    def _set_datetime_local(self, locator, dt_str):
        el = self.is_present(locator, timeout=10)
        value = self._to_datetime_local(dt_str)
    
        self.driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', {bubbles:true}));
            arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
        """, el, value)

    def fill_form(self, team_a_text, team_b_text, start_dt, end_dt, place):
 
        sel_a = Select(self.is_present(self.SELECT_A, timeout=10))
        sel_b = Select(self.is_present(self.SELECT_B, timeout=10))
        sel_a.select_by_visible_text(team_a_text)
        sel_b.select_by_visible_text(team_b_text)

 
        self._set_datetime_local(self.INPUT_INI, start_dt)
        self._set_datetime_local(self.INPUT_FIN, end_dt)

 
        self.type(self.INPUT_LUGAR, place)

    def submit(self):
        self.click(self.BTN_SUBMIT)
