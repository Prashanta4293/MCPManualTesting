import re
from playwright.sync_api import expect
from .home_page import HomePage
from .data import read_json

class HotelsPage(HomePage):
    def navigate(self):
        self.open()
        menu = self.reveal('Plan Your Trip')
        self.audit.destination()
        menu.locator('a[href$="/hotels"]').click()
        expect(self.page).to_have_url(re.compile(r'/hotels$'))

    def verify_matches(self):
        p = self.page
        more = p.get_by_role('button',name=re.compile('load more',re.I))
        expect(more).to_be_visible()
        for _ in range(30):
            if not more.is_visible():
                break
            more.click()
            p.wait_for_timeout(350)
        expect(more).not_to_be_visible()
        cards = read_json('artifacts/hotels-cards.json')
        for match in read_json('tests/data/hotel-matches.json'):
            assert any(c['name'] == match['name'] for c in cards), 'Match must exist in saved browser evidence'
            title = p.get_by_text(match['name'],exact=True)
            expect(title, 'Each confirmed hotel must have exactly one matching card (preserves the original strict locator)').to_have_count(1)
            expect(title).to_be_visible()
            text = title.locator('..').inner_text()
            self.audit.record({'source':match,'liveCard':text})
            self.audit.check(re.sub(r'\D','',match['phone']) in re.sub(r'\D','',text), f"{match['name']} phone from source workbook",text)
        self.audit.record({'expandedListing':p.locator('body').inner_text()})
