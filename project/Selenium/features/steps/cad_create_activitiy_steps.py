from behave import when, then
from pages.cadi_home_entry_page import CADIHomeEntryPage
from pages.cadi_categories_page import CADICategoriesPage
from pages.cadi_activities_list_page import CADIActivitiesListPage
from pages.cadi_activity_form_page import CADIActivityFormPage

@when("I open CADI management from the home card")
def step_open_cadi_from_home(context):
    CADIHomeEntryPage(context.driver).open_cadi_management()

@when('I open the CADI category "{category_name}"')
def step_open_cadi_category(context, category_name):
    CADICategoriesPage(context.driver).open_category_by_name(category_name)

@when('I click "Agregar actividad" in the CADI list')
def step_click_add_activity(context):
    CADIActivitiesListPage(context.driver).click_add_activity()

@when('I create a CADI activity named "{name}" of type "{tipo}" with capacity {cap:d}, requires "{req}" and description:')
def step_create_activity(context, name, tipo, cap, req):
    desc = context.text or ""
    page = CADIActivityFormPage(context.driver)
    page.fill_and_submit(
        name=name,
        tipo=tipo,
        aforo=str(cap),
        descripcion=desc,
        requiere_inscripcion=req
    )

@then('I should see the CADI activity titled "{expected_title}" in the list')
def step_see_created_activity(context, expected_title):
    CADIActivitiesListPage(context.driver).assert_activity_title_present(expected_title)
