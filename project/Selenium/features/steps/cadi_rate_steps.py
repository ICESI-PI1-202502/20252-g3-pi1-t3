from behave import when, then
from pages.search_page import SearchPage
from pages.rate_page import RatePage

@when('I click the CADI "Calificar" button')
def step_click_calificar(context):
    SearchPage(context.driver).click_first_calificar()

@when('I set the CADI rating to "{stars:d}" stars and confirm')
def step_rate_and_confirm(context, stars):
    RatePage(context.driver).rate_and_confirm(stars)

@then("I should see the CADI rating success message")
def step_assert_rating_success(context):
    SearchPage(context.driver).assert_rating_success()
