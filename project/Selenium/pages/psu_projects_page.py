from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage


class PSUProjectsPage(BasePage):
    INPUT_Q = (By.CSS_SELECTOR, 'input[name="q"]')
    BTN_SEARCH = (By.CSS_SELECTOR, 'button[type="submit"].btn.btn-primary, .btn.btn-primary[type="submit"]')
    RESULT_TITLES = (By.CSS_SELECTOR, 'article.card-item h3.title')
    # Make create selector flexible to match admin variations
    BTN_CREATE = (By.CSS_SELECTOR, 'a[href*="/psu/proyectos/crear"]')

    def search(self, text: str):
        self.type(self.INPUT_Q, text)
        try:
            self.retry_click(self.BTN_SEARCH, timeout=6)
        except Exception:
            self.is_present(self.INPUT_Q, timeout=5).send_keys(Keys.ENTER)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(self.RESULT_TITLES)
        )

    def assert_result_title_present(self, expected: str):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(self.RESULT_TITLES)
        )
        titles = [el.text.strip() for el in self.driver.find_elements(*self.RESULT_TITLES)]
        assert any(expected.lower() == t.lower() for t in titles), \
            f"No se encontró '{expected}'. Títulos: {titles}"

    def open_details_for_title(self, title: str):
        card_h3 = (By.XPATH, f"//article[contains(@class,'card-item')]//h3[contains(@class,'title')][normalize-space()='{title}']")
        h3_el = self.is_present(card_h3, timeout=12)
        article = h3_el.find_element(By.XPATH, "./ancestor::article[contains(@class,'card-item')]")
        details = article.find_element(By.CSS_SELECTOR, "a.btn.btn-detail")
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", details)
        try:
            details.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", details)
        WebDriverWait(self.driver, 12).until(
            EC.presence_of_element_located((By.XPATH, "//button[@type='submit' and contains(normalize-space(),'Inscribirme')]") )
        )

    def open_create_form(self):
        # Scroll and click the create button (admin view) with multiple fallbacks.
        el = self.scroll_into_view(self.BTN_CREATE, timeout=12)

        # 1) Try regular click
        try:
            el.click()
        except Exception:
            # 2) Try BasePage's retry_click which handles common interception issues
            try:
                self.retry_click(self.BTN_CREATE, timeout=8)
            except Exception:
                # 3) Try JS click on the element
                try:
                    self.driver.execute_script("arguments[0].click();", el)
                except Exception:
                    # 4) Fallback: navigate to the href directly (if present)
                    try:
                        href = el.get_attribute("href")
                        if href:
                            self.driver.get(href)
                    except Exception:
                        pass

        # Wait for the create form to appear (input 'nombre') or for URL containing '/crear'
        try:
            WebDriverWait(self.driver, 12).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="nombre"]'))
            )
        except Exception:
            WebDriverWait(self.driver, 8).until(EC.url_contains('/crear'))

