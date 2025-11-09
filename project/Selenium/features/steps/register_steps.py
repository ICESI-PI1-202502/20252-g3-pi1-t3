from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from pages.register_page import RegisterPage
import time
import psycopg2



# =========================
# CONFIGURACIÓN DEL DRIVER
# =========================
def crear_driver(detach=True):
    options = webdriver.ChromeOptions()
    if detach:
        options.add_experimental_option("detach", True)
    service = Service(executable_path="chromedriver.exe")  # en project/Selenium/
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    return driver


def eliminar_usuario_existente():
    """Elimina el usuario de prueba antes o después de ejecutar CF-A3 o CF-A4."""
    try:
        conn = psycopg2.connect(
            host="aws-1-us-east-2.pooler.supabase.com",
            database="postgres",
            user="postgres.xlknciyujekwbhysmamn",
            password="h9TZan8icTf3hjsn",
            port="5432",
            sslmode="require"
        )
        cur = conn.cursor()
        cur.execute("DELETE FROM participantes WHERE id_participante = %s;", ("1122334455",))
        cur.execute("DELETE FROM auth_user WHERE email = %s;", ("usuario@correo.com",))
        conn.commit()
        cur.close()
        conn.close()
        print(" Usuario de prueba eliminado (si existía).")
    except Exception as e:
        print(f" Error al eliminar usuario: {e}")


# =========================
# STEPS DEFINITIONS
# =========================
@given('I am on the register page')
def step_impl(context):
    context.driver = crear_driver()
    context.driver.get("http://127.0.0.1:8000/")
    eliminar_usuario_existente()
    time.sleep(2)
    register_link = WebDriverWait(context.driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Registrarse')]"))
    )
    register_link.click()
    time.sleep(2)


@when('I register with cedula "{cedula}", nombre "{nombre}", email "{email}" and password "{password}"')
def step_impl(context, cedula, nombre, email, password):
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.NAME, "cedula"))
    )
    context.driver.find_element(By.NAME, "cedula").send_keys(cedula)
    context.driver.find_element(By.NAME, "nombre_completo").send_keys(nombre)
    context.driver.find_element(By.NAME, "email").send_keys(email)

    # Si la contraseña no está vacía
    if password:
        context.driver.find_element(By.NAME, "password").send_keys(password)

    boton_registrar = context.driver.find_element(
        By.XPATH, "//form//*[contains(., 'Registrarse')]"
    )
    boton_registrar.click()
    time.sleep(3)


#  Step alternativo para cuando la contraseña está vacía
@when('I register with cedula "{cedula}", nombre "{nombre}", email "{email}" and password ""')
def step_impl_empty_password(context, cedula, nombre, email):
    # Reutiliza el mismo flujo pero sin enviar contraseña
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.NAME, "cedula"))
    )
    context.driver.find_element(By.NAME, "cedula").send_keys(cedula)
    context.driver.find_element(By.NAME, "nombre_completo").send_keys(nombre)
    context.driver.find_element(By.NAME, "email").send_keys(email)
    # No escribir contraseña
    boton_registrar = context.driver.find_element(
        By.XPATH, "//form//*[contains(., 'Registrarse')]"
    )
    boton_registrar.click()
    time.sleep(3)

@then('I should see a success message "{mensaje}"')
def step_impl(context, mensaje):
    mensaje_exito = WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{mensaje}')]"))
    )
    assert mensaje_exito is not None
    print(" Registro exitoso confirmado.")
    context.driver.quit()


@then('I should see a required field error')
def step_impl(context):
    mensaje_error = WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'This field is required.')]")
        )
    )
    assert mensaje_error is not None
    print(" Validación correcta: el sistema mostró el mensaje esperado.")
    context.driver.quit()
