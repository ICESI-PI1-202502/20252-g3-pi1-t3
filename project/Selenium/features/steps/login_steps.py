from behave import given, when, then
from pages.login_page import LoginPage

@given("I am on the login page")
def step_impl(context):
    context.login_page = LoginPage(context.driver)
    context.login_page.open(context.base_url)

@when('I login with username "{cedula}" and password "{password}"')
def step_impl(context, cedula, password):
    context.login_page.iniciar_sesion(cedula, password)

@then("I should see the user calendar")
def step_impl(context):
    assert context.login_page.login_exitoso()

@then("I should see an incorrect password message")
def step_impl(context):
    assert context.login_page.error_contrasena()

@then("I should see a user not found message")
def step_impl(context):
    assert context.login_page.error_usuario()

@then("I should see the admin panel")
def step_impl(context):
    assert context.login_page.login_admin_exitoso(), "Admin link not visible or user lacks admin role."
