from behave import when, then
from pages.navbar_page import NavBar
from pages.analytics_menu_page import AnalyticsMenuPage
from pages.analytics_recommendations_page import AnalyticsRecommendationsPage
from pages.notifications_config_page import NotificationsConfigPage

@when("I go to recommendations from analytics menu")
def step_go_recommendations(context):
    NavBar(context.driver).open_menu()
    NavBar(context.driver).go_to_analytics_reports()
    AnalyticsMenuPage(context.driver).go_to_recommendations()

@when("I open notifications config")
def step_open_notif_config(context):
    AnalyticsRecommendationsPage(context.driver).open_notifications_config()

@when("I save notifications config with zeros")
def step_submit_zeros(context):
    page = NotificationsConfigPage(context.driver)
    is_valid, m1, m2 = page.submit_with_zeros_expect_min_warning()
    context._notif_valid = is_valid
    context._notif_msgs  = (m1 + " " + m2).lower()

@then("I should see a native min-1 warning in notifications config")
def step_assert_min_warning(context):
    assert context._notif_valid is False, "El formulario no debería ser válido con valores 0."
    txt = context._notif_msgs
    ok = any(s in txt for s in [
        "mayor o igual que 1",
        "superior o igual a 1",
        "greater than or equal to 1"
    ])
    assert ok, f"Mensaje inesperado: '{txt}'"
