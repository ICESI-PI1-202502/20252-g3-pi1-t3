# CF-A1
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


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


@pytest.fixture
def driver():
    driver = crear_driver()
    driver.get("http://127.0.0.1:8000/")
    yield driver
    driver.quit()


# =========================
# FUNCIONES DE APOYO
# =========================
def iniciar_sesion(driver, username, password):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "cedula"))
        )

        driver.find_element(By.NAME, "cedula").send_keys(username)
        time.sleep(3)
        driver.find_element(By.NAME, "password").send_keys(password)
        time.sleep(3)
        driver.find_element(By.ID, "loginButton").click()
        time.sleep(3)
        print(f" Intentando iniciar sesión con usuario={username}")
        time.sleep(3)

    except Exception as e:
        print(f" Error durante el login: {e}")


# =========================
# CASOS DE PRUEBA
# =========================
def test_login_exitoso(driver):
    """CF-A1.1 - Login exitoso"""
    iniciar_sesion(driver, "123", "123")

    
    WebDriverWait(driver, 10).until( 
        EC.presence_of_element_located((By.XPATH, "//*[contains(button, 'Calendario')]"))
    )
    assert "Calendario" in driver.page_source
    print(" Login exitoso comprobado correctamente.")


def test_login_incorrecto(driver):
    """CF-A1.2 - Login fallido: Contraseña incorrecta."""
    iniciar_sesion(driver, "123", "456")

    # Espera mensaje de error
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Contraseña incorrecta.')]"))
    )
    assert "Contraseña incorrecta." in driver.page_source
    print(" Mensaje de error mostrado correctamente.")


def test_login_usuario_inexistente(driver):
    """CF-A1.3 - Login fallido: usuario no registrado"""
    iniciar_sesion(driver, "6673", "clave123")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'El usuario con esa cédula no existe.')]"))
    )
    assert "El usuario con esa cédula no existe." in driver.page_source
    print(" Mensaje de usuario no encontrado verificado.")


# =========================
# CASO DE PRUEBA CF-A5
# =========================
@pytest.mark.functional
def test_login_admin_exitoso(driver):
    """
    CF-A5: Inicio de sesión exitoso como administrador.
    Escenario: Acceso con credenciales válidas de rol administrador.
    Precondición: Existe un usuario con rol 'Administrador' registrado.
    """
    # Credenciales del administrador
    admin_cedula = "1110287841"
    admin_password = "123"

    # Iniciar sesión con las credenciales del administrador
    iniciar_sesion(driver, admin_cedula, admin_password)

    # Esperar redirección al panel de administración
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Gestionar actividades')]")
        )
    )

    # Verificar que el panel de administración esté visible
    assert "Gestionar actividades" in driver.page_source
    print(" Inicio de sesión exitoso como administrador confirmado.")
    