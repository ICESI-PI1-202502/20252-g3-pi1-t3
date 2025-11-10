from behave import when, then
from unicodedata import normalize
from pages.cadi_activity_form_page import CADIActivityFormPage
from unicodedata import normalize


def _norm(s: str) -> str:
    s = normalize("NFKD", s or "").encode("ascii","ignore").decode("ascii")
    return s.strip().lower().rstrip('.')

@when('I try to create a CADI activity with name "{name}" type "{tipo}" negative capacity {cap:d} and requires "{req}"')
def step_create_with_negative_capacity(context, name, tipo, cap, req):
    form = CADIActivityFormPage(context.driver)
    is_valid, msg = form.submit_with_negative_aforo_expect_min_error(
        name=name,
        tipo=tipo,
        aforo=cap,               # e.g., -10
        requiere_inscripcion=req,
        descripcion=""           # opcional
    )
    context._is_valid = is_valid
    context._msg = msg

@then("I should see a min-capacity warning on the CADI activity form")
def step_assert_min_warning(context):
    assert context._is_valid is False, "El form no debería ser válido con aforo negativo."
    msg = _norm(context._msg)
    variants = [
        "debe ser mayor o igual que 1",
        "debe ser superior o igual a 1",  # <— NUEVA variante
        "must be greater than or equal to 1",
        "value must be greater than or equal to 1",
        "range underflow"
    ]
    assert any(v in msg for v in variants), f"Mensaje inesperado: '{context._msg}'"
