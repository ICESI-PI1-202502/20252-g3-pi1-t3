from behave import when, then
from pages.navbar_page import NavBar
from pages.psu_projects_page import PSUProjectsPage
from pages.psu_project_detail_page import PSUProjectDetailPage
import unicodedata

def _norm(s: str) -> str:
    return " ".join(unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode("ascii").lower().split())

@when('I open PSU project details for "{title}"')
def step_open_details_for_title(context, title):
    PSUProjectsPage(context.driver).open_details_for_title(title)

@when("I enroll in the PSU project")
def step_enroll_psu(context):
    msg = PSUProjectDetailPage(context.driver).enroll_and_wait_success()
    context._psu_enroll_msg = msg

@then("I should see a PSU enrollment success alert")
def step_assert_success(context):
    m = _norm(getattr(context, "_psu_enroll_msg", ""))
    assert ("inscripcion" in m and "exito" in m) or ("inscripción" in getattr(context, "_psu_enroll_msg","").lower()), \
        f"Success alert not found or unexpected text: '{context._psu_enroll_msg}'"
