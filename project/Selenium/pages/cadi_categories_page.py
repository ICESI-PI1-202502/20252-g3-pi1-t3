from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class CADICategoriesPage(BasePage):

    def open_category_by_name(self, name: str):
        img_locator = (By.CSS_SELECTOR, f"img[alt='{name}']")
        img = self.scroll_into_view(img_locator, timeout=15)
      
        self.driver.execute_script("""
            const img = arguments[0];
            const a = img.closest('a') || img;
            a.click();
        """, img)
