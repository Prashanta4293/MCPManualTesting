import os
import re
import secrets
from playwright.sync_api import expect, TimeoutError as PlaywrightTimeoutError
from .home_page import HomePage

class VisitorLoginPage(HomePage):
    @property
    def username(self):
        return self.page.locator('#otLoginEmail')

    @property
    def password(self):
        return self.page.locator('#otLoginPassword')

    @property
    def captcha_display(self):
        return self.page.locator('#otlxCaptchaDisplay')

    def check_field(self, locator):
        expect(locator).to_be_visible()
        expect(locator).to_be_editable()
        box, parent = locator.bounding_box(), self.dialog.bounding_box()
        assert box and parent and box['width'] > 0 and box['height'] > 0
        assert parent['x'] <= box['x'] and box['x']+box['width'] <= parent['x']+parent['width'], 'Field extends outside popup'
        self.audit.record({'field':locator.get_attribute('placeholder'),'visible':True,'inside_dialog':True})

    def select_role(self, role):
        button = self.dialog.get_by_role('button',name=role,exact=True)
        expect(button).to_be_visible()
        button.click()
        expect(self.page.locator('#otlxRole')).to_have_value(role)
        expect(self.username).to_be_visible()
        expect(self.password).to_be_visible()
        self.audit.record({'selected_role':role,'login_form_visible':True})

    def submit_and_check_error(self, pattern):
        self.page.locator('#otLoginSubmit').click()
        error = self.page.locator('#otLoginError')
        expect(error).to_be_visible()
        expect(error).to_contain_text(re.compile(pattern,re.I))
        expect(self.dialog).to_be_visible()
        self.audit.record({'validation_message':error.inner_text()})

    def verify_workbook_case(self, case):
        """Implement the selected workbook expectations, not its historical statuses."""
        id, p = case['Test Case ID'], self.page
        if id == 'TC16':
            expect(self.dialog).to_be_visible()
            expect(self.dialog).to_have_attribute('aria-modal','true')
        elif id == 'TC17':
            expect(self.dialog.get_by_role('heading',name='Login',exact=True)).to_be_visible()
        elif id == 'TC18':
            expect(self.dialog.locator('p').filter(has_text='Welcome')).to_have_text('Welcome Back! Login to continue to your account')
        elif id == 'TC19':
            self.dialog.get_by_role('button',name='Close',exact=True).click()
            expect(self.dialog).not_to_be_visible()
        elif id in ('TC20','TC21','TC22','TC23'):
            roles = {'TC20':['Visitor'],'TC21':['Hotelier'],'TC22':['Travel Agent'],'TC23':['Visitor','Hotelier','Travel Agent']}[id]
            for role in roles:
                self.select_role(role)
        elif id == 'TC24':
            self.check_field(self.username)
        elif id in ('TC25','TC26'):
            value = 'test@odishatourism.gov.in' if id == 'TC25' else '9876543210'
            self.username.fill(value)
            expect(self.username).to_have_value(value)
            assert self.username.evaluate('(e)=>e.validity.valid'), 'Input reports invalid syntax'
            self.audit.record({'accepted_input':value,'submission_performed':False})
        elif id in ('TC27','TC41'):
            self.submit_and_check_error(r'(email|mobile).*required')
        elif id == 'TC28':
            self.check_field(self.password)
        elif id in ('TC29','TC30','TC31'):
            self.password.fill('Disposable-'+secrets.token_hex(8))
            assert self.password.evaluate('(e)=>e.value.length>0'), 'Password entry failed'
            if id in ('TC30','TC31'):
                expect(self.password).to_have_attribute('type','password')
            if id == 'TC31':
                p.locator('#togglePassword').click()
                expect(self.password).to_have_attribute('type','text')
                p.locator('#togglePassword').click()
                expect(self.password).to_have_attribute('type','password')
            self.audit.record({'entry_accepted':True,'default_masked':id in ('TC30','TC31'),'toggle_verified':id=='TC31','password_value':'omitted; disposable input'})
        elif id == 'TC32':
            self.username.fill('test@odishatourism.gov.in')
            self.submit_and_check_error(r'password.*required')
        elif id == 'TC33':
            self.check_field(p.locator('#otLoginCaptchaInput'))
        elif id == 'TC34':
            expect(self.captcha_display).to_be_visible(timeout=10000)
            assert self.captcha_display.evaluate('(e)=>e.childNodes.length>0'), 'CAPTCHA content not generated'
            self.audit.record({'captcha_generated':True,'captcha_read_or_solved':False})
        elif id == 'TC35':
            initial_visible = self.captcha_display.is_visible()
            # The workbook precondition is a loaded CAPTCHA. Refresh can establish it,
            # while TC34 separately checks generation without a recovery click.
            p.locator('#otlxRefreshCaptcha').click()
            expect(self.captcha_display).to_be_visible()
            before = self.captcha_display.screenshot()
            p.locator('#otlxRefreshCaptcha').click()
            self.poll(lambda: self.captcha_display.screenshot()!=before,timeout=10000)
            self.audit.record({'initial_visible':initial_visible,'refresh_changes_rendered_pixels':True,'captcha_read_or_solved':False})
        elif id == 'TC37':
            self.username.fill('visitor-negative@example.invalid')
            self.password.fill('Disposable-'+secrets.token_hex(8))
            p.locator('#otLoginCaptchaInput').fill('intentionally-invalid-captcha')
            self.submit_and_check_error(r'(incorrect|invalid).*captcha')
        elif id == 'TC38':
            button = p.locator('#otLoginSubmit')
            expect(button).to_be_visible()
            expect(button).to_be_enabled()
            expect(button).to_have_text('Login')
            assert button.bounding_box()['width']>0
        else:
            raise AssertionError(f'No stable implementation for {id}')
        self.audit.record({'case':id,'workbook_expectation_verified':True,'url':p.url})

    def attended_workbook_login(self, case, credentials, confirmation, trace_path):
        self.login_stage = 'Preparing Visitor login'
        # Attended runs record no trace/video, including anonymous setup.
        if self.audit.tracing:
            self.page.context.tracing.stop()
            self.audit.tracing = False
        self.audit.sensitive = True
        self.select_role('Visitor')
        if not self.captcha_display.is_visible():
            self.page.locator('#otlxRefreshCaptcha').click()
            expect(self.captcha_display).to_be_visible()
            self.audit.record({'captcha_refreshed_to_recover_initial_blank':True})
        self.username.evaluate("e => e.style.setProperty('-webkit-text-security','disc','important')")
        self.username.fill(credentials['VISITOR_EMAIL'])
        value = 'Deliberately-wrong-'+secrets.token_hex(16) if case['Test Case ID']=='TC40' else credentials['VISITOR_PASSWORD']
        self.password.fill(value)
        del value
        captcha = self.page.locator('#otLoginCaptchaInput')
        captcha.focus()
        confirmation(self.page)
        self.login_stage = 'Human confirmed CAPTCHA'
        assert captcha.evaluate('(e)=>e.value.trim().length>0'), 'Confirmed CAPTCHA field is empty; no submission performed'
        if case['Test Case ID']=='TC40':
            self.submit_and_check_error(r'(invalid|incorrect|wrong|failed).*(credential|password|login)|(credential|password).*(invalid|incorrect|wrong)')
            assert 'captcha' not in self.page.locator('#otLoginError').inner_text().lower(), 'CAPTCHA rejection does not verify invalid credentials'
        else:
            def diagnostic_response(response):
                from urllib.parse import urlsplit
                path = urlsplit(response.url).path
                if path == '/o/user-login/login':
                    self.audit.record({'authentication_api_status':response.status})
                elif response.request.is_navigation_request() and response.frame == self.page.main_frame:
                    self.audit.record({'navigation_http_status':response.status,'known_visitor_landing':path=='/visitor-landing'})
            self.page.on('response',diagnostic_response)
            self.login_stage = 'Click Login'
            self.page.locator('#otLoginSubmit').click()
            self.audit.record({'login_button_clicked':True})
            self.login_stage = 'Wait for login popup to close'
            expect(self.dialog).not_to_be_visible(timeout=15000)
            self.login_stage = 'Verify authenticated Visitor dashboard'
            expect(self.page).to_have_url(re.compile(r'^https://apptourlfr-stg\.estpl\.net/visitor-landing/?(?:[?#].*)?$'),timeout=15000)
            self.page.wait_for_function("() => window.Liferay?.ThemeDisplay?.isSignedIn?.() === true",timeout=15000)
            # The authenticated dashboard does not expose the homepage profile icon.
            # Check the signed-in page's main content, not a homepage-only control.
            dashboard = self.page.locator('body.signed-in').get_by_role('main').first
            expect(dashboard).to_be_visible(timeout=15000)
            expect(self.page.locator('main.error-page-wrapper')).to_have_count(0)
            expect(self.dialog).not_to_be_visible()
            self.audit.authenticated = True
            self.audit.record({'authenticated':True,'evidence':'Visitor dashboard URL, signed-in session and visible main content verified; identity omitted'})

    def record_private_login_diagnosis(self):
        """Only booleans and fixed labels; never attach DOM text or response bodies."""
        state = {'assertion_stage':getattr(self,'login_stage','Anonymous setup')}
        try:
            state.update(self.page.evaluate('''() => ({
                signed_in: typeof window.Liferay?.ThemeDisplay?.isSignedIn === 'function' ? !!window.Liferay.ThemeDisplay.isSignedIn() : null,
                error_page: !!document.querySelector('main.error-page-wrapper'),
                title_indicates_404: /404/.test(document.title),
                title_indicates_500: /500/.test(document.title),
                visitor_landing: location.pathname === '/visitor-landing'
            })'''))
            state['login_popup_visible'] = self.dialog.is_visible()
            state['profile_control_visible'] = self.page.locator('#otUserIconBtn').is_visible()
            state['logout_control_visible'] = self.page.locator('a:visible,button:visible').filter(has_text=re.compile(r'^\s*(log\s*out|sign\s*out)\s*$',re.I)).first.is_visible()
            error = self.page.locator('#otLoginError')
            if error.is_visible():
                message = error.inner_text()
                state['captcha_error_visible'] = bool(re.search(r'captcha',message,re.I))
                state['credential_error_visible'] = bool(re.search(r'invalid|incorrect|password|credential',message,re.I))
                del message
        except Exception:
            state['diagnostic_limitation'] = 'Some page-state checks unavailable'
        self.audit.record(state)

    @property
    def dialog(self):
        return self.page.locator('[role="dialog"][aria-labelledby="otlxTitle"]')

    def verify_account_case(self, case):
        p, id = self.page, case['Test Case ID']
        self.open_login()
        if id == 'ACCOUNT-001':
            for name in ['Email ID / Mobile Number','Password','Enter Captcha']:
                expect(self.dialog.get_by_placeholder(name,exact=True)).to_be_visible()
            for text in ['Forgot Password','Sign Up','Official Login']:
                expect(self.dialog).to_contain_text(text)
            self.dialog.locator('button[aria-label="Close"]').click()
            expect(self.dialog).not_to_be_visible()
        else:
            names = {'ACCOUNT-ForgotPassword':'Forgot Password?','ACCOUNT-SignUp':'Sign Up','ACCOUNT-OfficialLogin':'Official Login'}
            self.dialog.get_by_text(names[id],exact=True).click()
            expect(p).to_have_url(case['Tested URL'])
            content = {'ACCOUNT-ForgotPassword':'Back to Login','ACCOUNT-SignUp':'Register Here','ACCOUNT-OfficialLogin':'Official Portal Login'}
            expect(p.locator('body')).to_contain_text(content[id])
            if id == 'ACCOUNT-SignUp':
                expect(p.locator('[class*="breadcrumb"]').first).to_contain_text('Visitor Registration')
            if id != 'ACCOUNT-ForgotPassword':
                self.image_audit()
            else:
                expect(self.dialog.get_by_placeholder('Email ID / Mobile Number',exact=True)).to_be_visible()
            self.healthy()
        self.audit.record({'url':p.url,'title':p.title(),'language':p.locator('html').get_attribute('lang'),'content':p.locator('body').inner_text()[:10000]})

    def positive_login(self):
        self.open_login()
        # No secret is passed to an Allure step or pytest parameter; logging and recording are disabled.
        self.dialog.get_by_placeholder('Email ID / Mobile Number',exact=True).fill(os.environ['VISITOR_EMAIL'])
        self.dialog.get_by_placeholder('Password',exact=True).fill(os.environ['VISITOR_PASSWORD'])
        captcha = self.dialog.get_by_placeholder('Enter Captcha',exact=True)
        captcha.focus()
        print('Enter the complete displayed CAPTCHA in headed Chromium, then press Tab when finished (within 120 seconds).', flush=True)
        try:
            self.page.wait_for_function('(element) => element.value.trim().length > 0 && document.activeElement !== element', arg=captcha.element_handle(), timeout=120000)
        except PlaywrightTimeoutError:
            return False
        # Only non-emptiness and the human's focus change are checked; CAPTCHA text is never extracted or changed.
        self.dialog.get_by_role('button',name='Login',exact=True).click()
        expect(self.dialog).not_to_be_visible(timeout=15000)
        self.page.locator('#otUserIconBtn').click()
        # A disappeared dialog alone does not prove authentication.
        logout = self.page.locator('a:visible,button:visible').filter(has_text=re.compile(r'^\s*(log\s*out|sign\s*out)\s*$',re.I))
        expect(logout.first).to_be_visible(timeout=15000)
        self.audit.record({'authenticated':True,'evidence':'Visible authenticated logout control; identity omitted'})
        return True
