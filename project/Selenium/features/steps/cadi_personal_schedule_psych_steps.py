from behave import when, then
from pages.personal_schedule_page import PersonalSchedulePage

@when("I switch to month view in personal schedule")
def step_switch_month(context):
    PersonalSchedulePage(context.driver).click_month_view()

@then('I should see the personal schedule modal source "Creado automáticamente"')
def step_assert_source_auto(context):
    PersonalSchedulePage(context.driver).assert_modal_source_automatic()
