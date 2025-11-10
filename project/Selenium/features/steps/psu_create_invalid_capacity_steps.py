from behave import when, then
from pages.navbar_page import NavBar
from pages.psu_projects_admin_page import PSUProjectsAdminPage
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
    PSUProjectsAdminPage(context.driver).open_create_form()

@when('I try to create a PSU project named "{name}" with negative capacity -1')
def step_fill_negative_capacity(context, name):
    is_valid, msg = PSUProjectFormPage(context.driver).submit_with_negative_aforo_expect_min_error(
        nombre=name, aforo_neg=-1
    )
    context._psu_is_valid = is_valid
    context._psu_msg = (msg or "").strip()

@then("I should see a min-capacity warning on the PSU project form")
def step_assert_min_warning(context):
    assert context._psu_is_valid is False, "El form no debería ser válido con aforo negativo."
    m = _norm(context._psu_msg)

    # Frases posibles según navegador/locale (Chrome/Firefox/Edge, es/en)
    candidates = [
        "el valor debe ser superior o igual a 0",
        "el valor debe ser mayor o igual a 0",
        "introduzca un valor mayor o igual que 0",
        "introduzca un valor superior o igual que 0",
        "mayor o igual que 0",
        "mayor o igual a 0",
        "greater than or equal to 0",
        "no less than 0",
        ">= 0",
    ]
    ok = any(c in m for c in candidates)
    assert ok, f"Mensaje inesperado: '{context._psu_msg}'"
