
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from pages.base_page import BasePage
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class CADIActivitiesListPage(BasePage):
    BTN_AGREGAR = (By.LINK_TEXT, "Agregar actividad")
    TITLES      = (By.CSS_SELECTOR, ".card h5")

    def click_add_activity(self):
        self.scroll_into_view(self.BTN_AGREGAR, timeout=15)
        self.retry_click(self.BTN_AGREGAR, timeout=15)

    def assert_activity_title_present(self, title: str):
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_all_elements_located(self.TITLES)
        )
        titles = [el.text.strip() for el in self.driver.find_elements(*self.TITLES)]
        assert title in titles, f"No se encontró el título '{title}'. Títulos visibles: {titles}"

    def open_edit_for_activity(self, title: str):
       
        card = self.is_present((
            By.XPATH,
            f"//h5[normalize-space()='{title}']/ancestor::div[contains(@class,'card')]"
        ), timeout=15)

       
        edit_el = None
        try:
            edit_el = card.find_element(By.XPATH, ".//a[contains(@href,'/editar')]")
        except NoSuchElementException:
            pass

      
        if edit_el is None:
            try:
                img = card.find_element(By.XPATH, ".//img[@alt='Editar']")
              
                try:
                    edit_el = img.find_element(By.XPATH, "./ancestor-or-self::a[1]")
                except NoSuchElementException:
                    try:
                        edit_el = img.find_element(By.XPATH, "./ancestor-or-self::button[1]")
                    except NoSuchElementException:
                        edit_el = img
            except NoSuchElementException:
                raise AssertionError("No se encontró control de edición (link ni ícono) en la card.")

        
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", edit_el)
        try:
            edit_el.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", edit_el)
