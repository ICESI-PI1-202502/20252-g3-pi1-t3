from behave import when, then
from pages.navbar_page import NavBar
from pages.personal_schedule_page import PersonalSchedulePage

@when("I go to the personal schedule page from the menu")
def step_go_personal_schedule(context):
    NavBar(context.driver).go_to_schedule()

@when('I open the personal schedule event "{title}"')
def step_open_personal_event(context, title):
    PersonalSchedulePage(context.driver).open_event_by_title(title)

@then('I should see the personal schedule modal title detail "{title}"')
def step_assert_personal_modal_title(context, title):
    PersonalSchedulePage(context.driver).assert_modal_title_detail(title)
