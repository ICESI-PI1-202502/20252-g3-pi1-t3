from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class NewsDetailPage(BasePage):

    TITLE = (By.TAG_NAME, "h1")

    def get_title(self):
        return self.get_text(self.TITLE)

    PUBLICATION_LABEL = (By.XPATH, "//strong[normalize-space()='Fecha de Publicación:']")

    def has_publication_label(self, timeout=5):
        try:
            # esperamos a que el label esté presente/visible en el detalle
            return bool(self.is_visible(self.PUBLICATION_LABEL, timeout=timeout))
        except Exception:
            return False
