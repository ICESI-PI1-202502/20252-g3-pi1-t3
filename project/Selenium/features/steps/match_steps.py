from behave import when, then
from pages.tournaments_detail_page import TournamentDetailPage
from pages.match_create_page import MatchCreatePage

@when("I open the match creation form")
def step_open_match_form(context):
    details = TournamentDetailPage(context.driver)
    details.go_to_register_match()
    context.match_form = MatchCreatePage(context.driver)

@when('I register a match: team A "{team_a}", team B "{team_b}", start "{start_dt}", end "{end_dt}", place "{place}"')
def step_register_match(context, team_a, team_b, start_dt, end_dt, place):
    context.match_form.fill_form(team_a, team_b, start_dt, end_dt, place)
    context.match_form.submit()

@then('I should see the match "{pair_text}" with place "{place_text}"')
def step_verify_match(context, pair_text, place_text):
    details = TournamentDetailPage(context.driver)

    # separar "Equipo A vs Equipo B"
    if " vs " in pair_text:
        team_a, team_b = [s.strip() for s in pair_text.split(" vs ", 1)]
    else:
        team_a, team_b = pair_text.strip(), ""

    ok = details.match_is_listed(team_a, team_b, place_text.strip(), timeout=25)
    assert ok, (
        f"No se encontró el partido '{pair_text}' con lugar '{place_text}' en la tabla."
    )
