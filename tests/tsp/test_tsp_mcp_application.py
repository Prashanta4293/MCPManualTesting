from workbook_case_support import (
    attended_verified_banner_case,
    run_case,
    section_ids,
    attended_apply_case,
    attended_banner_apply_case,
    CASES
)
import json
import math
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import allure
import pytest   
from dotenv import load_dotenv

from sequential_flow_support import (
    FlowBlocked, ScenarioLedger, SequentialSections, confirm, require_contract,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.tsp_application
@pytest.mark.regression
@pytest.mark.manual_captcha
@pytest.mark.flaky(reruns=0)
@allure.epic('Odisha Tourism')
@allure.feature('Sequential TSP application')
class TestTSPApplicationFlow:
    __test__ = False  # Retain prior code; do not collect obsolete scenario IDs.
    @allure.title('TSP-SEQ-001 Eight-section sequential negative and positive flow')
    def test_tsp_sequential_flow(self, request):
        inventory = json.loads((ROOT / 'data/tsp_sequential_scenarios.json').read_text(encoding='utf-8'))
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]
        run_dir = ROOT / 'artifacts' / ('tsp-sequential-' + stamp)
        run_dir.mkdir(parents=True, exist_ok=False)
        ledger = ScenarioLedger(inventory, run_dir)
        browser = context = page = None
        try:
            if os.getenv('PYTEST_XDIST_WORKER') or getattr(request.config.option, 'numprocesses', 0):
                raise FlowBlocked('Parallel execution is prohibited.')
            if getattr(request.config.option, 'reruns', 0):
                raise FlowBlocked('Automatic retries are prohibited.')
            if not request.config.getoption('--tsp-attended') or request.config.getoption('capture') != 'no':
                raise FlowBlocked('Use --tsp-attended and -s for the attended flow.')
            if os.getenv('DEBUG') or os.getenv('PWDEBUG'):
                raise FlowBlocked('Disable debug logging before private login.')
            confirm('An authorized administrator/read-only backend check must confirm '
                    'the locally configured account has no application or draft in any status. '
                    'If this is NOT verified, do not confirm.', 'FRESH VERIFIED')
            # Opening Apply can initialize state. No browser needed to enforce this
            # currently unverified source contract; no automatic override is offered.
            require_contract('fresh-application-initialization')
            data = request.getfixturevalue('tsp_data')
            load_dotenv(ROOT / '.env', override=True)
            if not all(os.getenv(k, '').strip() for k in ('TSP_EMAIL', 'TSP_PASSWORD')):
                raise FlowBlocked('Required private TSP credential configuration missing.')
            # Same Chromium browser for pytest and MCP, loopback CDP only. No shared
            # fixture modification; credentials/traces/videos/screenshots never logged.
            with socket.socket() as reservation:
                reservation.bind(('127.0.0.1', 0))
                port = reservation.getsockname()[1]
            playwright = request.getfixturevalue('playwright')
            browser = playwright.chromium.launch(headless=False, args=[
                '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=' + str(port)])
            ledger.browser_started = True
            context = browser.new_context(viewport={'width': 1366, 'height': 900})
            page = context.new_page()
            page.set_default_timeout(15000)
            page.set_default_navigation_timeout(60000)
            def count(key):
                ledger.diagnostics[key] += 1
            page.on('console', lambda msg: count('console_errors') if msg.type == 'error' else None)
            page.on('pageerror', lambda _: count('runtime_errors'))
            page.on('requestfailed', lambda _: count('failed_requests'))
            endpoint = 'http://127.0.0.1:' + str(port)
            (run_dir / 'mcp-endpoint.json').write_text(json.dumps({'endpoint': endpoint}), encoding='utf-8')
            print('Headed pytest browser CDP endpoint: ' + endpoint, flush=True)
            confirm('Attach MCP read-only to THIS endpoint and verify the same context/page. '
                    'Do not open another UAT session or close the shared browser.', 'MCP ATTACHED')
            flow = SequentialSections(page, data, ledger)
            flow.form.fresh_account_confirmed = True
            flow.form.login_attended()  # Existing CAPTCHA + terminal CONFIRM unchanged.
            # Fresh-only helper refuses detected drafts, identity parameters and populated type.
            flow.form.open_fresh_application()
            flow.run()
            if any(r['status'] == 'BLOCKED' for r in ledger.rows.values()):
                raise FlowBlocked('Positive progression finished but blocked scenarios remain; no complete-suite success claimed.')
            if any(r['status'] != 'PASS' for r in ledger.rows.values()):
                raise FlowBlocked('Not all mapped scenarios were verified; no complete-suite success claimed.')
            ledger.execution_status = 'PASS'
        except FlowBlocked as exc:
            ledger.execution_status = 'BLOCKED'
            ledger.stop += ': ' + str(exc)
            if not ledger.browser_started:
                ledger.set('TSP-APP-001', 'BLOCKED', str(exc))
            pytest.skip('BLOCKED: ' + str(exc))
        except pytest.skip.Exception:
            ledger.execution_status = 'BLOCKED'
            ledger.stop += ': attended/page-object safety stop'
            raise
        except Exception as exc:
            ledger.execution_status = 'FAIL'
            ledger.capture_failure(exc, 'Sequential workflow')
            ledger.stop += ': unexpected failure; private details suppressed; state uncertain'
            raise AssertionError('Sequential TSP flow failed; private details suppressed. Do not retry persisted actions.') from None
        finally:
            pending = sys.exc_info()[0] is not None
            if pending and ledger.execution_status == 'NOT EXECUTED':
                ledger.execution_status = 'INTERRUPTED'
            try:
                cleanup_failed = False
                try:
                    if page is not None and not page.is_closed():
                        try:
                            seconds = float(os.getenv('TSP_BROWSER_HOLD_SECONDS', '60'))
                            if not math.isfinite(seconds) or seconds < 0:
                                seconds = 60
                        except ValueError:
                            seconds = 60
                        page.wait_for_timeout(min(seconds, 300) * 1000)
                except Exception:
                    cleanup_failed = True
                finally:
                    try:
                        if context is not None:
                            context.close()
                    except Exception:
                        cleanup_failed = True
                    finally:
                        try:
                            if browser is not None:
                                browser.close()
                        except Exception:
                            cleanup_failed = True
            finally:
                preserving_exception = pending or sys.exc_info()[0] is not None
                if cleanup_failed:
                    ledger.reporting_errors.append('Browser cleanup incomplete; private details suppressed.')
                    if not pending:
                        ledger.execution_status = 'FAIL'
                try:
                    ledger.finish()
                except Exception:
                    if not preserving_exception:
                        raise AssertionError('Sequential reporting failed; private details suppressed.') from None
                if not preserving_exception and (cleanup_failed or ledger.reporting_errors):
                    raise AssertionError('Sequential reporting or cleanup failed; private details suppressed.') from None


# Only these workbook-backed classes are collected. Legacy orchestration stays dormant.
from workbook_case_support import CASES, run_case, section_ids
from pages.tsp_mcp_application_page import TspMcpApplicationPage


@pytest.fixture
def tsp_mcp_attended_session(request, playwright):
    """TSPD-003-only headed session with loopback CDP for same-browser inspection."""
    if not request.config.getoption('--tsp-attended') or request.config.getoption('capture') != 'no':
        pytest.skip('Use --tsp-attended and -s for manual CAPTCHA.')
    if os.getenv('DEBUG') or os.getenv('PWDEBUG'):
        pytest.skip('Disable private browser debug logging.')
    load_dotenv(ROOT / '.env', override=True)
    if not all(os.getenv(k, '').strip() for k in ('TSP_EMAIL', 'TSP_PASSWORD')):
        pytest.skip('Required private TSP credential configuration missing.')
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    browser = playwright.chromium.launch(headless=False, args=[
        '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=' + str(port)])
    context = None
    try:
        context = browser.new_context(viewport={'width': 1366, 'height': 900})
        context.set_default_timeout(15000)
        context.set_default_navigation_timeout(60000)
        page = context.new_page()
        print('TSPD-003 MCP endpoint: http://127.0.0.1:' + str(port), flush=True)
        yield page
    finally:
        try:
            if context is not None:
                context.close()
        finally:
            browser.close()


def _attended_mcp_login_case(request, case_id):
    """Reuse the positive suite's attended browser fixture, never its page class."""
    # if (os.getenv('PYTEST_XDIST_WORKER') or
    #         getattr(request.config.option, 'numprocesses', 0) or
    #         getattr(request.config.option, 'reruns', 0)):
    #     pytest.skip('TSPD-003: BLOCKED — parallel execution/retries prohibited.')
    form = None
    outcome = 'FAIL'
    actual = 'Attended setup did not complete; Apply was not clicked.'
    try:
        allure.dynamic.id(case_id)
        allure.dynamic.title(case_id + ' — Apply navigation: attended prerequisite check')
        allure.dynamic.epic('Odisha Tourism')
        allure.dynamic.feature('TSP Application')
        allure.dynamic.story('Application Type')
        allure.attach(CASES[case_id]['source']['Expected result'],
                      'Expected result', allure.attachment_type.TEXT)
        # Same headed/private login conventions; local CDP fixture for MCP access.
        # No shared fixture change, video, trace or credential screenshot.
        page = request.getfixturevalue('tsp_mcp_attended_session')
        form = TspMcpApplicationPage(page)
        form.login_attended()
        actual = 'Authenticated dashboard verified. Apply not clicked.'
        form.verify_apply_available()
        form.verify_dashboard_freshness()
        actual = 'Dashboard shows Not Applied and No TSP application yet; user-approved UI freshness rule verified. Not a backend audit.'
        confirm('Pause for read-only MCP inspection of this dashboard, Apply link and '
                'loaded handlers. Do not activate application controls.', 'MCP INSPECTED')
        confirm('Opening Apply may initialize backend data; non-persistence has not been established. '
                'Authorize this ONE navigation for the dedicated account only if acceptable. '
                'No field changes, saves, uploads or submission are permitted.', 'OPEN APPLY ONCE')
        form.open_apply_once(initialization_authorized=True)
        form.verify_application_opened()
        actual += ' Apply clicked once; Application Type form displayed. Active sidebar verification pending.'
        confirm('Pause for sanitized MCP inspection of the Apply active-sidebar DOM. '
                'Do not change form data or navigate further.', 'SIDEBAR INSPECTED')
        raise FlowBlocked('TSPD-003: active-sidebar assertion awaits verified DOM implementation; no PASS claimed.')
    except FlowBlocked as exc:
        outcome = 'BLOCKED'
        actual += ' ' + str(exc)
        pytest.skip(str(exc))
    except pytest.skip.Exception:
        outcome = 'BLOCKED'
        actual += ' Attended setup or confirmation stopped.'
        raise
    except Exception:
        raise AssertionError('TSPD-003 attended setup failed; see sanitized login stage.') from None
    finally:
        pending = sys.exc_info()[0] is not None
        evidence = dict(case_id=case_id, status=outcome, actual=actual,
                        login_stage=form.login_stage if form else 'Browser/fixture setup',
                        login_error=form.login_error if form else None,
                        login_verified=bool(form and form.authenticated),
                        dashboard_freshness_verified=bool(form and form.dashboard_freshness_verified),
                        freshness_basis='User-approved dashboard indicators; no backend audit',
                        apply_click_attempted=bool(form and form.apply_click_attempted),
                        apply_clicked=bool(form and form.apply_clicked),
                        application_actions=int(bool(form and form.apply_click_attempted)),
                        persistence='Not independently measured; no saves/uploads/submission invoked')
        try:
            allure.attach(json.dumps(evidence, indent=2), 'TSPD-003 sanitized login result',
                          allure.attachment_type.JSON)
        except Exception:
            if not pending:
                raise AssertionError('TSPD-003 sanitized reporting failed.') from None



@pytest.mark.tsp_application
@pytest.mark.regression
@pytest.mark.flaky(reruns=0)
class TestWorkbookApplicationType:
    @pytest.mark.parametrize(
        'case_id',
        section_ids('Application Type'),
        ids=str
    )
    def test_case(self, request, case_id):
        if case_id == 'TSPD-003':
            attended_apply_case(request, CASES[case_id])
        elif case_id == 'TSPD-011':
            attended_banner_apply_case(request, CASES[case_id])
        elif case_id == 'TSPD-012':
            attended_verified_banner_case(request, CASES[case_id])    
        else:
            run_case(request, case_id)
        


@pytest.mark.tsp_application
@pytest.mark.regression
@pytest.mark.flaky(reruns=0)
class TestWorkbookApplicantDetails:
    @pytest.mark.parametrize('case_id', section_ids('Applicant Details'), ids=str)
    def test_case(self, request, case_id):
        run_case(request, case_id)


@pytest.mark.tsp_application
@pytest.mark.regression
@pytest.mark.flaky(reruns=0)
class TestWorkbookOfficeDetails:
    @pytest.mark.parametrize('case_id', section_ids('Office Details'), ids=str)
    def test_case(self, request, case_id):
        run_case(request, case_id)


@pytest.mark.tsp_application
@pytest.mark.regression
@pytest.mark.flaky(reruns=0)
class TestWorkbookHRCertification:
    @pytest.mark.parametrize('case_id', section_ids('HR & Certification'), ids=str)
    def test_case(self, request, case_id):
        run_case(request, case_id)


@pytest.mark.tsp_application
@pytest.mark.regression
@pytest.mark.flaky(reruns=0)
class TestWorkbookTransportDetails:
    @pytest.mark.parametrize('case_id', section_ids('Transport Details'), ids=str)
    def test_case(self, request, case_id):
        run_case(request, case_id)


@pytest.mark.tsp_application
@pytest.mark.regression
@pytest.mark.flaky(reruns=0)
class TestWorkbookDocuments:
    @pytest.mark.parametrize('case_id', section_ids('Documents'), ids=str)
    def test_case(self, request, case_id):
        run_case(request, case_id)


@pytest.mark.tsp_application
@pytest.mark.regression
@pytest.mark.flaky(reruns=0)
class TestWorkbookDeclaration:
    @pytest.mark.parametrize('case_id', section_ids('Declaration'), ids=str)
    def test_case(self, request, case_id):
        run_case(request, case_id)


@pytest.mark.tsp_application
@pytest.mark.regression
@pytest.mark.flaky(reruns=0)
class TestWorkbookPreviewSubmit:
    @pytest.mark.parametrize('case_id', section_ids('Preview & Submit'), ids=str)
    def test_case(self, request, case_id):
        run_case(request, case_id)
