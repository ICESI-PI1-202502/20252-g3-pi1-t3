from behave import when, then
from pages.navbar_page import NavBar
from pages.unified_schedule_page import UnifiedSchedulePage

@when("I go to the unified schedule page from the menu")
def step_go_unified_schedule(context):
    NavBar(context.driver).go_to_unified_schedule()

@when('I open the unified schedule event "{title}"')
def step_open_event(context, title):
    UnifiedSchedulePage(context.driver).open_event_by_title(title)

@then('I should see the unified schedule modal title "{title}"')
def step_assert_modal_title(context, title):
    UnifiedSchedulePage(context.driver).assert_modal_title(title)
