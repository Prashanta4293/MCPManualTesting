"""Evidence and explicit human-confirmation fixtures for workbook login cases."""
import json
import os
from pathlib import Path
import secrets
import tempfile
import time
from urllib.parse import urlsplit

import allure
import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
# Explicit project-root file only; never read .env.example or modify .env.
load_dotenv(ROOT / '.env', override=True)
LOGIN_ENV = {key: os.environ.get(key) for key in ('VISITOR_EMAIL', 'VISITOR_PASSWORD')}


def clean(value):
    value = str(value)
    for secret in LOGIN_ENV.values():
        if secret:
            value = value.replace(secret, '[REDACTED]')
    return value


def pytest_addoption(parser):
    parser.addoption('--visitor-evidence-dir', default='test-results/visitor-login')
    parser.addoption('--captcha-confirm-dir', default=None,
                     help='Private local confirmation handshake directory for an attended run.')


class VisitorAudit:
    def __init__(self):
        self.console, self.network, self.observations = [], [], []
        self.screenshot = self.trace = self.video = None
        self.url = None
        self.sensitive = False
        self.started = time.monotonic()
        self.block_reason = None
        self.tracing = False
        self.authenticated = False

    def record(self, observation):
        self.observations.append(observation)

    def destination(self):
        pass

    def connect(self, page):
        def console(message):
            if message.type == 'error':
                self.console.append({'message': 'Console error during private login; text suppressed' if self.sensitive else clean(message.text)})
        def error(exc):
            self.console.append({'message': 'Runtime error during private login; text suppressed' if self.sensitive else clean(str(exc))})
        def network(response=None, request=None):
            item = response or request
            u = urlsplit(item.url)
            entry = {'url': clean(f'{u.scheme}://{u.netloc}{u.path}')}
            if response:
                entry['status'] = response.status
            else:
                entry['error'] = request.failure
            self.network.append(entry)
        page.on('console', console)
        page.on('pageerror', error)
        page.on('requestfailed', lambda req: network(request=req))
        page.on('response', lambda res: network(response=res) if res.status >= 400 else None)


@pytest.fixture
def visitor_audit(request):
    case = request.node.callspec.params['case']
    audit = VisitorAudit()
    request.node._visitor_audit = audit
    title = f"{case['Test Case ID']} {case['Test Case Description']}"
    description = '\n'.join(f'{key}: {case.get(key) or "Not specified in workbook"}' for key in
                            ('Scenario','Field Name/Reference','Test Case Description','Preconditions','Steps','Expected Result'))
    def metadata():
        allure.dynamic.title(title)
        allure.dynamic.epic('Odisha Tourism')
        allure.dynamic.parent_suite('Odisha Tourism')
        allure.dynamic.suite('Visitor Login workbook TC16–TC41')
        allure.dynamic.feature('Visitor Login')
        allure.dynamic.story(case['Scenario'])
        allure.dynamic.severity('critical' if case['Severity'] == 'High' else 'normal')
        allure.dynamic.description(description)
        allure.dynamic.parameter('case', case['Test Case ID'])
    metadata()
    allure.attach(case['Expected Result'], 'Expected result', allure.attachment_type.TEXT)
    allure.attach('Workbook Test Data: not specified. Synthetic inputs for stable cases; environment credentials only for attended cases. Password values omitted.', 'Test data (passwords omitted)', allure.attachment_type.TEXT)
    yield audit
    metadata()
    report = getattr(request.node, 'rep_call', getattr(request.node, 'rep_setup', None))
    status = 'Not Executed' if not report else {'passed':'Passed','failed':'Failed','skipped':'Blocked'}[report.outcome]
    error = clean(str(report.longrepr)) if report and report.longrepr else None
    result = {
        'id':case['Test Case ID'], 'status':status, 'automation':case['automation'],
        'actual': {'observations':audit.observations, 'failure':error, 'blocked_reason':audit.block_reason},
        'expected_result':case['Expected Result'], 'duration_seconds':round(time.monotonic()-audit.started,3),
        'tested_url':audit.url, 'screenshot':audit.screenshot, 'trace':audit.trace, 'video':audit.video,
        'console_errors':audit.console, 'failed_network_requests':audit.network,
        'defect_description':error if status == 'Failed' else None,
        'execution':'Python pytest Chromium',
    }
    folder = Path(request.config.getoption('--visitor-evidence-dir'))
    folder.mkdir(parents=True, exist_ok=True)
    (folder/f"{case['Test Case ID']}.json").write_text(json.dumps(result,indent=2),encoding='utf-8')
    for name, content in [('Actual result',result['actual']),('Tested URL',audit.url),('Console errors',audit.console),('Network errors',audit.network)]:
        allure.attach(json.dumps(content,indent=2),name,allure.attachment_type.JSON)


@pytest.fixture
def visitor_session(request, visitor_audit, playwright):
    audit = visitor_audit
    attended = bool(request.node.get_closest_marker('manual_captcha'))
    audit.sensitive = attended
    if attended:
        reason = None
        if not request.config.getoption('--manual-login'):
            reason = 'An attended --manual-login run and explicit CAPTCHA confirmation are required.'
        elif not all(LOGIN_ENV.values()):
            reason = 'VISITOR_EMAIL and VISITOR_PASSWORD are not available in the process environment.'
        elif os.getenv('DEBUG') or os.getenv('PWDEBUG'):
            reason = 'Disable DEBUG/PWDEBUG to prevent credential logging.'
        if reason:
            audit.block_reason = reason
            pytest.skip('BLOCKED: '+reason)
    id = request.node.callspec.params['case']['Test Case ID']
    folder = Path(request.config.getoption('--visitor-evidence-dir')).resolve()/id
    folder.mkdir(parents=True,exist_ok=True)
    browser = playwright.chromium.launch(headless=False if attended else not request.config.getoption('headed'))
    with tempfile.TemporaryDirectory(prefix='visitor-video-') as temp:
        options = {'viewport':{'width':1366,'height':900}}
        if not attended:
            options['record_video_dir'] = temp
        context = browser.new_context(**options)
        context.set_default_timeout(10000)
        context.set_default_navigation_timeout(35000)
        if not attended:
            context.tracing.start(screenshots=True,snapshots=True,sources=False)
            audit.tracing = True
        page = context.new_page()
        audit.connect(page)
        yield page
        report = getattr(request.node,'rep_call',None)
        failed = bool(report and report.failed)
        audit.url = clean(page.url.split('?')[0])
        if not page.is_closed() and (not attended or audit.authenticated):
            target = folder/'screenshot.png'
            try:
                masks = [page.locator('body')] if attended else [page.locator('#otLoginPassword')]
                page.screenshot(path=str(target),mask=masks,timeout=10000)
                audit.screenshot = str(target)
                allure.attach.file(str(target),'Failure screenshot' if failed else 'Execution screenshot',allure.attachment_type.PNG)
            except Exception:
                audit.record({'screenshot_limitation':'Page screenshot unavailable; no unmasked sensitive fallback used.'})
        if audit.tracing:
            if failed:
                trace = folder/'trace.zip'
                context.tracing.stop(path=str(trace))
                audit.trace = str(trace)
            else:
                context.tracing.stop()
        if failed and audit.trace:
            allure.attach.file(audit.trace,'Pre-credential trace (privacy limited)' if attended else 'Failure trace', 'application/zip','zip')
        video = page.video
        context.close()
        if failed and video:
            target = folder/'failure.webm'
            video.save_as(str(target))
            audit.video = str(target)
            allure.attach.file(str(target),'Failure video',allure.attachment_type.WEBM)
        if attended:
            allure.attach('Attended login has no trace or video. A fully masked screenshot is taken only after authenticated login is verified and the login dialog is hidden. No form screenshot is taken on failure or while awaiting CAPTCHA.', 'Credential evidence limitations',allure.attachment_type.TEXT)
        browser.close()


@pytest.fixture
def captcha_confirmation(request, visitor_audit):
    """Never interpret blur/nonempty CAPTCHA as the user's confirmation."""
    def confirm(page):
        id = request.node.callspec.params['case']['Test Case ID']
        directory = request.config.getoption('--captcha-confirm-dir')
        if not directory:
            print(f'{id}: Enter CAPTCHA in the visible browser, then type CONFIRM here. No submission occurs before confirmation.',flush=True)
            try:
                answer = input().strip()
            except (EOFError,OSError):
                answer = ''
            if answer != 'CONFIRM':
                pytest.skip('BLOCKED: Explicit human CAPTCHA confirmation was not received.')
            return
        directory = Path(directory)
        directory.mkdir(parents=True,exist_ok=True)
        token = secrets.token_hex(16)
        ready = directory/f'{id}-ready.json'
        reply = directory/f'{id}-confirmed.json'
        ready.write_text(json.dumps({'id':id,'token':token,'instruction':'Enter CAPTCHA, then explicitly confirm in chat; do not send CAPTCHA text.'}),encoding='utf-8')
        print(f'CAPTCHA_READY {id}: enter CAPTCHA in headed Chromium and confirm in chat.',flush=True)
        deadline = time.monotonic()+300
        while time.monotonic()<deadline:
            if reply.exists():
                confirmation = json.loads(reply.read_text(encoding='utf-8'))
                if confirmation.get('token') == token and confirmation.get('confirmed') is True:
                    return
            page.wait_for_timeout(250)
        visitor_audit.block_reason = 'No explicit CAPTCHA confirmation received within five minutes.'
        pytest.skip('BLOCKED: '+visitor_audit.block_reason)
    return confirm
