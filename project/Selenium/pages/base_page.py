from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, ElementNotInteractableException

class BasePage:
    def __init__(self, driver):
        self.driver = driver

    # ---------- waits / finds ----------
    def is_present(self, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def is_visible(self, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )

    def exists_now(self, locator):
        try:
            self.driver.find_element(*locator)
            return True
        except Exception:
            return False

    # ---------- interactions ----------
    def open(self, url):
        self.driver.get(url)

    def scroll_into_view(self, locator, timeout=10):
        el = self.is_present(locator, timeout=timeout)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        return el

    def click(self, locator, timeout=10):
        el = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(locator))
        try:
            el.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            self.click_js(locator, timeout=timeout)

    def click_js(self, locator, timeout=10):
        el = self.is_present(locator, timeout=timeout)
        self.driver.execute_script("arguments[0].click();", el)

    def retry_click(self, locator, timeout=10, attempts=3):
        last = None
        for _ in range(attempts):
            try:
                self.click(locator, timeout=timeout)
                return
            except Exception as e:
                last = e
        raise last

    def type(self, locator, text, timeout=20):
        el = self.is_visible(locator, timeout=timeout)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        try:
            el.clear()
        except Exception:
            pass
        try:
            el.click()
        except Exception:
            pass
        try:
            el.send_keys(text)
        except ElementNotInteractableException:
            # Fallback JS + eventos input/change
            self.driver.execute_script("arguments[0].value = arguments[1];", el, text)
            self.driver.execute_script("""
                const e1 = new Event('input', {bubbles:true});
                const e2 = new Event('change', {bubbles:true});
                arguments[0].dispatchEvent(e1); arguments[0].dispatchEvent(e2);
            """, el)
