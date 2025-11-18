from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage
from pages.navbar_page import NavBar


class Sidebar(BasePage):

    MANAGE_NEWS_LINK = (By.LINK_TEXT, "Gestionar Noticias")
    LINK_PSU = (By.CSS_SELECTOR, 'a[href*="/psu/proyectos"]')

    def go_to_manage_news(self):
        self.click(self.MANAGE_NEWS_LINK)

    def go_to_psu_projects(self):
        """Admin-oriented navigation to PSU projects. Ensures sidebar is open and clicks the PSU link.

        This mirrors the behavior used in `NavBar.go_to_psu_projects` but is accessible
        from admin steps that interact with the `Sidebar` component.
        """
        # Ensure the sidebar/menu is open (NavBar knows how to open it)
        try:
            NavBar(self.driver).open_menu()
        except Exception:
            pass

        # Wait for the link to be present and click it
        link = self.is_present(self.LINK_PSU, timeout=10)
        try:
            link.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", link)

        # Wait for the PSU page to load (either search input or create link)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="q"], a[href*="/psu/proyectos/crear"]'))
        )
