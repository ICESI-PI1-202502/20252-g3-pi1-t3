from behave import when, then
from pages.navbar_page import NavBar
from pages.tournaments_page import TournamentsPage
from pages.tournaments_detail_page import TournamentDetailPage
from pages.join_team_page import JoinTeamPage
from pages.manage_team_page import ManageTeamPage

@when('I join the team "{team_visible_text}"')
def step_impl(context, team_visible_text):
    # Estamos en detalles del torneo
    details = TournamentDetailPage(context.driver)
    details.go_to_join_team()

    join = JoinTeamPage(context.driver)
    join.select_team_by_name(team_visible_text)
    join.submit()

@when("I open my team management")
def step_impl(context):
    details = TournamentDetailPage(context.driver)
    details.go_to_manage_my_team()

@then('I should see the manage team header for "{team_visible_text}"')
def step_impl(context, team_visible_text):
    manage = ManageTeamPage(context.driver)
    assert manage.header_contains_team(team_visible_text), \
        f"No aparece el encabezado con el equipo: {team_visible_text}"
