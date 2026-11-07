"""One sequential TSP test, with eight section helpers and fail-closed action gates.

Static implementation is not execution evidence. Fresh-account preflight is manual;
missing application handler/persistence contracts block before browser setup.
"""
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
