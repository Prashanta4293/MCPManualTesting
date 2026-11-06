"""Isolated attended TSP fixtures; no changes to Visitor fixtures."""
import json
import math
import os
import time
from pathlib import Path

import allure
import pytest
from dotenv import load_dotenv
from playwright.sync_api import Error as PlaywrightError

ROOT = Path(__file__).resolve().parents[2]


def pytest_addoption(parser):
    parser.addoption('--tsp-attended', action='store_true',
                     help='Authorize headed TSP flow including the required Documents Save Draft checkpoint; never final submit.')


def pytest_configure(config):
    config.addinivalue_line('markers', 'tsp_application: TSP eight-section draft flow, never final submit')


@pytest.fixture(autouse=True)
def audit():
    """Override the legacy autouse audit which requires a Visitor case parameter."""
    yield


@pytest.fixture
def tsp_data():
    data = json.loads((ROOT / 'data/tsp_application_data.json').read_text(encoding='utf-8'))
    assert data['home_url'] == 'https://apptourlfr-stg.estpl.net/en/home'
    assert set(data['documents']) == {str(n) for n in range(1, 12)}
    paths = list(data['documents'].items()) + [
        ('staff', data['staff']['qualification_file'])]
    # Normal staff flow is IITTM No. Preserve preflight for the opt-in diagnostic.
    if os.getenv('TSP_UPLOAD_DOM_DIAGNOSTIC') == '1':
        paths.append(('staff', data['staff']['iittm_file']))
    for slot, relative in paths:
        path = (ROOT / relative).resolve()
        assert path.is_relative_to((ROOT / 'test_data').resolve()), 'Test PDF must be inside test_data'
        assert path.is_file(), f'Missing authorized fixture: {relative}'
        with path.open('rb') as stream:
            assert stream.read(5) == b'%PDF-', f'Invalid PDF signature: {relative}'
        assert path.stat().st_size <= (1 if slot == '11' else 5) * 1000 * 1000
    return data


@pytest.fixture
def tsp_session(request, playwright, tsp_data):
    if not request.config.getoption('--tsp-attended'):
        pytest.skip('Attended TSP run requires --tsp-attended and manual CAPTCHA.')
    if os.getenv('PYTEST_XDIST_WORKER') or getattr(request.config.option, 'numprocesses', 0):
        pytest.skip('Run attended TSP without xdist.')
    if request.config.getoption('capture') != 'no':
        pytest.skip('Use -s for explicit terminal CAPTCHA confirmation.')
    if os.getenv('DEBUG') or os.getenv('PWDEBUG'):
        pytest.skip('Disable DEBUG/PWDEBUG before entering credentials.')
    load_dotenv(ROOT / '.env', override=True)
    if not all(os.getenv(k, '').strip() for k in ('TSP_EMAIL', 'TSP_PASSWORD')):
        pytest.skip('Configure TSP_EMAIL and TSP_PASSWORD in the project-root .env.')
    # Parse only the hold setting; never echo its raw environment value.
    try:
        hold_seconds = float(os.getenv('TSP_BROWSER_HOLD_SECONDS', '60'))
        if not math.isfinite(hold_seconds) or hold_seconds < 0:
            raise ValueError()
    except ValueError:
        hold_seconds = 60.0
        print('Invalid TSP_BROWSER_HOLD_SECONDS; using the 60-second default.', flush=True)

    browser = playwright.chromium.launch(headless=False)
    context = None
    test_started = False
    try:
        context = browser.new_context(viewport={'width': 1366, 'height': 900})
        context.set_default_timeout(15000)
        context.set_default_navigation_timeout(60000)
        page = context.new_page()
        # No video/trace: hidden login inputs may retain secrets after authentication.
        diagnostics = {'console_errors': 0, 'runtime_errors': 0, 'failed_requests': 0, 'http_error_statuses': []}
        def console(message):
            if message.type == 'error':
                diagnostics['console_errors'] += 1
        def runtime(_):
            diagnostics['runtime_errors'] += 1
        def failed(_):
            diagnostics['failed_requests'] += 1
        def response(res):
            if res.status >= 400:
                diagnostics['http_error_statuses'].append(res.status)
        page.on('console', console)
        page.on('pageerror', runtime)
        page.on('requestfailed', failed)
        page.on('response', response)
        test_started = True
        yield page
    finally:
        try:
            if test_started:
                allure.attach(
                    json.dumps(diagnostics),
                    'Sanitized diagnostics (counts only)',
                    allure.attachment_type.JSON
                )
        finally:
            try:
                if test_started and hold_seconds > 0:
                    print(f'TSP automation stopped. Browser inspection period: {hold_seconds:g} seconds; automatic cleanup follows.', flush=True)
                    deadline = time.monotonic() + hold_seconds
                    # Pump Playwright events while its dependency fixture remains alive.
                    while browser.is_connected():
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            break
                        pages = [p for c in browser.contexts for p in c.pages if not p.is_closed()]
                        if not pages:
                            break
                        try:
                            pages[0].wait_for_timeout(min(250, remaining * 1000))
                        except PlaywrightError:
                            # Browser/page closure or driver failure: proceed to cleanup.
                            break
            finally:
                # Both closures are attempted even on setup/test/attachment/hold failure.
                try:
                    if context is not None:
                        context.close()
                except PlaywrightError:
                    print('TSP context cleanup could not complete or context was already closed.', flush=True)
                finally:
                    try:
                        browser.close()
                    except PlaywrightError:
                        print('TSP browser cleanup could not complete or browser was already closed.', flush=True)
