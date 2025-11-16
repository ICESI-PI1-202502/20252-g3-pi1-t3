from behave import when, then
from pages.navbar_page import NavBar
from pages.psu_projects_page import PSUProjectsPage

@when("I go to PSU projects from the menu")
def step_go_psu(context):
    NavBar(context.driver).go_to_psu_projects()

@when('I search PSU projects by text "{query}"')
def step_search_psu(context, query):
    PSUProjectsPage(context.driver).search(query)

@then('I should see a PSU project titled "{expected}"')
def step_assert_psu_title(context, expected):
    PSUProjectsPage(context.driver).assert_result_title_present(expected)
