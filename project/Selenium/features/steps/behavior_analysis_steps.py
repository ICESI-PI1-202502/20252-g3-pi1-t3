from behave import when, then
from pages.navbar_page import NavBar
from pages.analytics_menu_page import AnalyticsMenuPage
from pages.behavior_analysis_page import BehaviorAnalysisPage

@when("I open the behavior analysis page")
def step_open_behavior(context):
    AnalyticsMenuPage(context.driver).go_to_behavior_analysis()

@when('I filter behavior by activity type "{tipo}" and search')
def step_filter_tipo(context, tipo):
    page = BehaviorAnalysisPage(context.driver)
    page.choose_tipo(tipo)
    page.search()
    context._expected_tipo = tipo

@then('I should see at least one row with activity type "{tipo}"')
def step_assert_tipo(context, tipo):
    BehaviorAnalysisPage(context.driver).assert_any_row_tipo(tipo)
