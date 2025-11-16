import re
from behave import when, then
from pages.navbar_page import NavBar
from pages.psu_projects_page import PSUProjectsPage
from pages.psu_project_form_page import PSUProjectFormPage  # <- actualizado




@when('I fill the PSU project with name "{name}", capacity {cap:d} and description:')
def step_fill_basic_info(context, name, cap):
    desc = context.text or ""
    form = PSUProjectFormPage(context.driver)
    form.fill_name_capacity_desc(name=name, capacity=str(cap), description=desc)
    context._psu_form = form

@when('I set the PSU project dates start "{start}" end "{end}" and submit')
def step_set_dates_and_submit(context, start, end):
    form = context._psu_form
    form.set_dates(start, end)
    form.submit()
    context._psu_alert = form.wait_danger_alert_text(timeout=10)

@then("I should see a PSU date error alert")
def step_assert_date_error(context):
    msg = (context._psu_alert or "").strip().lower()
    ok = ("fecha de inicio" in msg and "posterior" in msg and "fecha fin" in msg) or \
         re.search(r"inicio\s+no\s+puede\s+ser\s+posterior\s+a\s+la?\s*fecha\s+fin", msg or "")
    assert ok, f"Mensaje de alerta inesperado: '{context._psu_alert}'"
