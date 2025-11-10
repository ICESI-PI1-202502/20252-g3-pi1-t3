from behave import when, then
from time import sleep
from pages.search_page import SearchPage

@when('I enable the "Only available" filter and apply')
def step_enable_only_available(context):
    page = SearchPage(context.driver)
    page.enable_only_available(True)
    page.apply_filters()

@when("I wait {seconds:d} seconds")
def step_wait_seconds(context, seconds):
    sleep(seconds)

@then('I should not see "{title}" among the CADI results')
def step_not_see_title(context, title):
    SearchPage(context.driver).assert_result_title_absent(title)
