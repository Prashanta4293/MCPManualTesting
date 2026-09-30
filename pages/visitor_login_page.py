import os
import re
from playwright.sync_api import expect, TimeoutError as PlaywrightTimeoutError
from .home_page import HomePage

class VisitorLoginPage(HomePage):
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
