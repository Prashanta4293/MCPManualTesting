import allure
import pytest
import json
from pathlib import Path
from pages.data import ROWS, LOGIN_CASE, case_name
from pages.visitor_login_page import VisitorLoginPage

WORKBOOK_CASES = json.loads((Path(__file__).resolve().parents[1]/'data/visitor_login_data.json').read_text(encoding='utf-8'))['cases']

def workbook_parameters():
    for case in sorted(WORKBOOK_CASES,key=lambda c:(not c['negative'],int(c['Test Case ID'][2:]))):
        marks = [pytest.mark.visitor_login,pytest.mark.regression]
        if case['negative']:
            marks.append(pytest.mark.negative)
        if case['automation']=='Semi-automated':
            marks.extend([pytest.mark.manual_captcha,pytest.mark.flaky(reruns=0)])
        if case['Test Case ID'] in ('TC36','TC39'):
            marks.append(pytest.mark.positive)
        if case['Test Case ID'] in ('TC16','TC17','TC19','TC20','TC24','TC28','TC38'):
            marks.append(pytest.mark.smoke)
        yield pytest.param(case,id=case_name(case),marks=marks)


@pytest.mark.parametrize('case',list(workbook_parameters()))
def test_workbook_visitor_login(case, visitor_session, visitor_audit, captcha_confirmation, request):
    visitor = VisitorLoginPage(visitor_session,visitor_audit)
    with allure.step('Open staging home and access Visitor Login through the profile icon'):
        visitor.open()
        visitor.open_login()
    with allure.step(case['Steps']):
        if case['automation']=='Semi-automated':
            from utilities.visitor_fixtures import LOGIN_ENV
            trace = Path(request.config.getoption('--visitor-evidence-dir')).resolve()/case['Test Case ID']/'pre-credential-trace.zip'
            try:
                visitor.attended_workbook_login(case,LOGIN_ENV,captcha_confirmation,trace)
            except pytest.skip.Exception:
                raise
            except Exception:
                visitor.record_private_login_diagnosis()
                raise AssertionError('Attended Visitor Login expectation failed; credential-bearing details suppressed. Review sanitized evidence.') from None
        else:
            visitor.verify_workbook_case(case)

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
