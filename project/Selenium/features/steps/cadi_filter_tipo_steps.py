from behave import when, then
from pages.navbar_page import NavBar
from pages.search_page import SearchPage

@when("I open the CADI search filters")
def step_open_filters(context):
    SearchPage(context.driver).open_filters()

@when('I filter CADI by activity type "{tipo_text}" and apply')
def step_filter_tipo(context, tipo_text):
    page = SearchPage(context.driver)
    page.set_tipo_by_text(tipo_text)
    page.apply_filters()

@then('I should see "Ajedrez" among the CADI results')
def step_assert_ajedrez(context):
    SearchPage(context.driver).assert_result_title_present("Ajedrez")
