from behave import when, then
from pages.navbar_page import NavBar
from pages.analytics_menu_page import AnalyticsMenuPage
from pages.analytics_comparisons_page import AnalyticsComparisonsPage

@when("I go to analytics & reports from the menu")
def step_go_analytics(context):
    NavBar(context.driver).go_to_analytics_reports()

@when("I open the comparisons & statistics page")
def step_open_comparisons(context):
    AnalyticsMenuPage(context.driver).go_to_comparisons()

@when("I set an invalid custom period (start 2029, end 2025) grouped by Facultad and apply")
def step_set_invalid_period(context):
    page = AnalyticsComparisonsPage(context.driver)
    page.choose_custom_period()
    page.set_dates("2029-01-01", "2025-01-01")
    page.set_grouping("facultad")
    page.apply()
    context._alert_text = page.wait_info_alert_and_get_text()

@then("I should see the info alert about selecting filters")
def step_assert_info_alert(context):
    txt = (context._alert_text or "").lower()
    # Mensaje esperado (permitimos pequeñas variaciones)
    ok = "selecciona los filtros" in txt and "actualizar" in txt
    assert ok, f"Alert inesperado: {context._alert_text}"
