from behave import given, when, then
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from pages.login_page import LoginPage

#Ejecutar el proyecto primero, ir a selenium (cd selenium)
@given("I am on the login page")
def step_impl(context):
    service = Service(executable_path="chromedriver.exe")  # en project/Selenium/
    context.driver = webdriver.Chrome(service=service)
    context.driver.maximize_window()
    context.login_page = LoginPage(context.driver)
    context.login_page.open("http://127.0.0.1:8000/")

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

def after_scenario(context, scenario):
    if hasattr(context, "driver"):
        context.driver.quit()