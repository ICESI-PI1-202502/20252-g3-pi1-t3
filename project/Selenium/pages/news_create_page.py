from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class NewsCreatePage(BasePage):

    TITLE = (By.NAME, "titulo")
    ENUNCIADO = (By.NAME, "enunciado")
    DESCRIPCION = (By.NAME, "descripcion")
    IMAGEN = (By.ID, "imagen")
    SUBMIT = (By.XPATH, "//button[@type='submit']")

    def create_news(self, titulo, enunciado="Enunciado de prueba", descripcion="Descripción de prueba"):
        self.type(self.TITLE, titulo)
        self.type(self.ENUNCIADO, enunciado)
        self.type(self.DESCRIPCION, descripcion)
        self.click(self.SUBMIT)
