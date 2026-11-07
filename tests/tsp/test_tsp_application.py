"""Opt-in positive draft flow. No final submission, including on failure."""
import allure
import os
import sys
import pytest

from pages.tsp_application_page import TspApplicationPage


@pytest.mark.tsp_application
@pytest.mark.positive
@pytest.mark.regression
@pytest.mark.manual_captcha
@pytest.mark.flaky(reruns=0)
@allure.epic('Odisha Tourism')
@allure.feature('TSP Application')
@allure.story('Populate all applicable fields through preview, without final submission')
@allure.title('TSP-POS-001 All eight sections, mandatory and optional fields, no submit')
@allure.description('Attended Chromium login using private TSP environment credentials and manual CAPTCHA. Populate synthetic mandatory, optional and conditional fields, upload authorized PDF fixtures, verify all eight sections, and stop at preview without final submission. Existing submitted applications must not be bypassed.')
@allure.severity(allure.severity_level.CRITICAL)
def test_tsp_all_fields_without_submission(tsp_session, tsp_data):
    form = TspApplicationPage(tsp_session, tsp_data)
    if os.getenv('TSP_UPLOAD_DOM_DIAGNOSTIC') == '1':
        from upload_dom_diagnostic import capture_upload_dom
        allure.dynamic.title('TSP read-only upload DOM diagnostic (not a positive-flow execution)')
        allure.dynamic.description('Manual CAPTCHA login, manual navigation to an already accessible Step 4, and two sanitized upload DOM checkpoints. Tester may manually select authorized PDF fixtures; automation does not fill forms, upload, save, continue, submit or add staff.')
        try:
            form.login_attended()
            capture_upload_dom(form)
        except pytest.skip.Exception:
            raise
        except Exception:
            raise AssertionError('TSP DOM diagnostic could not complete; private details suppressed.') from None
        return
    try:
        allure.attach('All applicable fields populated; all 11 documents uploaded; preview verified; final confirmation unchecked and submission never invoked.',
                      'Expected result', allure.attachment_type.TEXT)
    except (Exception, pytest.skip.Exception):
        pass  # Optional reporting must not prevent the workflow from starting.
    outcome = 'INCOMPLETE'
    try:
        form.login_attended()
        form.open_application()
        form.fill_all_sections()
        form.verify_preview()
        form.attach_safe_evidence('Preview privacy placeholder', required=True)
        outcome = 'COMPLETED: Configured preview assertions completed; privacy placeholder generated, not visual evidence; final confirmation unchecked; Submit Application not invoked.'
    except pytest.skip.Exception:
        outcome = 'SKIPPED / BLOCKED: Workflow did not complete.'
        raise
    except Exception:
        outcome = 'FAILED: Workflow did not complete.'
        try:
            form.attach_safe_evidence('Failure before submission')
        except (Exception, pytest.skip.Exception):
            pass  # Preserve the sanitized workflow failure below.
        # Do not propagate Playwright fill call logs or raw DOM through pytest/Allure.
        try:
            allure.attach(form.stage, 'Last execution stage', allure.attachment_type.TEXT)
        except (Exception, pytest.skip.Exception):
            pass  # Preserve the sanitized workflow failure below.
        raise AssertionError(f'TSP positive draft flow failed at {form.stage}; private details suppressed.') from None
    finally:
        pending_exception = sys.exc_info()[0] is not None
        try:
            allure.attach(outcome + '\n\n' + form.save_draft_action_report(),
                          'Actual result', allure.attachment_type.TEXT)
        except (Exception, pytest.skip.Exception):
            if not pending_exception:
                raise AssertionError('TSP final reporting failed; private details suppressed.') from None
# python -m pytest tests\tsp\test_tsp_application.py -v --headed --tsp-attended -s
