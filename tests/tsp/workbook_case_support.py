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
    mapping = json.loads(
        (ROOT / 'data/tsp_workbook_automation.json').read_text(encoding='utf-8')
    )
    path = ROOT / mapping['workbook']

    if hashlib.sha256(path.read_bytes()).hexdigest() != mapping['workbook_sha256']:
        raise ValueError(
            'Workbook changed: review and regenerate the case mapping before collection.'
        )

    book = load_workbook(path, read_only=True, data_only=False)
    try:
        sheets = {sheet.title: list(sheet.values) for sheet in book}
        rows = sheets['TSP Test Cases']
        cases = [dict(zip(rows[0], row)) for row in rows[1:]]
    finally:
        book.close()

    ids = [case['Test Case ID'] for case in cases]
    records = mapping['records']

    if (
        len(ids) != 214 or len(set(ids)) != 214
        or len(records) != 214
        or {r['id'] for r in records} != set(ids)
    ):
        raise ValueError(
            'Workbook and automation mapping must contain exactly 214 unique matching IDs.'
        )

    by_id = {case['Test Case ID']: case for case in cases}
    result = {}

    for record in records:
        source = by_id[record['id']]

        if source['Module / section'] != record['section']:
            raise ValueError(
                f"Workbook section mismatch for {record['id']}; review required."
            )

        result[record['id']] = dict(record, source=source)

    return result


CASES = load_cases()



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


def login_failure_frames(error):
    """Recover sanitized source locations retained behind `raise ... from None`.

    Never serialize messages, frame locals, source text, URLs or credential values.
    """
    frames, seen = [], set()
    while error is not None and id(error) not in seen:
        seen.add(id(error))
        trace = error.__traceback__
        while trace is not None:
            code = trace.tb_frame.f_code
            if (Path(code.co_filename).name == 'tsp_application_page.py'
                    and code.co_name == 'login_attended'):
                frames.append({'file': 'pages/tsp_application_page.py',
                               'function': 'login_attended', 'line': trace.tb_lineno,
                               'exception_type': type(error).__name__})
            trace = trace.tb_next
        error = error.__cause__ or error.__context__
    return frames



def attended_apply_case(request, case):
    """TSPD-003: Verify Apply navigation and Application Type screen."""

    if not request.config.getoption('--tsp-attended') or request.config.getoption('capture') != 'no':
        pytest.skip('Use --tsp-attended and -s.')

    if os.getenv('DEBUG') or os.getenv('PWDEBUG'):
        pytest.skip('Disable debug logging before private login.')

    load_dotenv(ROOT / '.env', override=True)

    if not all(os.getenv(key, '').strip() for key in ('TSP_EMAIL', 'TSP_PASSWORD')):
        pytest.skip('Required private credentials are missing.')

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]
    folder = ROOT / 'artifacts' / ('tspd-003-' + stamp)
    folder.mkdir(parents=True, exist_ok=False)

    record = {
        'case_id': 'TSPD-003',
        'status': 'NOT RUN',
        'login_verified': False,
        'apply_clicked': False,
        'application_opened': False,
        'actual': 'Test not completed.',
        'expected': case['source']['Expected result']
    }

    browser = context = None

    try:
        driver = request.getfixturevalue('playwright')
        browser = driver.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1366, 'height': 900})
        context.set_default_timeout(15000)
        context.set_default_navigation_timeout(60000)

        page = context.new_page()

        login = TspApplicationPage(
            page,
            {'home_url': TspMcpApplicationPage.ORIGIN + '/en/home'}
        )
        login.login_attended()

        form = TspMcpApplicationPage(page)

        form.verify_authenticated_landing()
        record['login_verified'] = True

        apply_link = page.locator('a[href*="/en/tsp-registration-form"]')
        expect(apply_link).to_have_count(1)
        expect(apply_link).to_be_visible()

        apply_link.click()
        record['apply_clicked'] = True

        form.verify_application_opened()
        record['application_opened'] = True
        record['status'] = 'PASS'
        record['actual'] = (
            'Login successful. Apply clicked once. '
            'TSP Application Type screen opened successfully.'
        )

    except pytest.skip.Exception:
        raise

    except Exception:
        record['status'] = 'FAIL'
        record['actual'] = (
            'TSPD-003 failed during login or Apply navigation. '
            'Private details suppressed. No automatic retry.'
        )
        raise AssertionError(
            'TSPD-003 failed; private details suppressed.'
        ) from None

    finally:
        try:
            body = json.dumps(record, indent=2)
            (folder / 'execution.json').write_text(body, encoding='utf-8')
            allure.attach(
                body,
                'TSPD-003 execution evidence',
                allure.attachment_type.JSON
            )
        finally:
            try:
                if context is not None:
                    context.close()
            finally:
                if browser is not None:
                    browser.close()


def attended_banner_apply_case(request, case):
    """TSPD-011: Verify Apply for Recognition banner navigation."""

    if not request.config.getoption('--tsp-attended') or request.config.getoption('capture') != 'no':
        pytest.skip('Use --tsp-attended and -s.')

    if os.getenv('DEBUG') or os.getenv('PWDEBUG'):
        pytest.skip('Disable debug logging before private login.')

    load_dotenv(ROOT / '.env', override=True)

    if not all(os.getenv(key, '').strip() for key in ('TSP_EMAIL', 'TSP_PASSWORD')):
        pytest.skip('Required private credentials are missing.')

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]
    folder = ROOT / 'artifacts' / ('tspd-011-' + stamp)
    folder.mkdir(parents=True, exist_ok=False)

    record = {
        'case_id': 'TSPD-011',
        'status': 'NOT RUN',
        'login_verified': False,
        'home_clicked': False,
        'banner_visible': False,
        'banner_clicked': False,
        'application_opened': False,
        'actual': 'Test not completed.',
        'expected': case['source']['Expected result']
    }

    browser = context = None

    try:
        driver = request.getfixturevalue('playwright')
        browser = driver.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1366, 'height': 900})
        context.set_default_timeout(15000)
        context.set_default_navigation_timeout(60000)

        page = context.new_page()

        login = TspApplicationPage(
            page,
            {'home_url': TspMcpApplicationPage.ORIGIN + '/en/home'}
        )
        login.login_attended()

        form = TspMcpApplicationPage(page)
        form.verify_authenticated_landing()
        record['login_verified'] = True

        # Step 1: Click Home in the sidebar.
        home = page.get_by_text('Home', exact=True)
        expect(home).to_have_count(1)
        expect(home).to_be_visible()
        home.click()
        record['home_clicked'] = True

        # Verify return to the dashboard.
        form.verify_authenticated_landing()

        # Step 2: Locate the banner action.
        banner = page.get_by_text('Apply for Recognition', exact=True)
        expect(banner).to_have_count(1)
        expect(banner).to_be_visible()
        record['banner_visible'] = True

        # Step 3: Click the banner once.
        banner.click()
        record['banner_clicked'] = True

        # Step 4: Verify destination.
        form.verify_application_opened()

        record['application_opened'] = True
        record['status'] = 'PASS'
        record['actual'] = (
            'Login successful. Home clicked once. '
            'Apply for Recognition banner clicked once. '
            'TSP Application Type screen opened successfully.'
        )

    except pytest.skip.Exception:
        raise

    except Exception:
        record['status'] = 'FAIL'
        record['actual'] = (
            'TSPD-011 failed during login, Home navigation or banner navigation. '
            'Private details suppressed. No automatic retry.'
        )
        raise AssertionError(
            'TSPD-011 failed; private details suppressed.'
        ) from None

    finally:
        try:
            body = json.dumps(record, indent=2)
            (folder / 'execution.json').write_text(body, encoding='utf-8')
            allure.attach(
                body,
                'TSPD-011 execution evidence',
                allure.attachment_type.JSON
            )
        finally:
            try:
                if context is not None:
                    context.close()
            finally:
                if browser is not None:
                    browser.close()





def attended_verified_banner_case(request, case):
    """TSPD-012: Verify banner action for an already-verified TSP."""

    if (
        not request.config.getoption('--tsp-attended')
        or request.config.getoption('capture') != 'no'
    ):
        pytest.skip('Use --tsp-attended and -s.')

    if os.getenv('DEBUG') or os.getenv('PWDEBUG'):
        pytest.skip('Disable debug logging before private login.')

    load_dotenv(ROOT / '.env', override=True)

    # Validate dedicated Verified TSP credentials.
    if not all(
        os.getenv(key, '').strip()
        for key in (
            'TSP_VERIFIED_USERNAME',
            'TSP_VERIFIED_PASSWORD'
        )
    ):
        pytest.skip('Verified TSP credentials are missing.')

    stamp = (
        datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        + '-'
        + uuid4().hex[:8]
    )

    folder = ROOT / 'artifacts' / ('tspd-012-' + stamp)
    folder.mkdir(parents=True, exist_ok=False)

    record = {
        'case_id': 'TSPD-012',
        'status': 'NOT RUN',
        'login_verified': False,
        'approved_status_verified': False,
        'banner_visible': False,
        'banner_disabled': False,
        'actual': 'Test not completed.',
        'expected': case['source']['Expected result']
    }

    browser = context = page = None

    try:
        driver = request.getfixturevalue('playwright')

        browser = driver.chromium.launch(headless=False)

        context = browser.new_context(
            viewport={'width': 1366, 'height': 900}
        )

        context.set_default_timeout(15000)
        context.set_default_navigation_timeout(60000)

        page = context.new_page()

        # Register the manually created page for failure screenshots.
        def cleanup_browser():
            if context is not None:
                context.close()

            if browser is not None:
                browser.close()

        register_page = request.getfixturevalue(
            'allure_failure_screenshots'
        )

        register_page(
            page,
            cleanup=cleanup_browser
        )

        # Login using the dedicated Verified TSP account.
        form = TspMcpApplicationPage(page)
        form.login_verified_attended()

        # Verify authenticated dashboard landing.
        form.verify_authenticated_landing()
        record['login_verified'] = True

        # Verify Approved Status is Verified.
        verified_status = page.get_by_text(
            'Verified',
            exact=True
        )

        expect(verified_status.first).to_be_visible()
        record['approved_status_verified'] = True

        # Apply for Recognition is an anchor, not a button.
        banner = page.locator('a[data-tsp="applyBtn"]')

        expect(banner).to_be_visible()
        record['banner_visible'] = True

        # Verify disabled CSS class.
        expect(banner).to_have_class(
            'btn btn-primary-custom rounded-pill px-4 disabled'
        )

        # Verify accessibility disabled state.
        expect(banner).to_have_attribute(
            'aria-disabled',
            'true'
        )

        record['banner_disabled'] = True

        # Observation-only test. Never click the link.
        record['status'] = 'PASS'
        record['actual'] = (
            'Login successful. Approved Status displays Verified. '
            'Apply for Recognition link is visible and disabled '
            'using disabled CSS class and aria-disabled=true. '
            'Link was not clicked.'
        )

    except pytest.skip.Exception:
        raise

    except Exception:
        record['status'] = 'FAIL'
        record['actual'] = (
            'TSPD-012 failed during login or dashboard verification. '
            'Private details suppressed. No automatic retry.'
        )

        raise AssertionError(
            'TSPD-012 failed; private details suppressed.'
        ) from None

    finally:
        try:
            body = json.dumps(record, indent=2)

            (folder / 'execution.json').write_text(
                body,
                encoding='utf-8'
            )

            allure.attach(
                body,
                'TSPD-012 execution evidence',
                allure.attachment_type.JSON
            )

        finally:
            # Browser cleanup is handled by the shared fixture.
            # Keep the page open until failure screenshot capture.
            pass







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
