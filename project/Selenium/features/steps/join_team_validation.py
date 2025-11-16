from behave import when, then
from pages.tournaments_detail_page import TournamentDetailPage
from pages.join_team_page import JoinTeamPage

@when("I open the join team form")
def step_open_join_form(context):
    details = TournamentDetailPage(context.driver)
    details.go_to_join_team()
    context.join_page = JoinTeamPage(context.driver)

@when("I submit the empty join team form")
def step_submit_empty_join(context):
    context.is_valid, context.validation_msg = context.join_page.submit_expect_required_errors()

@then("I should see required warnings on the join team form")
def step_assert_required_join(context):
    # El form NO debe ser válido
    assert context.is_valid is False, (
        f"El formulario resultó válido al enviar vacío. validationMessage='{context.validation_msg}'"
    )

    # Validación suave del mensaje (varía por navegador/idioma)
    msg = (context.validation_msg or "").strip().lower()
    if msg:
        ok = any(s in msg for s in [
            "selecciona un elemento de la lista",   # Chrome ES (tu caso)
            "seleccione un elemento de la lista",
            "seleccione un elemento",
            "please select",
            "select an item",
            "required",
        ])
        assert ok, f"Mensaje inesperado: '{context.validation_msg}'"
