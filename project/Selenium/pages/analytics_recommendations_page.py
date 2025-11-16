from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class AnalyticsRecommendationsPage(BasePage):
    LINK_CONFIG_ALERTS = (By.CSS_SELECTOR, 'a[href="/analytics-reports/configurar-notificaciones/"]')

    def open_notifications_config(self):
        self.scroll_into_view(self.LINK_CONFIG_ALERTS, timeout=12)
        self.retry_click(self.LINK_CONFIG_ALERTS, timeout=12)
