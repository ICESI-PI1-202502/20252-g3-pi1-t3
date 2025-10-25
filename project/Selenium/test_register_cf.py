# CF-A3
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import psycopg2

# =========================
# CONFIGURACIÓN DEL DRIVER
# =========================
def crear_driver(detach=True):
    opciones = webdriver.ChromeOptions()
    if detach:
        opciones.add_experimental_option("detach", True)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opciones)
    driver.maximize_window()
    return driver

def eliminar_usuario_existente():
    """
    Elimina el usuario de prueba de las tablas 'participantes' y 'auth_user'
    antes o después de ejecutar el test CF-A3.
    """
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

@pytest.fixture
def driver():
    driver = crear_driver()
    driver.get("http://127.0.0.1:8000/")
    yield driver
    driver.quit()


# =========================
# CASO DE PRUEBA CF-A3
# =========================
@pytest.mark.functional
def test_registro_usuario_valido(driver):
    """
    CF-A3: Registro de usuario con datos válidos.
    Escenario: Registro exitoso de un nuevo usuario.
    """
    eliminar_usuario_existente()
    time.sleep(3)
    # 1️ Ingresar al formulario de registro
    register_link = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH,  "//a[contains(., 'Registrarse')]"))
    )
    time.sleep(3)
    register_link.click()
    time.sleep(3)
    # 2️ Completar todos los campos obligatorios
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "cedula"))
    )
    time.sleep(3)
    driver.find_element(By.NAME, "cedula").send_keys("1122334455")
    driver.find_element(By.NAME, "nombre_completo").send_keys("Juan Pérez")
    driver.find_element(By.NAME, "email").send_keys("usuario@correo.com")
    driver.find_element(By.NAME, "password").send_keys("nuevaClave")
    time.sleep(3)
    # 3️ Presionar “Registrar”
    boton_registrar = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//form//*[contains(., 'Registrarse')]"))
    )
    boton_registrar.click()
    time.sleep(3)
    # 4️ Verificar mensaje de éxito
    mensaje_exito = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Usuario registrado con éxito. Ahora puede iniciar sesión.')]")
        )
    )
    time.sleep(3)
    assert mensaje_exito is not None
    print("  Registro exitoso confirmado.")
    time.sleep(3)



# =========================
# CASO DE PRUEBA CF-A4
# =========================
@pytest.mark.functional
def test_error_registro_campo_faltante(driver):
    """
    CF-A4: Error de registro por campo faltante.
    Escenario: Validación de campos obligatorios en registro.
    """
    # Limpiar por si quedó algo de pruebas anteriores
    eliminar_usuario_existente()
    time.sleep(3)

    # 1️ Ingresar al formulario de registro
    register_link = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Registrarse')]"))
    )
    time.sleep(2)
    register_link.click()
    time.sleep(2)

    # 2️ Completar campos, dejando la contraseña vacía
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "cedula"))
    )

    driver.find_element(By.NAME, "cedula").send_keys("1234567890")
    driver.find_element(By.NAME, "nombre_completo").send_keys("Ana Gómez")
    driver.find_element(By.NAME, "email").send_keys("usuario@correo.com")
    # Contraseña vacía (no escribimos nada)

    time.sleep(2)

    # 3️ Presionar “Registrar”
    boton_registrar = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//form//*[contains(., 'Registrarse')]"))
    )
    boton_registrar.click()
    time.sleep(3)

    # 4️ Verificar mensaje de error esperado
    mensaje_error = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'This field is required.')]")
        )
    )

    assert mensaje_error is not None
    print(" Validación correcta: El sistema mostró el mensaje de error esperado.")
