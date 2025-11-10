from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage

class TeamCreatePage(BasePage):
    INPUT_NOMBRE   = (By.NAME, "nombre_equipo")
    INPUT_RESP_ID  = (By.NAME, "responsable_id")
    SELECT_DISC    = (By.NAME, "disciplina_id")
    INPUT_MIN      = (By.NAME, "capacidad_min")
    INPUT_MAX      = (By.NAME, "capacidad_max")
    BTN_SUBMIT     = (By.XPATH, "//button[@type='submit' and contains(.,'Crear equipo')]")

    def fill_form(self, nombre_equipo, responsable_id, disciplina, capacidad_min, capacidad_max):
        self.type(self.INPUT_NOMBRE, nombre_equipo)
        self.type(self.INPUT_RESP_ID, responsable_id)
        select_el = self.is_present(self.SELECT_DISC, timeout=10)
        Select(select_el).select_by_visible_text(disciplina)
        self.type(self.INPUT_MIN, str(capacidad_min))
        self.type(self.INPUT_MAX, str(capacidad_max))

    def submit(self):
        self.click(self.BTN_SUBMIT)

    def submit_expect_required_errors(self):
  
        self.click(self.BTN_SUBMIT)
 
        is_valid = self.driver.execute_script("return document.querySelector('form').checkValidity();")
   
        nombre_el = self.is_present(self.INPUT_NOMBRE, timeout=10)
        validation_msg = self.driver.execute_script("return arguments[0].validationMessage;", nombre_el)
        return is_valid, (validation_msg or "")

