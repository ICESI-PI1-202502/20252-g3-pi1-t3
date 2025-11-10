from behave import when, then
from pages.navbar_page import NavBar
from pages.personal_schedule_page import PersonalSchedulePage

@when("I delete the opened personal schedule event with confirmation")
def step_delete_opened_event(context):
    PersonalSchedulePage(context.driver).delete_opened_event_with_confirmation()

@then('I should see the personal schedule deletion toast for "{title}"')
def step_assert_deletion_toast(context, title):
    PersonalSchedulePage(context.driver).assert_deletion_toast_for_title(title)
