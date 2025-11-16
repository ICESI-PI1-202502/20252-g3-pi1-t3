from behave import when, then
from pages.navbar_page import NavBar
from pages.schedule_page import SchedulePage

@when("I go to the schedule page from the menu")
def step_go_schedule(context):
    NavBar(context.driver).go_to_schedule()

@then('I should see the "Semana" button')
def step_see_week_button(context):
    assert SchedulePage(context.driver).assert_week_button_visible(), "No se encontró el botón 'Semana' (id=btn-week)."
