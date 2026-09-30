import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import quote, quote_plus

import allure
from dotenv import load_dotenv
import pytest
from playwright.sync_api import expect
from pages.data import ROOT, HOME, case_name

load_dotenv(ROOT / '.env', override=False)
expect.set_options(timeout=10000)

def redact(value):
    text = str(value)
    for key in ('VISITOR_EMAIL', 'VISITOR_PASSWORD'):
        secret = os.getenv(key)
        if secret:
            for encoded in (secret, quote(secret, safe=''), quote_plus(secret)):
                text = text.replace(encoded, '[REDACTED]')
    return text

def attach_json(name, value):
    allure.attach(redact(json.dumps(value, ensure_ascii=False, indent=2)), name, allure.attachment_type.JSON)

def pytest_addoption(parser):
    parser.addoption('--manual-login', action='store_true', help='Enable attended headed visitor login with environment credentials and human CAPTCHA.')

def pytest_configure(config):
    config._execution_records = []

def pytest_collection_modifyitems(config, items):
    for item in items:
        case = getattr(item, 'callspec', None)
        if case and 'case' in case.params:
            item.user_properties.append(('case_name', case_name(case.params['case'])))

def pytest_collection_finish(session):
    if session.config.option.collectonly and not hasattr(session.config, 'workerinput'):
        records = [{'nodeid':item.nodeid,'name':dict(item.user_properties).get('case_name',item.nodeid)} for item in session.items]
        out = ROOT / 'migration'
        out.mkdir(exist_ok=True)
        (out/'python-collection.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')

@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if item.get_closest_marker('positive') and call.excinfo and report.failed:
        # Playwright call logs may contain fill values. Never persist a positive-login traceback.
        if report.failed:
            report.longrepr = 'Positive visitor login failed; sensitive call details suppressed. See sanitized Allure observations.'
        call.excinfo.value.args = ('Positive visitor login did not complete; sensitive details suppressed.',)
    setattr(item, 'rep_' + report.when, report)
    report.user_properties = list(item.user_properties)
    report.user_properties.append(('attempt', getattr(item, 'execution_count', 1)))

def pytest_runtest_logreport(report):
    # A dedicated JSON record stream is written by each worker, independent of Allure presentation.
    if report.when == 'call' or (report.when == 'setup' and report.outcome != 'passed') or (report.when == 'teardown' and report.failed):
        record = {'nodeid': report.nodeid, 'name': dict(report.user_properties).get('case_name', report.nodeid), 'phase': report.when, 'outcome': report.outcome, 'attempt': dict(report.user_properties).get('attempt', 1), 'duration': report.duration, 'error': redact(str(report.longrepr)) if report.longrepr else ''}
        out = ROOT / 'test-results/python'
        out.mkdir(parents=True, exist_ok=True)
        worker = os.environ.get('PYTEST_XDIST_WORKER', 'main')
        with (out / f'events-{worker}.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

class Audit:
    def __init__(self, sensitive=False):
        self.console, self.network, self.observations, self.errors = [], [], [], []
        self.phase, self.sensitive = 'home', sensitive

    def record(self, value):
        self.observations.append(value)

    def destination(self):
        self.phase = 'destination'

    def check(self, condition, message, actual=None):
        if not condition:
            self.errors.append({'message': message, 'actual': actual})

    def finish(self):
        if self.errors:
            pytest.fail(redact(json.dumps(self.errors, ensure_ascii=False, indent=2)), pytrace=False)

    def connect(self, context):
        def page_opened(page):
            if self.sensitive:
                return  # No credential-bearing browser logs, URLs, response bodies or DOM snapshots.
            page.on('console', lambda m: self.console.append({'phase': self.phase, 'page': page.url, 'text': m.text, 'location': m.location}) if m.type == 'error' else None)
            page.on('pageerror', lambda e: self.console.append({'phase': self.phase, 'page': page.url, 'text': str(e), 'type': 'uncaught'}))
        context.on('page', page_opened)
        if not self.sensitive:
            context.on('requestfailed', lambda r: self.network.append({'phase': self.phase, 'url': r.url, 'method': r.method, 'error': r.failure}))
            context.on('response', lambda r: self.network.append({'phase': self.phase, 'url': r.url, 'status': r.status}) if r.status >= 400 else None)

@pytest.fixture(autouse=True)
def audit(request):
    case = request.node.callspec.params['case']
    positive = bool(request.node.get_closest_marker('positive'))
    result = Audit(sensitive=positive)
    request.node._audit = result
    name = case_name(case)
    allure.dynamic.title(name)
    allure.dynamic.parent_suite('Odisha Tourism')
    allure.dynamic.suite(case['Module'])
    hotel = case['Test Case ID'] == 'HOTEL-DATA-001'
    allure.dynamic.feature('Header navigation' if case['Test Case ID'].startswith('NAV') else 'Hotels' if hotel else case['Module'])
    allure.dynamic.story(name if hotel else case['Test Scenario'])
    allure.dynamic.severity({'High':'critical', 'Medium':'normal', 'Low':'minor'}.get(case.get('Severity'), 'normal'))
    allure.dynamic.description(f"{case['Test Scenario']}\nPreconditions: {case.get('Preconditions', '')}\nSteps: {case.get('Test Steps', '')}\nData: {case.get('Test Data', '')}\nEvidence: {case.get('Evidence/Screenshot', '')}\nHistorical results are not current outcomes.")
    # Hide pytest's verbose dict parameter in the report; it contains evidence, never credentials.
    allure.dynamic.parameter('case', case['Test Case ID'])
    allure.attach(case['Expected Result'], 'Expected result', allure.attachment_type.TEXT)
    yield result
    # allure-pytest fills its default name/description after fixture setup;
    # reapply the preserved manual identity during teardown, including blocked setup cases.
    allure.dynamic.title(name)
    allure.dynamic.description(f"{case['Test Scenario']}\nPreconditions: {case.get('Preconditions', '')}\nSteps: {case.get('Test Steps', '')}\nData: {case.get('Test Data', '')}\nEvidence: {case.get('Evidence/Screenshot', '')}\nHistorical results are not current outcomes.")
    report = getattr(request.node, 'rep_call', getattr(request.node, 'rep_setup', None))
    attach_json('Console errors', result.console if not positive else {'omitted': 'Credential privacy'})
    attach_json('Network errors', result.network if not positive else {'omitted': 'Credential privacy'})
    attach_json('Actual result', {'status': report.outcome if report else 'setup incomplete', 'attempt': getattr(request.node, 'execution_count', 1), 'observations': result.observations, 'errors': result.errors, 'failure': redact(str(report.longrepr)) if report and report.longrepr else None})
    if positive and not hasattr(request.node, 'rep_call'):
        attach_json('Tested URL', {'expected':HOME,'visited':False,'reason':'Manual login prerequisites unavailable'})

@pytest.fixture
def context(request, audit):
    positive = bool(request.node.get_closest_marker('positive'))
    if positive:
        if not request.config.getoption('--manual-login'):
            pytest.skip('BLOCKED: Positive login needs an attended --manual-login run and manual CAPTCHA.')
        if not all(os.getenv(k) for k in ('VISITOR_EMAIL','VISITOR_PASSWORD')):
            pytest.skip('BLOCKED: Configure VISITOR_EMAIL and VISITOR_PASSWORD privately in the environment.')
        if os.getenv('DEBUG') or os.getenv('PWDEBUG'):
            pytest.skip('BLOCKED: Disable DEBUG and PWDEBUG before credential entry so API call logging cannot expose credentials.')
        browser = request.getfixturevalue('playwright').chromium.launch(headless=False)
    else:
        browser = request.getfixturevalue('browser')
    attempt = getattr(request.node, 'execution_count', 1)
    case = request.node.callspec.params['case']
    out = ROOT / 'test-results/python' / f"{case['Test Case ID']}-attempt-{attempt}"
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='odisha-video-') as temp:
        args = {'viewport': {'width':1366,'height':900}, 'ignore_https_errors':False}
        if not positive:
            args['record_video_dir'] = temp
        ctx = browser.new_context(**args)
        ctx.set_default_timeout(15000)
        ctx.set_default_navigation_timeout(35000)
        audit.connect(ctx)
        tracing = attempt == 2 and not positive
        if tracing:
            ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
        try:
            yield ctx
        finally:
            report = getattr(request.node, 'rep_call', getattr(request.node, 'rep_setup', None))
            failed = bool(report and report.failed)
            attach_json('Tested URL', [HOME + ' [authentication URL suppressed]'] if positive else [p.url for p in ctx.pages])
            videos = []
            for i, p in enumerate(ctx.pages):
                if failed:
                    try:
                        target = out / f'failure-{i+1}.png'
                        # Mask the entire authenticated page, including any profile identity.
                        p.screenshot(path=str(target), full_page=True, mask=[p.locator('body')] if positive else [], timeout=10000)
                        allure.attach.file(str(target), f'Failure screenshot page {i+1}', allure.attachment_type.PNG)
                    except Exception:
                        allure.attach('Screenshot capture unavailable; sensitive details suppressed.', 'Screenshot limitation', allure.attachment_type.TEXT)
                if p.video:
                    videos.append(p.video)
            if tracing:
                trace = out / 'trace.zip'
                ctx.tracing.stop(path=str(trace))
                allure.attach.file(str(trace), 'trace', 'application/zip', 'zip')
            if not positive and ctx.pages and ctx.pages[0].url != HOME:
                try:
                    ctx.pages[0].goto(HOME, wait_until='domcontentloaded', timeout=15000)
                except Exception as e:
                    allure.attach(redact(str(e)), 'Return home error', allure.attachment_type.TEXT)
            ctx.close()
            if failed:
                for i, video in enumerate(videos):
                    target = out / f'failure-{i+1}.webm'
                    video.save_as(str(target))
                    allure.attach.file(str(target), f'Failure video page {i+1}', allure.attachment_type.WEBM)
            if positive:
                browser.close()

@pytest.fixture
def page(context):
    return context.new_page()
