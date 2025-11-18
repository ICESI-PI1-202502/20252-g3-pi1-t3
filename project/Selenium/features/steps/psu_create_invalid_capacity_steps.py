# features/steps/psu_create_invalid_capacity_steps.py
from behave import when, then
from pages.navbar_page import NavBar
from pages.psu_projects_page import PSUProjectsPage
from pages.psu_project_form_page import PSUProjectFormPage
import unicodedata

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().strip().split())

@when("I go to PSU projects (admin) from the menu")
def step_go_psu_admin(context):
    NavBar(context.driver).go_to_psu_projects()

@when('I open the PSU create project form')
def step_open_create_form(context):
    PSUProjectsPage(context.driver).open_create_form()
