import allure
import pytest
from pages.data import ROWS, case_name
from pages.header_page import HeaderPage

CASES = [r for r in ROWS if not r['Test Case ID'].startswith(('NAV-','LIMIT-','ACCOUNT-'))]

@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.parametrize('case', CASES, ids=case_name)
def test_header(case, page, audit):
    home = HeaderPage(page,audit)
    with allure.step('Load home in a fresh anonymous browser context'):
        home.open()
    with allure.step(case['Test Scenario']):
        home.verify_case(case)
    audit.finish()
