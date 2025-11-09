from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from pages.base_page import BasePage

class NavBar(BasePage):
    MENU_BTN = (By.ID, "menu-btn")
    SIDEBAR  = (By.ID, "sidebar")
    LINK_TOURNAMENTS = (By.CSS_SELECTOR, '#sidebar a[href="/tournaments/"]')
    LINK_SEARCH = (By.CSS_SELECTOR, '#sidebar a[href="/search/"]')

    def open_menu(self):
        # Si ya está abierto, salir
        try:
            classes = self.is_present(self.SIDEBAR, timeout=5).get_attribute("class") or ""
            if "open" in classes:
                return
        except Exception:
            pass

        # Click normal → fallback JS → reintentos
        try:
            self.retry_click(self.MENU_BTN, timeout=8, attempts=2)
        except Exception:
            self.click_js(self.MENU_BTN, timeout=5)

        # Esperar a que el sidebar tenga la clase "open" y el link sea visible
        WebDriverWait(self.driver, 10).until(
            lambda d: "open" in (d.find_element(*self.SIDEBAR).get_attribute("class") or "")
        )
        self.is_visible(self.LINK_TOURNAMENTS, timeout=10)

    def go_to_tournaments(self):
        self.click(self.LINK_TOURNAMENTS)

    def go_to_search(self):
        self.open_menu()
        # Click normal, fallback JS para evitar overlays
        try:
            self.click(self.LINK_SEARCH)
        except Exception:
            self.click_js(self.LINK_SEARCH, timeout=5)
