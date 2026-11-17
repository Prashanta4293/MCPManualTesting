"""Workbook-specific passive assertions; never establish or mutate browser state.

The prepared-section fixture is deliberately blocked. The existing tsp_session
creates a new browser, and reaching Documents/Preview requires unverified writes.
Do not replace this gate with a call to a positive-flow section method.
"""
import hashlib
import json
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import allure
import pytest
from openpyxl import load_workbook
from playwright.sync_api import expect
from dotenv import load_dotenv

from pages.tsp_mcp_application_page import TspMcpApplicationPage
from pages.tsp_application_page import TspApplicationPage
from sequential_flow_support import FlowBlocked, confirm, require_contract

ROOT = Path(__file__).resolve().parents[2]


def load_cases():
    mapping = json.loads((ROOT / 'data/tsp_workbook_automation.json').read_text(encoding='utf-8'))
    path = ROOT / mapping['workbook']
    if hashlib.sha256(path.read_bytes()).hexdigest() != mapping['workbook_sha256']:
        raise ValueError('Workbook changed: review and regenerate the case mapping before collection.')
    book = load_workbook(path, read_only=True, data_only=False)
    try:
        sheets = {sheet.title: list(sheet.values) for sheet in book}
        rows = sheets['TSP Test Cases']
        cases = [dict(zip(rows[0], row)) for row in rows[1:]]
    finally:
        book.close()
    ids = [case['Test Case ID'] for case in cases]
    records = mapping['records']
    if (len(ids) != 214 or len(set(ids)) != 214 or
            len(records) != 214 or {r['id'] for r in records} != set(ids)):
        raise ValueError('Workbook and automation mapping must contain exactly 214 unique matching IDs.')
    by_id = {case['Test Case ID']: case for case in cases}
    result = {}
    for record in records:
        source = by_id[record['id']]
        if (source['Module / section'] != record['section'] or
                source['Review status'] != record['review_status']):
            raise ValueError('Workbook classification mismatch; review required.')
        result[record['id']] = dict(record, source=source)
    return result


CASES = load_cases()  # Read-only; no browser, .env, application actions or writes.


def section_ids(section):
    return [key for key, value in CASES.items() if value['section'] == section]


def prepared_readonly_form(request, case):
    # Do not request tsp_session: it launches Chromium and has no independently
    # verified read-only route to a prepared Documents/Preview section.
    # This requires a separate reviewed fixture implementation, not an env bypass.
    pytest.skip(case['id'] + ': BLOCKED — an authorized, independently prepared '
                'read-only section fixture is not verified. No browser or login requested. '
                'Fresh-account, manual CAPTCHA and initialization gates remain required.')


def document_actions(form, numbers, names):
    """Observe existing rows/buttons; never call viewDoc/upload or any control."""
    for number in numbers:
        row = form.document_row(number)
        expect(row).to_have_count(1)
        expect(row).to_be_visible()
        # Count ALL buttons, not only matching ones: unexpected extra actions fail.
        expect(form.document_actions(number)).to_have_count(len(names))
        for name in names:
            button = form.document_action(number, name)
            expect(button).to_have_count(1)
            expect(button).to_be_visible()
        if 'Not Applicable' not in names:
            expect(form.document_action(number, 'Not Applicable',
                                        include_hidden=True)).to_have_count(0)


def required_document_actions(form, case):
    document_actions(form, (1, 3, 5, 6, 7, 8), ('View', 'Upload'))


def applicable_document_actions(form, case):
    document_actions(form, (2, 4, 9, 10), ('View', 'Upload', 'Not Applicable'))


def preview_banner(form, case):
    # Exact public wording comes from the workbook, not a generic success check.
    expected = case['source']['Expected result']
    prefix = "Banner should read '"
    if not expected.startswith(prefix) or not expected.endswith("'."):
        raise AssertionError('Preview banner specification requires renewed review.')
    wording = expected[len(prefix):-2]
    banner = form.preview_banner(wording)
    expect(banner).to_have_count(1)
    expect(banner).to_be_visible()


VALIDATORS = {
    'required_document_actions': required_document_actions,
    'applicable_document_actions': applicable_document_actions,
    'preview_banner': preview_banner,
}


def attended_apply_case(request, case):
    """TSPD-003 only: login/landing inspection precedes independent Apply gates."""
    if (os.getenv('PYTEST_XDIST_WORKER') or
            getattr(request.config.option, 'numprocesses', 0) or
            getattr(request.config.option, 'reruns', 0)):
        pytest.skip('TSPD-003: BLOCKED — parallel execution/retries prohibited.')
    if not request.config.getoption('--tsp-attended') or request.config.getoption('capture') != 'no':
        pytest.skip('TSPD-003: BLOCKED — use --tsp-attended and -s.')
    if os.getenv('DEBUG') or os.getenv('PWDEBUG'):
        pytest.skip('TSPD-003: BLOCKED — disable debug logging before private login.')
    load_dotenv(ROOT / '.env', override=True)
    if not all(os.getenv(key, '').strip() for key in ('TSP_EMAIL', 'TSP_PASSWORD')):
        pytest.skip('TSPD-003: BLOCKED — required private credential configuration missing.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]
    folder = ROOT / 'artifacts' / ('tspd-003-' + stamp)
    folder.mkdir(parents=True, exist_ok=False)
    record = dict(case_id='TSPD-003', status='BLOCKED', login_verified=False,
                  apply_clicked=False, freshness_verified=False,
                  initialization_authorized=False,
                  actual='Attended setup incomplete; Apply navigation not executed.',
                  expected=case['source']['Expected result'],
                  application_state='No form action dispatched. Backend state not independently measured.')
    browser = context = None
    try:
        with socket.socket() as reservation:
            reservation.bind(('127.0.0.1', 0))
            port = reservation.getsockname()[1]
        driver = request.getfixturevalue('playwright')
        browser = driver.chromium.launch(headless=False, args=[
            '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=' + str(port)])
        context = browser.new_context(viewport={'width': 1366, 'height': 900})
        context.set_default_timeout(15000)
        context.set_default_navigation_timeout(60000)
        page = context.new_page()
        endpoint = 'http://127.0.0.1:' + str(port)
        (folder / 'mcp-endpoint.json').write_text(json.dumps({'endpoint': endpoint}), encoding='utf-8')
        print('TSPD-003 headed-browser MCP endpoint: ' + endpoint, flush=True)
        # Reuse only the existing sanitized login; never its persistence-authorizing
        # freshness prompt, positive fill methods, save or upload operations.
        TspApplicationPage(page, {'home_url': TspMcpApplicationPage.ORIGIN + '/en/home'}).login_attended()
        form = TspMcpApplicationPage(page)
        with allure.step('TSPD-003 authenticated landing and Apply availability'):
            try:
                form.verify_authenticated_landing()
                record['login_verified'] = True
                form.verify_apply_available()
            except Exception:
                raise AssertionError('TSPD-003 landing/Apply availability failed; private details suppressed.') from None
        record['actual'] = 'Authenticated dashboard and unique visible Apply link verified. Apply not clicked.'
        # Save a safe checkpoint while the attended browser waits for MCP.
        (folder / 'execution.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
        confirm('Pause for read-only MCP inspection of this dashboard and Apply link. '
                'Do not navigate or expose personal data.', 'MCP INSPECTED')
        confirm('Confirm an authorized administrator/read-only backend check established '
                'NO application or draft in any status for this account and cycle. '
                'This confirms freshness ONLY, not permission to create or save.', 'FRESH VERIFIED')
        record['freshness_verified'] = True
        # Freshness does not authorize initialization or establish its behavior.
        require_contract('fresh-application-initialization')
        # Active-sidebar selection evidence has not yet been established. Do not
        # click first and later discover that the complete assertion cannot run.
        raise FlowBlocked('TSPD-003: active-sidebar DOM selection contract still requires review; Apply not clicked.')
    except FlowBlocked as exc:
        record['actual'] += ' BLOCKED: ' + str(exc)
        pytest.skip(str(exc))
    except pytest.skip.Exception:
        record['actual'] += ' BLOCKED: attended setup/confirmation stopped.'
        raise
    except Exception:
        record['status'] = 'FAIL'
        record['actual'] = 'Attended setup or landing verification failed; private details suppressed. No automatic retry.'
        raise AssertionError('TSPD-003 setup/inspection failed; private details suppressed.') from None
    finally:
        pending = sys.exc_info()[0] is not None
        try:
            body = json.dumps(record, indent=2)
            (folder / 'execution.json').write_text(body, encoding='utf-8')
            allure.attach(body, 'TSPD-003 sanitized execution evidence', allure.attachment_type.JSON)
        except Exception:
            if not pending:
                raise AssertionError('TSPD-003 evidence recording failed; private details suppressed.') from None
        finally:
            try:
                if context is not None:
                    context.close()
            finally:
                if browser is not None:
                    browser.close()


def run_case(request, case_id):
    case = CASES[case_id]
    # Do not attach full source data: it contains historical applicant examples.
    try:
        allure.dynamic.id(case_id)
        allure.dynamic.title(case_id + ' — ' + case['source']['Description'])
        allure.dynamic.epic('Odisha Tourism')
        allure.dynamic.feature('TSP Application')
        allure.dynamic.story(case['section'])
        allure.dynamic.suite(case['section'])
        allure.dynamic.description('Workbook case ' + case_id + '. ' + case['classification'] +
                                   '. Static implementation is not execution evidence.')
        if case_id == 'TSPD-003':
            attended_apply_case(request, case)
            return
        with allure.step(case_id + ': check implementation and safe setup prerequisites'):
            if case['classification'] != 'READY FOR IMPLEMENTATION REVIEW':
                pytest.skip(case_id + ': BLOCKED — ' + case['reason'])
            prepared = prepared_readonly_form(request, case)
            form = TspMcpApplicationPage(prepared.page)
        with allure.step(case_id + ': verify workbook expected result without changing state'):
            try:
                form.at(case['section'])  # Dedicated page object's read-only section check.
                VALIDATORS[case['validator']](form, case)
            except pytest.skip.Exception:
                raise
            except Exception:
                # Sanitize BEFORE the Allure step records the exception. Never
                # expose Playwright call logs, row text, URLs or document names.
                raise AssertionError(case_id + ': read-only assertion failed; private details suppressed.') from None
        allure.attach('Workbook assertions completed; no application action performed.',
                      case_id + ' Actual result', allure.attachment_type.TEXT)
    except pytest.skip.Exception:
        raise
    except Exception:
        raise AssertionError(case_id + ': assertion or reporting failed; private details suppressed.') from None
