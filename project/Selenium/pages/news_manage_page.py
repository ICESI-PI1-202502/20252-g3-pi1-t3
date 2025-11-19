from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class NewsManagePage(BasePage):
    CREATE_BUTTON = (By.LINK_TEXT, "Crear Nueva Noticia")

    def click_create_news(self):
        self.click(self.CREATE_BUTTON)

    def title_exists(self, title):
        locator = (By.XPATH, f"//a[normalize-space()='{title}']")
        return self.exists_now(locator)

    def open_news_by_title(self, title):
        locator = (By.XPATH, f"//a[normalize-space()='{title}']")
        self.click(locator)

    def open_edit_form(self, title):
        # Encuentra la fila que contiene el título y hace click en el botón Editar de esa fila
        locator = (By.XPATH, f"//a[normalize-space()='{title}']/ancestor::tr//a[contains(@class,'btn-primary') and contains(@href,'/editar')]")
        self.click(locator)

    def open_delete_modal(self, title):
        locator = (By.XPATH, f"//a[normalize-space()='{title}']/ancestor::tr//button[contains(@class,'btn-danger')]")
        self.click(locator)

    def confirm_delete(self, title):
        # intenta localizar el botón de confirmación dentro del modal actualmente abierto
        modal_submit = (By.XPATH, "//div[contains(@class,'modal') and contains(@class,'show')]//button[@type='submit']")
        self.click(modal_submit)

