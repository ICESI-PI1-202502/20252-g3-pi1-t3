from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#ir a C:\Users\luisg\Desktop\Integrador\20252-g3-pi1-t3\project\selenium>
#y ejecutar por ejemplo: behave features/register.feature
#
#
class BasePage:
    def __init__(self, driver):
        self.driver = driver

    def open(self, url):
        self.driver.get(url)

    def click(self, locator):
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(locator)
        ).click()

    def type(self, locator, text):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(locator)
        ).send_keys(text)

    def is_visible(self, locator):
        return WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(locator)
        )
