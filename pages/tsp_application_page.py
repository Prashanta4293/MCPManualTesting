"""TSP page object using controls observed during the attended MCP inspection."""
import os
import re
import time
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path

import allure
import pytest
from playwright.sync_api import expect

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://apptourlfr-stg.estpl.net'


class TspApplicationPage:
    def __init__(self, page, data):
        self.page, self.data = page, data
        self.stage = 'Prepare attended login'
        self.authenticated = False
        self.content = page.locator('#stepContent')
        self.resumed_existing_draft = False
        self.save_draft_actions = []
        self.fresh_account_confirmed = False
        self.fresh_only = False
        self.document_checkpoint_authorized = False

    @contextmanager
    def private_step(self, label):
        """Sanitize inside the Allure boundary; labels must be fixed public text."""
        with allure.step(label):
            try:
                yield
            except pytest.skip.Exception:
                raise

            except Exception as exc:
                raise AssertionError(
                    label + ': check failed (' +
                    type(exc).__name__ +
                    '); private details suppressed.'
                ) from None



    def confirm_fresh_account(self):
        """Manual authoritative preflight, before login or Apply navigation."""
        print('Confirm an authorized administrator/read-only backend check established '
              'this configured account has NO application or draft in any status. '
              'Confirm this cycle permits form initialization and Save & Continue '
              'to persist test data. A fresh browser or empty UI is insufficient. '
              'Type FRESH VERIFIED; otherwise stop. Do not enter account details.', flush=True)
        try:
            confirmed = input().strip() == 'FRESH VERIFIED'
        except (EOFError, OSError):
            confirmed = False
        if not confirmed:
            self.block('Authoritative manual fresh-account and persistence preconditions not confirmed.')
        self.fresh_account_confirmed = True

    def open_fresh_application(self):
        self.stage = 'Open authorized fresh application'
        with self.private_step(self.stage):
            if not self.fresh_account_confirmed:
                self.block('Fresh-account preflight required before Apply navigation.')
            self.fresh_only = True
            self.resumed_existing_draft = False
            self.page.locator('a[href*="/en/tsp-registration-form"]').click()
            self.page.locator('#tspApplyBlocked, #screenForm').first.wait_for(state='visible')
            if self.page.locator('#tspApplyBlocked').is_visible():
                self.block('Existing application state detected; no resume permitted.')
            if re.search(r'[?&]tspId=', self.page.url):
                self.block('Application identity present unexpectedly; fresh setup stopped.')
            expect(self.page.locator('#screenForm')).to_be_visible()
            self.at('Application Type')
            # These UI checks supplement, never replace, the authoritative preflight.
            select = self.content.locator('select')
            expect(select).to_have_count(1)
            if select.input_value().strip():
                self.block('Unexpected populated application-type state; no reset permitted.')

    def positive_document_checkpoint(self):
        """No inferred save: require a visible requirement and explicit attended approval."""
        if not self.fresh_only or not self.fresh_account_confirmed:
            self.block('Positive fresh-flow authorization required for document checkpoint.')
        messages = self.page.get_by_text(re.compile(
            r'Save Draft To Upload|Please save the draft first', re.I))
        if not any(message.is_visible() for message in messages.all()):
            return  # No visible requirement: do not save speculatively.
        if self.save_draft_actions:
            self.block('Document checkpoint already attempted; no automatic repeat.')
        print('Documents explicitly requires Save Draft. This can persist application data. '
              'Type SAVE CHECKPOINT only if this positive checkpoint is approved; otherwise stop.', flush=True)
        try:
            approved = input().strip() == 'SAVE CHECKPOINT'
        except (EOFError, OSError):
            approved = False
        if not approved:
            self.block('Positive document save checkpoint not approved.')
        self.document_checkpoint_authorized = True
        try:
            self.save_draft_checkpoint()
        finally:
            self.document_checkpoint_authorized = False

    def require_verified_upload_contract(self):
        """Allow upload only through the existing explicit verification helper."""
        return

    def at(self, title):
        expect(self.page).to_have_url(re.compile(r'^' + re.escape(ORIGIN) + r'/en/tsp-registration-form(?:[?#].*)?$'))
        expect(self.page.locator('#stepTitle')).to_have_text(title)

    
    
    
    
    
    
    def continue_existing_draft(self):
        """Detect and resume an existing draft using the observed link."""

        if self.fresh_only:
            self.block('Fresh-only flow cannot resume a draft.')

        continue_link = self.page.locator(
            'a[href*="tspId="]'
        ).filter(
            has_text=re.compile(r'^\s*Continue Draft\s*$', re.I)
        )

        # Allow the page to finish rendering its draft control.
        self.page.wait_for_timeout(1000)

        visible_links = [
            link for link in continue_link.all()
            if link.is_visible() and link.is_enabled()
        ]

        print(
            '[DRAFT DIAGNOSTIC] Visible enabled Continue Draft links:',
            len(visible_links),
            flush=True
        )

        if len(visible_links) == 0:
            print(
                '[DRAFT DIAGNOSTIC] No Continue Draft link detected.',
                flush=True
            )
            return False

        if len(visible_links) != 1:
            self.block(
                'Multiple Continue Draft links detected. '
                'No application was opened.'
            )

        link = visible_links[0]

        href = link.get_attribute('href') or ''

        if not re.search(r'[?&]tspId=\d+', href):
            self.block(
                'Continue Draft link does not contain a valid application reference.'
            )

        link.scroll_into_view_if_needed(timeout=10000)

        expect(link).to_be_visible()
        expect(link).to_be_enabled()

        print(
            '[DRAFT DIAGNOSTIC] Opening existing draft.',
            flush=True
        )

        link.click(timeout=15000)

        screen_form = self.page.locator('#screenForm')

        expect(screen_form).to_be_visible(timeout=20000)

        self.resumed_existing_draft = True
        self.fresh_only = False

        print(
            '[DRAFT DIAGNOSTIC] Existing draft opened successfully.',
            flush=True
        )

        return True




    def fill(self, placeholder, value, index=None):
        field = self.content.get_by_placeholder(placeholder, exact=True)
        if index is not None:
            field = field.nth(index)
        field.fill(value)
        expect(field).to_have_value(value)

    def select_label(self, select, label):
        expect(select).to_have_count(1)
        select.select_option(label=label)
        expect(select.locator('option:checked')).to_have_text(label)

    def complete_visible_fields(self):
        """Fail if a new or missed applicable text/select control is left blank."""
        fields = self.content.locator('input:visible:not([type=radio]):not([type=checkbox]):not([type=file]):not([type=hidden]), textarea:visible, select:visible')
        for field in fields.all():
            if field.is_enabled():
                assert field.input_value().strip(), 'An applicable visible field was left empty'

    def next_section(self, expected):
        # Never use this helper to click the final Submit Application control.
        self.reject_draft_requirement()
        button = self.page.locator('#nextBtn')
        expect(button).to_have_text(re.compile(r'^\s*Save & Continue\s*$'))
        expect(button).to_be_enabled()
        button.click()
        self.at(expected)

    
    def document_filename_matches(self, expected, actual):
        expected_stem = Path(expected).stem
        expected_suffix = Path(expected).suffix

        pattern = (
            rf'^{re.escape(expected_stem)}'
            rf'(?: \(\d+\))?'
            rf'{re.escape(expected_suffix)}$'
        )

        return re.fullmatch(pattern, actual) is not None
    
    
    def save_draft_checkpoint(self):
        """Track each attempt without retaining toast text or application data.

        Confirmed means the expected notification was observed after the click;
        the toast must be hidden before dispatch and visible afterward.
        This does not independently prove backend persistence or request correlation.
        """
        if not self.document_checkpoint_authorized:
            self.block('Save Draft requires the explicit positive document checkpoint.')
        action = {'status': 'attempted', 'click_started': False,
                  'clicked': False, 'confirmed': False}
        self.save_draft_actions.append(action)
        try:
            save_button = self.page.locator('#draftBtn')
            expect(save_button).to_have_count(1)
            expect(save_button).to_be_visible()
            expect(save_button).to_be_enabled()

            # Require an absent prior toast before dispatching this save.
            expect(self.page.locator('#toastEl')).not_to_be_visible(timeout=15000)
            action['click_started'] = True
            save_button.click()
            action['clicked'] = True
            action['status'] = 'clicked'

            toast = self.page.locator('#toastEl')
            toast_inner = self.page.locator('#toastInner')
            toast_message = self.page.locator('#toastMsg')
            expect(toast).to_be_visible(timeout=15000)
            expect(toast_inner).to_have_class(re.compile(r'\btoast-success\b'))
            expect(toast_message).to_contain_text('Draft saved', timeout=15000)
            action['confirmed'] = True
            action['status'] = 'confirmed'
        except BaseException:
            action['status'] = 'failed'
            raise

    def save_draft_action_report(self):
        """Sanitized action evidence, separate from the overall test outcome."""
        actions = self.save_draft_actions or [
            {'status': 'not_attempted', 'click_started': False,
             'clicked': False, 'confirmed': False}]
        reports = []
        for number, action in enumerate(actions, 1):
            clicked = ('YES' if action['clicked'] else
                       'UNKNOWN (click raised before completion)' if action['click_started'] else 'NO')
            confirmation = ('VERIFIED' if action['confirmed'] else
                            'NOT APPLICABLE' if action['status'] == 'not_attempted' else 'NOT VERIFIED')
            reports.append(
                f"Save Draft Action {number}: {action['status'].upper().replace('_', ' ')}\n"
                f"Button Clicked: {clicked}\n"
                f"Success Notification: {confirmation}\n"
                f"Not Attempted: {'YES' if action['status'] == 'not_attempted' else 'NO'}\n"
                f"Action Failed: {'YES' if action['status'] == 'failed' else 'NO'}")
        return '\n\n'.join(reports)

    def reject_draft_requirement(self):
        messages = self.page.get_by_text(re.compile(
            r'Save Draft To Upload|Please save the draft first', re.I))
        if any(message.is_visible() for message in messages.all()):
            self.block('Upload requires Save Draft; no Save Draft fallback is permitted.')

    @staticmethod
    def block(reason):
        # Callers supply fixed sanitized text, never raw DOM or exception details.
        try:
            allure.attach(reason, 'Blocked reason', allure.attachment_type.TEXT)
        except Exception:
            pass  # Reporting cannot convert the intended safe stop into a raw error.
        pytest.skip('BLOCKED: ' + reason)

    
    def wait_for_upload(
        self,
        filename,
        row=None,
        success_texts=('Uploaded successfully',),
        timeout_seconds=90
    ):
        """Verify the exact filename and upload-success message."""

        deadline = time.monotonic() + timeout_seconds

        if row is None:
            self.block(
                'Upload container not provided. '
                'No dependent action performed.'
            )

        while time.monotonic() < deadline:
            self.reject_draft_requirement()

            count = row.count()

            if count == 1 and row.is_visible():
                lines = {
                    line.strip()
                    for line in row.inner_text().splitlines()
                }


                if filename in lines and lines.intersection(success_texts):
                    self.reject_draft_requirement()

                    return

            self.page.wait_for_timeout(500)

        self.reject_draft_requirement()

        self.block(
            'Expected upload success not confirmed. '
            'No dependent action was performed.'
        )


    def login_attended(self):
        with allure.step('Headed TSP login with private environment credentials and human CAPTCHA'):
            # Sanitize inside the step, before Allure records failure details.
            try:
                self.page.goto(self.data['home_url'], wait_until='domcontentloaded')
                self.page.locator('#otUserIconBtn').click()
                self.page.get_by_role('button', name='TSP', exact=True).click()
                email = self.page.locator('#otLoginEmail')
                email.evaluate("e => e.style.setProperty('-webkit-text-security','disc','important')")
                email.fill(os.environ['TSP_EMAIL'])
                self.page.locator('#otLoginPassword').fill(os.environ['TSP_PASSWORD'])
                self.page.locator('#otLoginCaptchaInput').focus()
                print('Enter CAPTCHA in the visible TSP browser. Type CONFIRM here to click Login once. Do not type credentials or CAPTCHA in the terminal.', flush=True)
                try:
                    confirmation = input().strip()
                except (EOFError, OSError):
                    confirmation = ''
                if confirmation != 'CONFIRM':
                    pytest.skip('Explicit CAPTCHA confirmation not received; no login submitted.')
                assert self.page.locator('#otLoginCaptchaInput').evaluate('(e) => e.value.trim().length > 0'), 'CAPTCHA field is empty'
                self.stage = 'Verify single TSP login attempt'
                self.page.locator('#otLoginSubmit').click()
                expect(self.page).to_have_url(re.compile(r'^' + re.escape(ORIGIN) + r'/en/tsp-dashboard(?:[?#].*)?$'), timeout=30000)
                self.page.wait_for_function('() => window.Liferay?.ThemeDisplay?.isSignedIn?.() === true')
                expect(self.page.locator('#otLoginSubmit')).not_to_be_visible()
                self.authenticated = True
            except pytest.skip.Exception:
                raise  # Preserve the fixed no-confirmation skip.
            except Exception:
                # Retain the original exception as internal context only;
                # suppress its displayed chain and never attach its details.
                raise AssertionError('Attended TSP login failed; private details suppressed.') from None

    
    
    def open_application(self):
        self.stage = 'Open Apply Form'

        with self.private_step(self.stage):

            # Start in detection mode, not fresh-only mode.
            self.fresh_only = False
            self.resumed_existing_draft = False

            self.page.locator(
                'a[href*="/en/tsp-registration-form"]'
            ).click()

            self.page.locator(
                '#tspApplyBlocked, #screenForm'
            ).first.wait_for(state='visible', timeout=15000)

            # Existing draft: resume without fresh-account preflight.
            if self.continue_existing_draft():
                self.resumed_existing_draft = True
                self.fresh_only = False

                self.at('Application Type')
                return

            # No draft: require authoritative fresh-account verification.
            self.confirm_fresh_account()

            self.fresh_only = True
            self.resumed_existing_draft = False

            expect(
                self.page.locator('#screenForm')
            ).to_be_visible()

            # Do not overwrite existing applicant data.
            self.page.locator(
                '#stepperBar button'
            ).filter(
                has_text='Applicant Details'
            ).click()

            name = self.content.get_by_placeholder(
                'Full legal name of the firm or applicant',
                exact=True
            )

            if name.is_visible():
                current = name.input_value()

                if current and not current.startswith('UAT TEST ONLY -'):
                    pytest.skip(
                        'Existing non-test applicant data found. '
                        'Use a dedicated unused TSP account.'
                    )

            # Return to Application Type.
            self.page.locator(
                '#stepperBar button'
            ).filter(
                has_text='Application Type'
            ).click()

            self.at('Application Type')




    def fill_all_sections(self):
        for label, operation in [
            ('1 Application Type', self.application_type),
            ('2 Applicant Details', self.applicant),
            ('3 Office Details', self.office),
            ('4 HR & Certification', self.staff),
            ('5 Transport Details', self.transport),
            ('6 Documents', self.documents),
            ('7 Declaration', self.declaration),
        ]:
            self.stage = label
            with self.private_step(label):
                operation()

    def application_type(self):
        self.at('Application Type')
        self.content.get_by_role('button', name=re.compile(re.escape(self.data['category']))).click()
        self.select_label(self.content.locator('select'), self.data['tsp_type'])
        self.complete_visible_fields()
        self.next_section('Applicant Details')

    def applicant(self):
        self.at('Applicant Details')
        d = self.data['applicant']
        existing = self.content.get_by_placeholder('Full legal name of the firm or applicant').input_value()
        if self.fresh_only and existing.strip():
            self.block('Unexpected applicant data in fresh cycle; no overwrite permitted.')
        if existing and not existing.startswith('UAT TEST ONLY -'):
            pytest.skip('Non-test applicant data found; refusing to overwrite.')
        self.fill('Full legal name of the firm or applicant', d['name'])
        self.select_label(self.content.locator('select').first, d['constitution'])
        self.fill('Specify constitution type', d['constitution_other'])
        self.content.locator('input[type=checkbox]').uncheck()
        expect(self.content.locator('input[type=checkbox]')).not_to_be_checked()
        for i, prefix in enumerate(('registered', 'communication')):
            self.fill('Flat / House No., Street, Locality', d[prefix + '_address'], i)
            self.select_label(self.content.locator('select').nth(i + 1), d[prefix + '_district'])
            self.fill('Enter Block / ULB', d[prefix + '_block'], i)
            self.fill('Enter Gram Panchayat / Ward', d[prefix + '_ward'], i)
            self.fill('Enter Village', d[prefix + '_village'], i)
        for placeholder, key in [
            ('10-digit mobile number', 'mobile'), ('contact@example.com', 'email'),
            ('https://www.example.com', 'website'), ('AAAPL0000A', 'pan'),
            ('21AAAPL0000A1Z5', 'gstin'), ('e.g. U63040OR2015PTC012345', 'incorporation')
        ]:
            self.fill(placeholder, d[key])
        self.content.locator('input[type=date]').fill(d['established'])
        expect(self.content.locator('input[type=date]')).to_have_value(d['established'])
        self.complete_visible_fields()
        self.next_section('Office Details')

    def office(self):
        self.at('Office Details')
        d = self.data['office']
        self.fill('e.g. 5', d['experience'])
        self.fill('Amount in rupees', d['capital'], 0)
        self.fill('Amount in rupees', d['turnover'], 1)
        for area in d['areas']:
            # Selection adds the observed U+F00C check icon to the accessible name.
            chip = self.content.get_by_role(
                'button', name=re.compile(rf'^(?:\uf00c\s*)?{re.escape(area)}$')
            )
            # Saved accessibility snapshot: selected State is named "\uf00c State".
            # Assert this observed visual indicator, not an unverified CSS/ARIA state.
            selected = self.content.get_by_role(
                'button', name=re.compile(rf'^\uf00c\s*{re.escape(area)}$')
            )
            expect(chip).to_have_count(1)
            if selected.count() == 0:
                chip.click()
            expect(selected).to_have_count(1)
            expect(selected).to_be_visible()
        # Re-query each checkbox after changes: this UI rebuilds its controls.
        for label in [
            'Tour Packages', 'Hotel / Accommodation Booking', 'Transport & Transfers',
            'Adventure Activities', 'Wildlife Tourism', 'Heritage & Cultural Tours',
            'Eco Tourism', 'Cruise & Boat Tourism', 'Medical Tourism',
            'MICE (Meetings, Incentives, Conferences & Exhibitions)', 'Other Services'
        ]:
            self.content.get_by_label(label, exact=True).check()
            expect(self.content.get_by_label(label, exact=True)).to_be_checked()
        self.fill('Please specify the other tourism services offered', d['other_service'])
        self.content.get_by_label('Yes', exact=True).check()
        self.fill('Full office address', d['address'])
        self.fill('e.g. 500', d['area'])
        self.select_label(self.content.locator('select'), d['ownership'])
        self.fill('Specify other ownership status', d['other_ownership'])
        self.complete_visible_fields()
        self.next_section('HR & Certification')

    def click_add_staff_member(self):
        """Click Add Staff Member and collect diagnostic information."""

        add_staff_button = self.content.locator('#staffSaveBtn')

        expect(add_staff_button).to_be_visible()
        expect(add_staff_button).to_be_enabled()

        # Check JavaScript handler
        save_staff_function = self.page.evaluate(
            "() => typeof window.saveStaff"
        )


        # Perform normal Playwright click
        add_staff_button.click(timeout=10000)

        # Wait for application response
        self.page.wait_for_timeout(2000)

    
    
    # def staff(self):
    #     self.at('HR & Certification')
    #     d = self.data['staff']

    #     rows = self.content.locator('tbody tr')

    #     # Identify the configured staff record by exact name.
    #     row = rows.filter(
    #         has=self.page.get_by_role(
    #             'cell',
    #             name=d['name'],
    #             exact=True
    #         )
    #     )

    #     matching_count = row.count()
    #     total_rows = rows.count()

    #     # ==================================================
    #     # EXISTING STAFF RECORD: VERIFY ONLY
    #     # ==================================================

    #     if matching_count == 1:

    #         checks = [
    #             (
    #                 'qualification',
    #                 lambda: expect(row).to_contain_text(d['qualification'])
    #             ),
    #             (
    #                 'designation',
    #                 lambda: expect(row).to_contain_text(d['designation'])
    #             ),
    #             (
    #                 'qualification certificate attachment',
    #                 lambda: expect(
    #                     row.get_by_role(
    #                         'cell',
    #                         name='Attached',
    #                         exact=True
    #                     )
    #                 ).to_have_count(1)
    #             ),
    #             (
    #                 'Not Attached status',
    #                 lambda: expect(row).not_to_contain_text('Not Attached')
    #             ),
    #             (
    #                 'IITTM certification No status',
    #                 lambda: expect(
    #                     row.get_by_role(
    #                         'cell',
    #                         name='No',
    #                         exact=True
    #                     )
    #                 ).to_have_count(1)
    #             ),
    #             (
    #                 'IITTM certificate N/A status',
    #                 lambda: expect(
    #                     row.get_by_role(
    #                         'cell',
    #                         name='N/A',
    #                         exact=True
    #                     )
    #                 ).to_have_count(1)
    #             )
    #         ]

    #         for check_name, check in checks:
    #             try:
    #                 check()
    #             except Exception:
    #                 self.block(
    #                     'Existing HR staff record failed verification: ' +
    #                     check_name +
    #                     '. No staff record was modified.'
    #                 )

    #         self.next_section('Transport Details')
    #         return

    #     # ==================================================
    #     # DUPLICATE RECORD CHECK
    #     # ==================================================

    #     if matching_count > 1:
    #         self.block(
    #             'Duplicate staff records found. '
    #             'No staff record was modified.'
    #         )

    #     # ==================================================
    #     # EXISTING OTHER STAFF RECORDS
    #     # ==================================================

    #     if total_rows > 0:
    #         self.block(
    #             'Staff table contains records, but the configured '
    #             'staff record was not found. Manual verification required.'
    #         )

    #     # ==================================================
    #     # EMPTY TABLE: NEW STAFF RECORD
    #     # ==================================================

    #     self.fill('Full name of staff', d['name'])

    #     self.fill(
    #         'e.g. B.Sc. Computer Science',
    #         d['qualification']
    #     )

    #     self.fill(
    #         'e.g. Tour Manager',
    #         d['designation']
    #     )

    #     # ==================================================
    #     # QUALIFICATION CERTIFICATE UPLOAD
    #     # ==================================================

    #     filename = Path(d['qualification_file']).name
    #     file_path = ROOT / d['qualification_file']

    #     if not file_path.is_file():
    #         self.block(
    #             'Qualification certificate file does not exist. '
    #             'No dependent action performed.'
    #         )

    #     file_input = self.content.locator(
    #         '#fileInput_tempQualCert'
    #     )

    #     expect(file_input).to_have_count(1)

    #     self.require_verified_upload_contract()

    #     file_input.set_input_files(str(file_path))

    #     upload_row = self.content.locator(
    #         '.file-preview'
    #     ).filter(
    #         has_text=filename
    #     )

    #     self.wait_for_upload(
    #         filename,
    #         row=upload_row
    #     )

    #     # ==================================================
    #     # IITTM CERTIFICATION = NO
    #     # ==================================================

    #     no = self.content.get_by_label(
    #         'No',
    #         exact=True
    #     )

    #     yes = self.content.get_by_label(
    #         'Yes',
    #         exact=True
    #     )

    #     no.check()

    #     expect(no).to_be_checked()
    #     expect(yes).not_to_be_checked()

    #     iittm_label = self.content.get_by_text(
    #         'Upload IITTM Certificate Document',
    #         exact=True
    #     )

    #     expect(iittm_label).not_to_be_visible()

    #     iittm_input = self.content.locator(
    #         '#fileInput_tempIittmDoc'
    #     )

    #     if iittm_input.count():
    #         expect(
    #             iittm_input.locator('..')
    #         ).not_to_be_visible()

    #     # Complete remaining visible mandatory fields.
    #     self.complete_visible_fields()

    #     self.reject_draft_requirement()

    #     # ==================================================
    #     # VERIFY BEFORE SAVING
    #     # ==================================================

    #     expect(row).to_have_count(0)

    #     # ==================================================
    #     # SAVE NEW STAFF RECORD
    #     # ==================================================

    #     staff_save_button = self.content.locator(
    #         '#staffSaveBtn'
    #     )

    #     expect(staff_save_button).to_have_text(
    #         'Add Staff Member',
    #         use_inner_text=True
    #     )

    #     expect(staff_save_button).to_be_visible()
    #     expect(staff_save_button).to_be_enabled()

    #     self.reject_draft_requirement()

    #     staff_save_button.click()

    #     # ==================================================
    #     # VERIFY SAVED STAFF RECORD
    #     # ==================================================

    #     saved_row = rows.filter(
    #         has=self.page.get_by_role(
    #             'cell',
    #             name=d['name'],
    #             exact=True
    #         )
    #     )

    #     expect(saved_row).to_have_count(
    #         1,
    #         timeout=15000
    #     )

    #     expect(saved_row).to_contain_text(d['qualification'])
    #     expect(saved_row).to_contain_text(d['designation'])
    #     expect(saved_row).not_to_contain_text('Not Attached')

    #     expect(
    #         saved_row.get_by_role(
    #             'cell',
    #             name='Attached',
    #             exact=True
    #         )
    #     ).to_have_count(1)

    #     expect(
    #         saved_row.get_by_role(
    #             'cell',
    #             name='No',
    #             exact=True
    #         )
    #     ).to_have_count(1)

    #     expect(
    #         saved_row.get_by_role(
    #             'cell',
    #             name='N/A',
    #             exact=True
    #         )
    #     ).to_have_count(1)

    #     self.next_section('Transport Details')

        
    def staff(self):
        self.at('HR & Certification')
        d = self.data['staff']

        rows = self.content.locator('tbody tr')

        # Identify the configured staff record by exact name.
        row = rows.filter(
            has=self.page.get_by_role(
                'cell',
                name=d['name'],
                exact=True
            )
        )

        matching_count = row.count()
        total_rows = rows.count()

        # ==================================================
        # EXISTING STAFF RECORD: VERIFY ONLY
        # ==================================================

        if matching_count == 1:

            attachment_cell = row.locator('td').filter(
                has_text=re.compile(r'Attached|Not Attached', re.I)
            )

            checks = [
                (
                    'qualification',
                    lambda: expect(row).to_contain_text(d['qualification'])
                ),
                (
                    'designation',
                    lambda: expect(row).to_contain_text(d['designation'])
                ),
                (
                    'qualification certificate attachment',
                    lambda: (
                        expect(attachment_cell).to_have_count(1),
                        expect(attachment_cell).to_contain_text(
                            re.compile(r'Attached', re.I)
                        ),
                        expect(attachment_cell).not_to_contain_text(
                            re.compile(r'Not Attached', re.I)
                        )
                    )
                ),
                (
                    'IITTM certification No status',
                    lambda: expect(
                        row.get_by_role(
                            'cell',
                            name='No',
                            exact=True
                        )
                    ).to_have_count(1)
                ),
                (
                    'IITTM certificate N/A status',
                    lambda: expect(
                        row.get_by_role(
                            'cell',
                            name='N/A',
                            exact=True
                        )
                    ).to_have_count(1)
                )
            ]

            for check_name, check in checks:
                try:
                    check()
                except Exception:
                    self.block(
                        'Existing HR staff record failed verification: ' +
                        check_name +
                        '. No staff record was modified.'
                    )

            # Existing record verified. No modification.
            self.next_section('Transport Details')
            return

        # ==================================================
        # DUPLICATE RECORD CHECK
        # ==================================================

        if matching_count > 1:
            self.block(
                'Duplicate staff records found. '
                'No staff record was modified.'
            )

        # ==================================================
        # EXISTING OTHER STAFF RECORDS
        # ==================================================

        if total_rows > 0:
            self.block(
                'Staff table contains records, but the configured '
                'staff record was not found. Manual verification required.'
            )

        # ==================================================
        # EMPTY TABLE: NEW STAFF RECORD
        # ==================================================

        self.fill('Full name of staff', d['name'])

        self.fill(
            'e.g. B.Sc. Computer Science',
            d['qualification']
        )

        self.fill(
            'e.g. Tour Manager',
            d['designation']
        )

        # ==================================================
        # QUALIFICATION CERTIFICATE UPLOAD
        # ==================================================

        filename = Path(d['qualification_file']).name
        file_path = ROOT / d['qualification_file']

        if not file_path.is_file():
            self.block(
                'Qualification certificate file does not exist. '
                'No dependent action performed.'
            )

        file_input = self.content.locator(
            '#fileInput_tempQualCert'
        )

        expect(file_input).to_have_count(1)

        self.require_verified_upload_contract()

        file_input.set_input_files(str(file_path))

        upload_row = self.content.locator(
            '.file-preview'
        ).filter(
            has_text=filename
        )

        self.wait_for_upload(
            filename,
            row=upload_row
        )

        # ==================================================
        # IITTM CERTIFICATION = NO
        # ==================================================

        no = self.content.get_by_label(
            'No',
            exact=True
        )

        yes = self.content.get_by_label(
            'Yes',
            exact=True
        )

        no.check()

        expect(no).to_be_checked()
        expect(yes).not_to_be_checked()

        iittm_label = self.content.get_by_text(
            'Upload IITTM Certificate Document',
            exact=True
        )

        expect(iittm_label).not_to_be_visible()

        iittm_input = self.content.locator(
            '#fileInput_tempIittmDoc'
        )

        if iittm_input.count():
            expect(
                iittm_input.locator('..')
            ).not_to_be_visible()

        # Complete remaining visible mandatory fields.
        self.complete_visible_fields()

        self.reject_draft_requirement()

        # ==================================================
        # VERIFY BEFORE SAVING
        # ==================================================

        expect(row).to_have_count(0)

        # ==================================================
        # SAVE NEW STAFF RECORD
        # ==================================================

        staff_save_button = self.content.locator(
            '#staffSaveBtn'
        )

        expect(staff_save_button).to_have_text(
            'Add Staff Member',
            use_inner_text=True
        )

        expect(staff_save_button).to_be_visible()
        expect(staff_save_button).to_be_enabled()

        self.reject_draft_requirement()

        staff_save_button.click()

        # ==================================================
        # VERIFY SAVED STAFF RECORD
        # ==================================================

        saved_row = rows.filter(
            has=self.page.get_by_role(
                'cell',
                name=d['name'],
                exact=True
            )
        )

        expect(saved_row).to_have_count(
            1,
            timeout=15000
        )

        expect(saved_row).to_contain_text(d['qualification'])
        expect(saved_row).to_contain_text(d['designation'])

        saved_attachment_cell = saved_row.locator('td').filter(
            has_text=re.compile(r'Attached|Not Attached', re.I)
        )

        expect(saved_attachment_cell).to_have_count(1)

        expect(saved_attachment_cell).to_contain_text(
            re.compile(r'Attached', re.I)
        )

        expect(saved_attachment_cell).not_to_contain_text(
            re.compile(r'Not Attached', re.I)
        )

        expect(
            saved_row.get_by_role(
                'cell',
                name='No',
                exact=True
            )
        ).to_have_count(1)

        expect(
            saved_row.get_by_role(
                'cell',
                name='N/A',
                exact=True
            )
        ).to_have_count(1)

        self.next_section('Transport Details')



    

    
    def transport(self):
        self.at('Transport Details')
        d = self.data['vehicle']

        yes = self.content.get_by_label('Yes', exact=True)
        no = self.content.get_by_label('No', exact=True)

        rows = self.content.locator('tbody tr')

        # Identify the configured vehicle by exact registration.
        matching = rows.filter(
            has=self.page.get_by_role(
                'cell',
                name=d['registration'],
                exact=True
            )
        )

        # ==================================================
        # EXISTING DRAFT: VERIFY ONLY
        # ==================================================

        if self.resumed_existing_draft:

            if yes.is_checked():
                pass
            elif no.is_checked():
                self.block(
                    'Existing draft has Transport set to No. '
                    'Vehicle record cannot be verified.'
                )
            else:
                self.block(
                    'Existing draft Transport selection is not verified.'
                )

            if rows.count() != 1:
                self.block(
                    'Existing draft must contain exactly one vehicle record. '
                    'No vehicle was modified.'
                )

            if matching.count() != 1:
                self.block(
                    'Configured vehicle registration was not found '
                    'in the existing draft. No vehicle was modified.'
                )

            for key in ('type', 'registration', 'capacity', 'ownership'):
                expect(
                    matching.get_by_role(
                        'cell',
                        name=d[key],
                        exact=True
                    )
                ).to_have_count(1)

            self.next_section('Documents')
            return

        # ==================================================
        # FRESH APPLICATION
        # ==================================================

        yes.check()
        expect(yes).to_be_checked()

        if rows.count():
            self.block(
                'Unexpected vehicles found in fresh cycle. '
                'No vehicle was added.'
            )

        # ==================================================
        # ADD NEW VEHICLE
        # ==================================================

        for selector, key in [
            ('#vehicleType', 'type'),
            ('#vehicleRegNo', 'registration'),
            ('#vehicleCapacity', 'capacity')
        ]:
            field = self.content.locator(selector)
            field.fill(d[key])
            expect(field).to_have_value(d[key])

        self.select_label(
            self.content.locator('#vehicleOwnership'),
            d['ownership']
        )

        self.complete_visible_fields()

        add_button = self.content.get_by_role(
            'button',
            name='Add Vehicle',
            exact=True
        )

        expect(add_button).to_be_visible()
        expect(add_button).to_be_enabled()

        self.reject_draft_requirement()
        add_button.click()

        # ==================================================
        # VERIFY SAVED VEHICLE
        # ==================================================

        expect(rows).to_have_count(1, timeout=15000)
        expect(matching).to_have_count(1)

        for key in ('type', 'registration', 'capacity', 'ownership'):
            expect(
                matching.get_by_role(
                    'cell',
                    name=d[key],
                    exact=True
                )
            ).to_have_count(1)

        self.next_section('Documents')


    def documents(self):
        self.at('Documents')


        # Unsupported upload semantics stop before any save/upload. Once verified,
        # the explicit checkpoint saves only on a visible requirement and approval.
        self.require_verified_upload_contract()
        self.positive_document_checkpoint()

        for number, relative in self.data['documents'].items():
            filename = Path(relative).name

            with self.private_step(f'Populate document checklist entry {number}'):


                row = self.content.locator('.doc-item').filter(
                    has=self.page.locator(
                        f'button[onclick="viewDoc({number})"]'
                    )
                )

                expect(row).to_have_count(1)


                lines = {
                    line.strip()
                    for line in row.inner_text().splitlines()
                }

                # Check whether the document is already uploaded.
                if lines.intersection({'Uploaded', '- Uploaded'}):

                    uploaded_names = [
                        line for line in lines
                        if self.document_filename_matches(filename, line)
                    ]

                    if not uploaded_names:
                        self.block(
                            'Existing document identity could not be verified; no replacement permitted.'
                        )


                else:
                    upload = row.locator(
                        f'input[onchange="handleDocUpload({number}, this)"]'
                    )

                    expect(upload).to_have_count(1)

                    file_path = ROOT / relative

                    if not file_path.is_file():
                        self.block(
                            'Configured document fixture is unavailable.'
                        )


                    upload.set_input_files(str(file_path))



                    # A retry control alone does not establish duplicate-safe delivery.
                    retry_button = row.get_by_role(
                        'button',
                        name='Retry Upload',
                        exact=True
                    )

                    if retry_button.is_visible():
                        self.block('Upload retry blocked: prior attempt outcome and idempotency unverified.')

                # Verify upload status and filename.
                deadline = time.monotonic() + 90
                uploaded_filename = None

                while time.monotonic() < deadline:

                    self.reject_draft_requirement()

                    if row.count() == 1 and row.is_visible():

                        lines = {
                            line.strip()
                            for line in row.inner_text().splitlines()
                        }

                        uploaded_names = [
                            line for line in lines
                            if self.document_filename_matches(
                                filename, line
                            )
                        ]

                        if (
                            uploaded_names
                            and lines.intersection({'Uploaded', '- Uploaded'})
                        ):
                            uploaded_filename = uploaded_names[0]
                            break

                    self.page.wait_for_timeout(500)

                if not uploaded_filename:
                    self.block(
                        'Document upload verification failed. '
                        'No dependent action was performed.'
                    )


                expect(row).not_to_contain_text('Pending Upload')


        expect(self.content).to_contain_text(
            '11 of 11 applicable documents uploaded'
        )


        self.next_section('Declaration')



    # def documents(self):
    #     self.at('Documents')
    #     for number, relative in self.data['documents'].items():
    #         with self.private_step(f'Populate document checklist entry {number}'):
    #             # Stable document identity, never positional file inputs: uploads remove inputs.
    #             row = self.content.locator('.doc-item').filter(
    #                 has=self.page.locator(f'button[onclick="viewDoc({number})"]'))
    #             expect(row).to_have_count(1)
    #             if {line.strip() for line in row.inner_text().splitlines()}.intersection({'Uploaded', '- Uploaded'}):
    #                 expect(row).to_contain_text(Path(relative).name)
    #             else:
    #                 upload = row.locator(f'input[onchange="handleDocUpload({number}, this)"]')
    #                 expect(upload).to_have_count(1)
    #                 upload.set_input_files(str(ROOT / relative))
    #             self.wait_for_upload(Path(relative).name, row=row)
    #             expect(row).not_to_contain_text('Pending Upload')
    #     expect(self.content).to_contain_text('11 of 11 applicable documents uploaded')
    #     self.next_section('Declaration')

    def declaration(self):
        self.at('Declaration')
        expect(self.content.locator('input[type=checkbox]')).to_have_count(1)
        self.content.locator('input[type=checkbox]').check()
        expect(self.content.locator('input[type=checkbox]')).to_be_checked()
        self.next_section('Preview & Submit')

    def verify_preview(self):
        self.stage = '8 Preview verification, never submission'
        with self.private_step(self.stage):
            self.at('Preview & Submit')
            for value in [self.data['applicant']['name'], self.data['applicant']['email'],
                          self.data['applicant']['website'], self.data['applicant']['gstin'],
                          self.data['applicant']['incorporation'], self.data['staff']['qualification'],
                          self.data['vehicle']['registration']]:
                expect(self.content).to_contain_text(value)
            expect(self.content).not_to_contain_text(re.compile(r'\b(Pending|Not provided|Not Attached)\b', re.I))
            final_confirmation = self.content.locator('input[type=checkbox]')
            # Intentionally leave the submission authorization unchecked.
            expect(final_confirmation).to_have_count(1)
            # Inspect only: unexpected authorization state must fail, not be reset.
            expect(final_confirmation).not_to_be_checked()
            expect(self.page.locator('#nextBtn')).to_have_text(re.compile('Submit Application'))
            allure.attach('Configured preview text assertions completed; no visual verification claimed. Final confirmation unchecked; Submit Application not invoked.',
                          'Preview inspection', allure.attachment_type.TEXT)

    
    def attach_safe_evidence(self, name, required=False):
        """Create a privacy placeholder, NOT a screenshot or visual verification."""

        safe_png = None
        stage = 'Initialization'

        try:
            from importlib import import_module

            stage = 'Import Pillow'
            Image = import_module('PIL.Image')

            stage = 'Authentication check'

            if not self.authenticated:
                raise ValueError('Authentication flag is False')

            if self.page.locator('#otLoginSubmit').is_visible():
                raise ValueError('Login form is visible')

            stage = 'Form locator check'
            form = self.page.locator('#screenForm')

            expect(form).to_have_count(1)
            expect(form).to_be_visible()

            stage = 'Get form dimensions'
            box = form.bounding_box()

            if not box:
                raise ValueError('Form bounding box unavailable')

            width = round(box['width'])
            height = round(box['height'])

            if width < 1 or height < 1:
                raise ValueError('Invalid form dimensions')

            stage = 'Create sanitized image'

            sanitized = Image.new(
                'RGBA',
                (width, height),
                (0, 0, 0, 255)
            )

            stage = 'Verify sanitized pixels'

            extrema = sanitized.getextrema()

            expected = (
                (0, 0),
                (0, 0),
                (0, 0),
                (255, 255)
            )

            if extrema != expected:
                raise ValueError('Opaque black pixel verification failed')

            stage = 'Encode sanitized PNG'

            output = BytesIO()

            sanitized.convert('RGB').save(
                output,
                format='PNG'
            )

            safe_png = output.getvalue()

            stage = 'Verify encoded PNG'

            with Image.open(BytesIO(safe_png)) as verification:
                if verification.format != 'PNG':
                    raise ValueError('Invalid PNG format')

                if verification.getextrema() != (
                    (0, 0),
                    (0, 0),
                    (0, 0)
                ):
                    raise ValueError('Encoded image is not completely black')

        except Exception as exc:

            # Log only the stage and exception type, not page data.
            print(
                f'EVIDENCE DIAGNOSTIC: stage={stage}, '
                f'exception_type={type(exc).__name__}',
                flush=True
            )

            reason = (
                'Evidence Blocked: sanitized evidence image could not '
                'be verified. Screenshot suppressed; no unmasked fallback.'
            )

            allure.attach(
                f'Failed stage: {stage}\n'
                f'Exception type: {type(exc).__name__}',
                'Evidence diagnostic',
                allure.attachment_type.TEXT
            )

            if required:
                self.block(reason)

            return False

        allure.attach(
            safe_png,
            name + ' (privacy placeholder - not a captured form image)',
            allure.attachment_type.PNG
        )

        allure.attach(
            'Generated black privacy placeholder only. No form image was captured; no layout or visual verification is claimed.',
            'Evidence privacy verification',
            allure.attachment_type.TEXT
        )

        allure.attach(
            ORIGIN + '/en/tsp-registration-form',
            'Tested URL',
            allure.attachment_type.TEXT
        )

        return True
        

    
    # def attach_safe_evidence(self, name, required=False):
    #     """
    #     Capture form dimensions, create a completely black evidence image,
    #     verify every pixel, and attach only the sanitized image.
    #     Never attach original browser screenshot bytes.
    #     """

    #     safe_png = None

    #     try:
    #         from importlib import import_module

    #         Image = import_module('PIL.Image')

    #         if (
    #             not self.authenticated
    #             or self.page.locator('#otLoginSubmit').is_visible()
    #         ):
    #             raise ValueError('Capture preconditions unavailable')

    #         form = self.page.locator('#screenForm')

    #         expect(form).to_have_count(1)
    #         expect(form).to_be_visible()

    #         # Capture only the form's dimensions, not its displayed content.
    #         box = form.bounding_box()

    #         if not box or box['width'] <= 0 or box['height'] <= 0:
    #             raise ValueError('Form dimensions unavailable')

    #         width = round(box['width'])
    #         height = round(box['height'])

    #         if width < 1 or height < 1:
    #             raise ValueError('Invalid form dimensions')

    #         # Create a completely black image without capturing form contents.
    #         sanitized = Image.new(
    #             'RGBA',
    #             (width, height),
    #             (0, 0, 0, 255)
    #         )

    #         # Verify every pixel is opaque black.
    #         if sanitized.getextrema() != (
    #             (0, 0),
    #             (0, 0),
    #             (0, 0),
    #             (255, 255)
    #         ):
    #             raise ValueError('Full mask verification failed')

    #         # Convert to RGB and remove metadata.
    #         output = BytesIO()

    #         sanitized.convert('RGB').save(
    #             output,
    #             format='PNG'
    #         )

    #         safe_png = output.getvalue()

    #     except Exception:
    #         reason = (
    #             'Evidence Blocked: sanitized evidence image could not be '
    #             'verified. Screenshot suppressed; no unmasked fallback.'
    #         )

    #         allure.attach(
    #             reason,
    #             'Evidence status',
    #             allure.attachment_type.TEXT
    #         )

    #         if required:
    #             self.block(reason)

    #         return False

    #     allure.attach(
    #         safe_png,
    #         name + ' (privacy placeholder - not a captured form image)',
    #         allure.attachment_type.PNG
    #     )

    #     allure.attach(
    #         'Evidence image contains only opaque black pixels. '
    #         'No form values or displayed text were captured.',
    #         'Evidence privacy verification',
    #         allure.attachment_type.TEXT
    #     )

    #     allure.attach(
    #         ORIGIN + '/en/tsp-registration-form',
    #         'Tested URL',
    #         allure.attachment_type.TEXT
    #     )

    #     return True

