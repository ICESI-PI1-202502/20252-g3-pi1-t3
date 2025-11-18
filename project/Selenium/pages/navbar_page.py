from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from pages.base_page import BasePage
from selenium.webdriver.support import expected_conditions as EC

class NavBar(BasePage):
    MENU_BTN = (By.ID, "menu-btn")
    SIDEBAR  = (By.ID, "sidebar")
    LINK_TOURNAMENTS = (By.CSS_SELECTOR, '#sidebar a[href="/tournaments/"]')
    LINK_SEARCH = (By.CSS_SELECTOR, '#sidebar a[href="/search/"]')
    LINK_SCHEDULE = (By.CSS_SELECTOR, '#sidebar a[href="/horario/"]') 
    LINK_ANALYTICS = (By.CSS_SELECTOR, '#sidebar a[href="/analytics-reports/"]')
    LINK_PSU         = (By.CSS_SELECTOR, '#sidebar a[href="/psu/proyectos/"]')
    LINK_UNIFIED_SCHEDULE = (By.CSS_SELECTOR, '#sidebar a[href="/calendario-unificado/"]')


    def open_menu(self):
        try:
            classes = self.is_present(self.SIDEBAR, timeout=5).get_attribute("class") or ""
            if "open" in classes:
                return
        except Exception:
            pass

       
        try:
            self.retry_click(self.MENU_BTN, timeout=8, attempts=2)
        except Exception:
            self.click_js(self.MENU_BTN, timeout=5)

       
        WebDriverWait(self.driver, 10).until(
            lambda d: "open" in (d.find_element(*self.SIDEBAR).get_attribute("class") or "")
        )
        self.is_visible(self.LINK_TOURNAMENTS, timeout=10)

    def go_to_tournaments(self):
        self.click(self.LINK_TOURNAMENTS)

    def go_to_search(self):
        self.open_menu()
    
        try:
            self.click(self.LINK_SEARCH)
        except Exception:
            self.click_js(self.LINK_SEARCH, timeout=5)

    def go_to_analytics_reports(self):
        self.open_menu()
        try:
            self.click(self.LINK_ANALYTICS)
        except Exception:
            self.click_js(self.LINK_ANALYTICS, timeout=5)

        # 🔹 Espera a que cargue la página de Analítica
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                'a[href="/analytics/attendance/"], a[href$="gestion-asistencia/"]'  # pon el correcto
            ))
        )

    def go_to_psu_projects(self):
        self.open_menu()

        # 1) Esperar a que exista el link en el sidebar
        link = self.is_present(self.LINK_PSU, timeout=10)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)

        # 2) Click normal + fallback JS
        try:
            link.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", link)

        # 3) Esperar a que cargue algo propio de la página de PSU
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                'input[name="q"], a[href="/psu/proyectos/crear/"]'
            ))
        )

    def go_to_unified_schedule(self):
        self.open_menu()
        try:
            self.click(self.LINK_UNIFIED_SCHEDULE)
        except Exception:
            self.click_js(self.LINK_UNIFIED_SCHEDULE, timeout=5)
        WebDriverWait(self.driver, 15).until(EC.url_contains("/calendario-unificado"))

    def go_to_schedule(self):
        self.open_menu()
        try:
            self.click(self.LINK_SCHEDULE)
        except Exception:
            self.click_js(self.LINK_SCHEDULE, timeout=5)
        WebDriverWait(self.driver, 15).until(EC.url_contains("/horario"))

