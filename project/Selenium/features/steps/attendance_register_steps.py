from behave import when, then
from pages.navbar_page import NavBar
from pages.analytics_menu_page import AnalyticsMenuPage
from pages.attendance_management_page import AttendanceManagementPage
from pages.register_attendance_page import RegisterAttendancePage

@when("I go to attendance management from the analytics menu")
def step_go_attendance_mgmt(context):
    # go_to_analytics_reports ya abre el menú por dentro
    NavBar(context.driver).go_to_analytics_reports()
    AnalyticsMenuPage(context.driver).go_to_attendance_mgmt()

@when("I open the individual attendance register")
def step_open_register(context):
    AttendanceManagementPage(context.driver).open_register_individual()

@when('I submit attendance for activity "Accesorios & Tejidos" with ids text "MALOMALO"')
def step_submit_invalid_ids(context):
    page = RegisterAttendancePage(context.driver)
    context._warn_text = page.fill_and_submit("Accesorios & Tejidos", "MALOMALO")

@then("I should see a warning alert indicating errors in attendance register")
def step_assert_warning(context):
    txt = (context._warn_text or "").lower()
    assert "errores" in txt or "error" in txt, f"Alerta inesperada: '{context._warn_text}'"
