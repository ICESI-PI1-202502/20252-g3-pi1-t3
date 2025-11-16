# features/environment.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def before_all(context):
    context.base_url = "http://127.0.0.1:8000/"

def before_scenario(context, scenario):
    opts = Options()
    opts.add_argument("--start-maximized")
    # opcional, acelera cargas pesadas:
    # opts.set_capability("pageLoadStrategy", "eager")
    context.driver = webdriver.Chrome(options=opts)
    context.driver.set_page_load_timeout(25)
    context.driver.implicitly_wait(0)  # usa esperas explícitas en las pages

def after_scenario(context, scenario):
    if getattr(context, "driver", None):
        context.driver.quit()
