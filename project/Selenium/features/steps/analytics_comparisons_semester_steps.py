from behave import when, then
from pages.analytics_comparisons_page import AnalyticsComparisonsPage

@when("I filter by semester 2 grouped by Facultad and update")
def step_filter_sem2(context):
    page = AnalyticsComparisonsPage(context.driver)
    page.choose_semester_specific()
    page.pick_semester("2")
    page.set_grouping_facultad()
    page.click_update()

@then("I should see the results heading for semester 2 grouped by Facultad")
def step_assert_heading(context):
    AnalyticsComparisonsPage(context.driver).assert_results_sem2_group_facultad()

