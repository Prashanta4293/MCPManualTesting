"""Read-only browser primitives for the workbook-based TSP MCP suite.

No login, navigation, state preparation or mutation belongs to this page object.
Case IDs, expected wording, document numbers and assertions stay in test support.
Locators come from the existing TSP page object and workbook assertion helpers.
"""
import re

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
