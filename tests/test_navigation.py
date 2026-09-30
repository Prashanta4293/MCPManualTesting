import allure
import pytest
from pages.data import ROWS, case_name
from pages.navigation_page import NavigationPage

@pytest.mark.regression
@pytest.mark.parametrize('case', [r for r in ROWS if r['Test Case ID'].startswith('NAV-')], ids=case_name)
def test_navigation(case, page, audit):
    destination = NavigationPage(page,audit)
    with allure.step('Start from home and open the recorded header menu'):
        destination.open()
    with allure.step(case['Test Scenario']):
        target = destination.navigate(case)
    with allure.step('Verify URL, title, heading, breadcrumb, content, images and browser diagnostics'):
        destination.verify(case,target)
    audit.finish()
