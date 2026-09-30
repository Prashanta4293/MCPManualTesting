import allure
import pytest
from pages.data import ROWS, LOGIN_CASE, case_name
from pages.visitor_login_page import VisitorLoginPage

@pytest.mark.visitor_login
@pytest.mark.regression
@pytest.mark.parametrize('case', [r for r in ROWS if r['Test Case ID'].startswith('ACCOUNT-')], ids=case_name)
def test_visitor_account_controls(case, page, audit):
    visitor = VisitorLoginPage(page,audit)
    with allure.step('Load home in a fresh anonymous browser context'):
        visitor.open()
    with allure.step(case['Test Scenario']):
        visitor.verify_account_case(case)
    audit.finish()

@pytest.mark.visitor_login
@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.flaky(reruns=0)
@pytest.mark.parametrize('case', [LOGIN_CASE], ids=case_name)
def test_positive_visitor_login(case, page, audit):
    completed = False
    with allure.step('Headed login using private credentials and human CAPTCHA; recordings disabled'):
        try:
            visitor = VisitorLoginPage(page,audit)
            visitor.open()
            completed = visitor.positive_login()
        except Exception:
            raise AssertionError('Positive Visitor login failed; credential-bearing diagnostic details suppressed.') from None
    if not completed:
        pytest.skip('BLOCKED: No manual CAPTCHA entered within 120 seconds; login was not submitted.')
