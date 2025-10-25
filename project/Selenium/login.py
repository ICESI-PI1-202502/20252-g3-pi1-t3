import os
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
import time
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
#
from selenium.webdriver.chrome.service import Service
#
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException, WebDriverException, StaleElementReferenceException


from selenium.webdriver.support import expected_conditions as EC


ruta = os.getcwd()
print(ruta)
##//div[@role='dialog']//div[1]//div[2]

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
#, ancho=500, alto=1000
def crear_driver(detach=True):
    """Configura y retorna una instancia del navegador Chrome."""
    opciones = webdriver.ChromeOptions()
    if detach:
        opciones.add_experimental_option("detach", True)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opciones)
    #driver.set_window_size(ancho, alto)
    return driver

def abrir_instagram(driver):
    driver.get("http://127.0.0.1:8000/")
    time.sleep(5)  # Puedes reemplazar con WebDriverWait si quieres mayor robustez

def iniciar_sesion(driver, username, password):

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )

        username_input = driver.find_element(By.NAME, "username")
        username_input.click()
        username_input.send_keys(username)
        time.sleep(2)

        password_input = driver.find_element(By.NAME, "password")
        password_input.click()
        password_input.send_keys(password)
        time.sleep(2)

        boton_login = driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[3]/button')
        boton_login.click()
        print(" Intentando iniciar sesión...")
        time.sleep(8)  # Esperar carga post-login
    except Exception as e:
        print(f" Error durante el login: {e}")


if __name__ == "__main__":
    # Crear el driver
    driver = crear_driver()

    # Abrir la página
    abrir_instagram(driver)

    # Iniciar sesión (reemplaza con tus credenciales reales)
    iniciar_sesion(driver, "TU_USUARIO", "TU_CONTRASEÑA")
