# features/environment.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def before_all(context):
    # Ajusta si tu server Django corre en otro host/puerto
    context.base_url = "http://127.0.0.1:8000/"

def before_scenario(context, scenario):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # Si quieres que la ventana no se cierre al finalizar manualmente:
    # options.add_experimental_option("detach", True)
    context.driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    context.driver.implicitly_wait(5)

def after_scenario(context, scenario):
    # Cierra el navegador al terminar cada escenario
    context.driver.quit()
