from behave import when, then
from pages.navbar_page import NavBar
from pages.tournaments_page import TournamentsPage
from pages.tournaments_detail_page import TournamentDetailPage
from pages.team_create_page import TeamCreatePage

@when("I go to tournaments from the menu")
def step_impl(context):
    nav = NavBar(context.driver)
    nav.open_menu()
    nav.go_to_tournaments()

@when('I open tournament details for "{title}"')
def step_impl(context, title):
    tournaments = TournamentsPage(context.driver)
    tournaments.open_details_for_title(title)

@when('I create a team named "{name}" with responsible "{resp_id}", discipline "{disc}", min {minc:d} and max {maxc:d}')
def step_impl(context, name, resp_id, disc, minc, maxc):
    details = TournamentDetailPage(context.driver)
    details.go_to_create_team()

    form = TeamCreatePage(context.driver)
    form.fill_form(
        nombre_equipo=name,
        responsable_id=resp_id,
        disciplina=disc,
        capacidad_min=minc,
        capacidad_max=maxc
    )
    form.submit()

@then('I should see the team "{team_name}" in the tournament details')
def step_impl(context, team_name):
    details = TournamentDetailPage(context.driver)
    assert details.team_name_is_listed(team_name), f'No se encontró el equipo: {team_name}'
