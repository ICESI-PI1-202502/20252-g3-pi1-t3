from behave import when, then
from unicodedata import normalize
from pages.cadi_activity_form_page import CADIActivityFormPage

def _norm(s: str) -> str:
    s = normalize("NFKD", s or "").encode("ascii","ignore").decode("ascii")
    return s.strip().lower().rstrip('.')

@when("I try to create the CADI activity with the form empty")
def step_try_create_empty(context):
    # Usa el helper que ya tienes para vaciar 'nombre' y enviar
    form = CADIActivityFormPage(context.driver)
    is_valid, msg = form.clear_name_and_submit_expect_required()
    context._cadi_is_valid = is_valid
    context._cadi_msg = msg

@then("I should see a native required warning on the CADI activity creation form")
def step_assert_required_msg(context):
    assert context._cadi_is_valid is False, "El form no debería ser válido con campos requeridos vacíos."
    msg = _norm(context._cadi_msg)
    variants = [
        "rellene este campo",    # ES (Chrome/Edge/Firefox)
        "completa este campo",   # ES informal
        "complete este campo",   # ES formal
        "campo obligatorio",
        "fill out this field",   # EN
        "please fill",
        "required"
    ]
    assert any(v in msg for v in variants), f"Mensaje inesperado: '{context._cadi_msg}'"
