# pages/cadi_activities_list_page.py
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from pages.base_page import BasePage

class CADIActivitiesListPage(BasePage):
    BTN_AGREGAR = (By.LINK_TEXT, "Agregar actividad")
    TITLES      = (By.CSS_SELECTOR, ".card h5")

    def click_add_activity(self):
        self.scroll_into_view(self.BTN_AGREGAR, timeout=15)
        self.retry_click(self.BTN_AGREGAR, timeout=15)

    def assert_activity_title_present(self, title: str):
        titles = [el.text.strip() for el in self.driver.find_elements(*self.TITLES)]
        assert title in titles, f"No se encontró el título '{title}'. Títulos visibles: {titles}"

    def open_edit_for_activity(self, title: str):
        # 1) Card por título (normalizamos espacios)
        card = self.is_present((
            By.XPATH,
            f"//h5[normalize-space()='{title}']/ancestor::div[contains(@class,'card')]"
        ), timeout=15)

        # 2) Intentar <a> con href que contenga '/editar'
        edit_el = None
        try:
            edit_el = card.find_element(By.XPATH, ".//a[contains(@href,'/editar')]")
        except NoSuchElementException:
            pass

        # 3) Fallback: img[alt='Editar'] → su <a> o <button> ancestro clickeable
        if edit_el is None:
            try:
                img = card.find_element(By.XPATH, ".//img[@alt='Editar']")
                # Ancestro clickeable (a o button). Si no hay, clic directo al img.
                try:
                    edit_el = img.find_element(By.XPATH, "./ancestor-or-self::a[1]")
                except NoSuchElementException:
                    try:
                        edit_el = img.find_element(By.XPATH, "./ancestor-or-self::button[1]")
                    except NoSuchElementException:
                        edit_el = img
            except NoSuchElementException:
                raise AssertionError("No se encontró control de edición (link ni ícono) en la card.")

        # 4) Scroll + click robusto (JS) para evitar overlays
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", edit_el)
        try:
            edit_el.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", edit_el)
