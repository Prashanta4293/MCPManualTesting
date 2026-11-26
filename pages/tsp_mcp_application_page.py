import re
import os

import allure
import pytest

from playwright.sync_api import Locator, Page, expect


class TspMcpApplicationPage:
    ORIGIN = 'https://apptourlfr-stg.estpl.net'
    SECTIONS = (
        'Application Type', 'Applicant Details', 'Office Details',
        'HR & Certification', 'Transport Details', 'Documents',
        'Declaration', 'Preview & Submit',
    )
    
    def __init__(self, page: Page):
        self.page = page
        self.content = page.locator('#stepContent')
        self.authenticated = False
        self.login_stage = 'Not started'
        self.login_error = None
        self.dashboard_freshness_verified = False
        self.apply_click_attempted = False
        self.apply_clicked = False

    def login_attended(self) -> None:
        """Same selectors and manual CONFIRM flow as the existing positive login."""
        with allure.step('TSP MCP attended login with manual CAPTCHA'):
            try:
                self.login_stage = 'Load UAT home page'
                self.page.goto(self.ORIGIN + '/en/home', wait_until='domcontentloaded')
                self.login_stage = 'Open profile login popup'
                self.page.locator('#otUserIconBtn').click()
                self.login_stage = 'Select TSP user type'
                self.page.get_by_role('button', name='TSP', exact=True).click()
                self.login_stage = 'Enter private email'
                email = self.page.locator('#otLoginEmail')
                email.evaluate("e => e.style.setProperty('-webkit-text-security','disc','important')")
                email.fill(os.environ['TSP_EMAIL'])
                self.login_stage = 'Enter private password'
                self.page.locator('#otLoginPassword').fill(os.environ['TSP_PASSWORD'])
                self.login_stage = 'Focus manual CAPTCHA'
                self.page.locator('#otLoginCaptchaInput').focus()
                self.login_stage = 'Await manual CAPTCHA confirmation'
                print('Enter CAPTCHA in the visible TSP browser. Type CONFIRM here to click Login once. Do not type credentials or CAPTCHA in the terminal.', flush=True)
                try:
                    confirmation = input().strip()
                except (EOFError, OSError):
                    confirmation = ''
                if confirmation != 'CONFIRM':
                    pytest.skip('Explicit CAPTCHA confirmation not received; no login submitted.')
                self.login_stage = 'Verify CAPTCHA entered'
                assert self.page.locator('#otLoginCaptchaInput').evaluate(
                    '(e) => e.value.trim().length > 0'), 'CAPTCHA field is empty'
                self.login_stage = 'Click Login once'
                self.page.locator('#otLoginSubmit').click()
                self.login_stage = 'Verify authenticated dashboard'
                expect(self.page).to_have_url(re.compile(
                    r'^' + re.escape(self.ORIGIN) + r'/en/tsp-dashboard(?:[?#].*)?$'), timeout=30000)
                self.page.wait_for_function(
                    '() => window.Liferay?.ThemeDisplay?.isSignedIn?.() === true')
                expect(self.page.locator('#otLoginSubmit')).not_to_be_visible()
                self.authenticated = True
                self.login_stage = 'Authenticated dashboard verified'
            except pytest.skip.Exception:
                raise
            except Exception as exc:
                # Only an exception type and standard Chromium error code leave
                # this boundary. Never expose the raw message/call log or URL.
                code = re.search(r'\bnet::ERR_[A-Z_]+\b', str(exc))
                self.login_error = {
                    'type': type(exc).__name__,
                    'browser_code': code.group(0) if code else 'Not available',
                }
                raise AssertionError('TSP MCP login failed at ' + self.login_stage +
                                     '; private details suppressed.') from None

    def verify_authenticated_landing(self) -> None:
        """Existing login postconditions, inspected without navigation."""
        expect(self.page).to_have_url(re.compile(
            r'^' + re.escape(self.ORIGIN) + r'/en/tsp-dashboard(?:[?#].*)?$'))
        self.page.wait_for_function(
            '() => window.Liferay?.ThemeDisplay?.isSignedIn?.() === true')
        expect(self.page.locator('#otLoginSubmit')).not_to_be_visible()

    def apply_link(self) -> Locator:
        """Reuse the Apply sidebar locator from the existing positive page class."""
        return self.page.locator('a[href*="/en/tsp-registration-form"]')

    def verify_apply_available(self) -> None:
        """Existing Apply locator; only verify presence, never click."""
        entry = self.apply_link()
        expect(entry).to_have_count(1)
        expect(entry).to_be_visible()

    def verify_dashboard_freshness(self) -> None:
        """User-approved UI eligibility rule, not an authoritative backend audit."""
        self.verify_authenticated_landing()
        self.dashboard_freshness_verified = False
        for wording in ('Not Applied', 'No TSP application yet'):
            indicator = self.page.get_by_text(wording, exact=True)
            expect(indicator).to_have_count(1)
            expect(indicator).to_be_visible()
        self.dashboard_freshness_verified = True

    def open_apply_once(self, *, initialization_authorized=False) -> None:
        if not self.dashboard_freshness_verified or not initialization_authorized:
            raise AssertionError('Apply requires dashboard eligibility and separate navigation authorization.')
        if self.apply_click_attempted:
            raise AssertionError('Apply was already attempted; no repeat permitted.')
        self.verify_dashboard_freshness()
        self.verify_apply_available()
        self.apply_click_attempted = True
        self.page.locator('a[href*="/en/tsp-registration-form"]').click()
        self.apply_clicked = True

    def verify_application_opened(self) -> None:
        expect(self.page.locator('#tspApplyBlocked')).not_to_be_visible()
        expect(self.page.locator('#screenForm')).to_be_visible()
        self.at('Application Type')

    # Common read-only section verification covers all eight sections. Blocked
    # sections deliberately have no fill/navigation placeholder methods.
    def at(self, section: str) -> None:
        """Same URL/heading checks as TspApplicationPage.at; never navigate."""
        expect(self.page).to_have_url(re.compile(
            r'^' + re.escape(self.ORIGIN) + r'/en/tsp-registration-form(?:[?#].*)?$'))
        expect(self.page.locator('#stepTitle')).to_have_text(section)

    # Section 6 — Documents: inspect controls without invoking their handlers.
    def document_row(self, number: int) -> Locator:
        return self.content.locator('.doc-item').filter(
            has=self.page.locator(f'button[onclick="viewDoc({number})"]'))

    def document_actions(self, number: int) -> Locator:
        return self.document_row(number).get_by_role('button', include_hidden=True)

    def document_action(self, number: int, name: str, *, include_hidden=False) -> Locator:
        return self.document_row(number).get_by_role(
            'button', name=name, exact=True, include_hidden=include_hidden)

    # Section 8 — Preview & Submit: locate exact workbook-provided public text.
    def preview_banner(self, wording: str) -> Locator:
        return self.content.get_by_text(wording, exact=True)
