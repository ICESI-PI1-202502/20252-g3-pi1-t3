from behave import when, then
from pages.navbar_page import NavBar
from pages.search_page import SearchPage

@when("I open the sidebar menu")
def step_open_sidebar(context):
    NavBar(context.driver).open_menu()

@when("I go to the search page from the menu")
def step_go_to_search(context):
    NavBar(context.driver).go_to_search()

@when('I search CADI activities by name "{query}"')
def step_search_by_name(context, query):
    SearchPage(context.driver).search_by_name(query)

@then('I should see the search result titled "{expected}"')
def step_assert_result(context, expected):
    SearchPage(context.driver).assert_result_title_present(expected)
