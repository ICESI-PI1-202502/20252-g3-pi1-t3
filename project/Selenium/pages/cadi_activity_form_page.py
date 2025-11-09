from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage

class CADIActivityFormPage(BasePage):
    INPUT_NOMBRE = (By.CSS_SELECTOR, "input[name='nombre']")
    SELECT_TIPO  = (By.CSS_SELECTOR, "select[name='tipo']")
    INPUT_AFORO  = (By.CSS_SELECTOR, "input[name='aforo']")
    TEXT_DESC    = (By.CSS_SELECTOR, "textarea[name='descripcion']")
    SELECT_REQ   = (By.CSS_SELECTOR, "select[name='requiere_inscripcion']")
    # Sirve tanto para “Crear actividad” como para “Actualizar”
    BTN_CREAR    = (By.CSS_SELECTOR, "button.greenBotton_White[name='action'][value='confirm'], button.greenBotton_White")

    def fill_and_submit(self, name, tipo, aforo, descripcion, requiere_inscripcion):
        self.type(self.INPUT_NOMBRE, name)

        select_tipo = self.is_present(self.SELECT_TIPO, timeout=15)
        try:
            Select(select_tipo).select_by_visible_text(tipo)
        except Exception:
            wanted = (tipo or "").strip().lower()
            for opt in select_tipo.find_elements(By.TAG_NAME, "option"):
                if opt.text.strip().lower() == wanted:
                    opt.click()
                    break

        if aforo:
            self.type(self.INPUT_AFORO, str(aforo))
        if descripcion:
            self.type(self.TEXT_DESC, descripcion)

        if requiere_inscripcion:
            sel_req = self.is_present(self.SELECT_REQ, timeout=15)
            txt = requiere_inscripcion.strip()
            try:
                Select(sel_req).select_by_visible_text(txt)
            except Exception:
                Select(sel_req).select_by_value('si' if txt.lower().startswith('s') else 'no')

        self.scroll_into_view(self.BTN_CREAR, timeout=15)
        self.retry_click(self.BTN_CREAR, timeout=15)

    def clear_name_and_submit_expect_required(self):
        nombre_el = self.is_present(self.INPUT_NOMBRE, timeout=15)
        try:
            nombre_el.clear()
        except Exception:
            pass

        # asegurar vacío + eventos
        self.driver.execute_script("""
            arguments[0].value = '';
            arguments[0].dispatchEvent(new Event('input', {bubbles:true}));
            arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
        """, nombre_el)

        self.scroll_into_view(self.BTN_CREAR)
        self.retry_click(self.BTN_CREAR, timeout=12)

        is_valid = self.driver.execute_script("return document.querySelector('form').checkValidity();")
        validation_msg = self.driver.execute_script("return arguments[0].validationMessage;", nombre_el)
        return is_valid, (validation_msg or "")

    def submit_with_negative_aforo_expect_min_error(self, name, tipo, aforo, requiere_inscripcion, descripcion=""):
        # nombre (requerido)
        self.type(self.INPUT_NOMBRE, name)

        # tipo (requerido)
        select_tipo = self.is_present(self.SELECT_TIPO, timeout=15)
        try:
            Select(select_tipo).select_by_visible_text(tipo)
        except Exception:
            wanted = (tipo or "").strip().lower()
            for opt in select_tipo.find_elements(By.TAG_NAME, "option"):
                if opt.text.strip().lower() == wanted:
                    opt.click()
                    break

        # aforo negativo para gatillar min=1
        if aforo is not None:
            self.type(self.INPUT_AFORO, str(aforo))

        # descripción (opcional)
        if descripcion:
            self.type(self.TEXT_DESC, descripcion)

        # requiere_inscripcion (requerido)
        if requiere_inscripcion:
            sel_req = self.is_present(self.SELECT_REQ, timeout=15)
            txt = requiere_inscripcion.strip()
            try:
                Select(sel_req).select_by_visible_text(txt)
            except Exception:
                Select(sel_req).select_by_value('si' if txt.lower().startswith('s') else 'no')

        # intentar enviar
        self.scroll_into_view(self.BTN_CREAR, timeout=15)
        self.retry_click(self.BTN_CREAR, timeout=15)

        # leer validez y mensaje del input number[min=1]
        is_valid = self.driver.execute_script("return document.querySelector('form').checkValidity();")
        aforo_el = self.is_present(self.INPUT_AFORO, timeout=10)
        validation_msg = self.driver.execute_script("return arguments[0].validationMessage;", aforo_el)
        return is_valid, (validation_msg or "")
