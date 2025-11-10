from behave import when, then
from pages.navbar_page import NavBar
from pages.tournaments_page import TournamentsPage
from pages.tournaments_detail_page import TournamentDetailPage
from pages.team_create_page import TeamCreatePage

@when("I open the team creation form")
def step_impl(context):
    details = TournamentDetailPage(context.driver)
    details.go_to_create_team()
    context.team_form = TeamCreatePage(context.driver)

@when("I submit the empty team form")
def step_impl(context):
    context.is_valid, context.validation_msg = context.team_form.submit_expect_required_errors()

@then("I should see required warnings on the team form")
def step_impl(context):
    # El form no debe pasar validación, y debe haber un mensaje nativo
    assert context.is_valid is False
    assert context.validation_msg.strip() != ""   # p.ej. "Rellene este campo."
