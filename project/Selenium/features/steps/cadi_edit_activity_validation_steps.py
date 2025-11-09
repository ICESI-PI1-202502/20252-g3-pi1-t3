from behave import when, then
from pages.cadi_activities_list_page import CADIActivitiesListPage
from pages.cadi_activity_form_page import CADIActivityFormPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from unicodedata import normalize


def _norm(s: str) -> str:
    # normaliza, quita acentos y puntos finales
    s = normalize("NFKD", s or "").encode("ascii","ignore").decode("ascii")
    return s.strip().lower().rstrip('.')


@when('I click edit on CADI activity "{title}"')
def step_click_edit(context, title):
    CADIActivitiesListPage(context.driver).open_edit_for_activity(title)
    # Espera rápida a que aparezca el formulario de edición
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='nombre']"))
    )

@when("I clear the CADI activity name and try to update")
def step_clear_and_submit(context):
    form = CADIActivityFormPage(context.driver)
    is_valid, msg = form.clear_name_and_submit_expect_required()
    context._cadi_is_valid = is_valid
    context._cadi_msg = msg

@then("I should see a native required warning on the CADI activity form")
def step_assert_warning(context):
    assert context._cadi_is_valid is False, "El form no debería ser válido con nombre vacío."

    msg = _norm(context._cadi_msg)
   
    synonyms = [
        "rellene este campo",   
        "completa este campo",   
        "complete este campo",   
        "este campo es obligatorio",
        "campo obligatorio",
        "fill out this field",
        "please fill",
        "required"
    ]
    ok = any(s in msg for s in synonyms)
    assert ok, f"Mensaje inesperado: '{context._cadi_msg}'"
