from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class CADIHomeEntryPage(BasePage):
    # CTA específico para CADI (no el de Salud): href exacto
    CTA_GESTIONAR_CADI = (By.CSS_SELECTOR, "a[href='/cadi/cadi-home/-/1/']")

    def open_cadi_management(self):
        self.scroll_into_view(self.CTA_GESTIONAR_CADI, timeout=15)
        self.retry_click(self.CTA_GESTIONAR_CADI, timeout=15)
