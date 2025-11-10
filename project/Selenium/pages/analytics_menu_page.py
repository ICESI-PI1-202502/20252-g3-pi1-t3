from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class AnalyticsMenuPage(BasePage):
    LINK_COMPARISONS = (By.CSS_SELECTOR, 'a[href="/analytics-reports/comparaciones/"]')
    LINK_BEHAVIOR    = (By.CSS_SELECTOR, 'a[href="/analytics-reports/analisis-comportamiento/"]')
    LINK_RECOMMEND     = (By.CSS_SELECTOR, 'a[href="/analytics-reports/recomendaciones/"]')
    LINK_ATTEND_MGMT   = (By.CSS_SELECTOR, 'a[href="/analytics-reports/gestion-asistencia/"]') 

    def go_to_comparisons(self):
        self.scroll_into_view(self.LINK_COMPARISONS, timeout=12)
        self.retry_click(self.LINK_COMPARISONS, timeout=12)

    def go_to_behavior_analysis(self):  
        self.scroll_into_view(self.LINK_BEHAVIOR, timeout=12)
        self.retry_click(self.LINK_BEHAVIOR, timeout=12)

    def go_to_recommendations(self):  # NUEVO
        self.scroll_into_view(self.LINK_RECOMMEND, timeout=12)
        self.retry_click(self.LINK_RECOMMEND, timeout=12)

    def go_to_attendance_mgmt(self):  # NUEVO
        self.scroll_into_view(self.LINK_ATTEND_MGMT, timeout=12)
        self.retry_click(self.LINK_ATTEND_MGMT, timeout=12)
        
