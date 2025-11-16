from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage

class PSUProjectDetailPage(BasePage):
    BTN_ENROLL = (By.XPATH, "//button[@type='submit' and contains(normalize-space(),'Inscribirme')]")
    ALERT_SUCCESS = (By.CSS_SELECTOR, ".alert.alert-success")

    def enroll_and_wait_success(self):
        self.scroll_into_view(self.BTN_ENROLL, timeout=12)
        try:
            self.retry_click(self.BTN_ENROLL, timeout=12)
        except Exception:
            self.click_js(self.BTN_ENROLL, timeout=8)

        el = WebDriverWait(self.driver, 12).until(
            EC.visibility_of_element_located(self.ALERT_SUCCESS)
        )
        return el.text.strip()
