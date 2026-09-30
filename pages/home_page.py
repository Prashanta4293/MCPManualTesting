import re
from playwright.sync_api import expect
from .base_page import BasePage
from .data import HOME

class HomePage(BasePage):
    def open(self):
        response = self.page.goto(HOME, wait_until='domcontentloaded')
        assert response and response.status < 400, 'Home document HTTP status must be below 400'
        expect(self.page.locator('.main-nav-fixed')).to_be_visible()
        close = self.page.locator('#closeCookieBtn')
        if close.is_visible():
            close.click()

    def reveal(self, name):
        p = self.page
        if name == 'Hamburger':
            p.locator('#hamburgerBtn').click()
            return p.locator('#hamburgerMenu')
        item = p.locator('.main-nav-fixed .nav-item-wrapper').filter(has=p.locator('.highlight-text').filter(has_text=re.compile(f'^{re.escape(name)}$', re.I)))
        item.locator(':scope > a').hover()
        expect(item.locator('.mega-menu-container')).to_be_visible()
        return item.locator('.mega-menu-container')

    def open_search(self):
        self.audit.destination()
        self.page.locator('#searchTriggerBtn').click()
        expect(self.page.locator('#searchInput')).to_be_visible()

    def open_login(self):
        self.audit.destination()
        self.page.locator('#otUserIconBtn').click()
        expect(self.page.locator('[role="dialog"][aria-labelledby="otlxTitle"]')).to_be_visible()

    def open_external(self, index):
        p = self.page
        area = p.locator('.main-nav-fixed') if index == 71 else self.reveal('Hamburger')
        domains = {55:'dot.odisha.gov.in',71:'bookodisha.com',72:'facebook.com',73:'x.com/',74:'instagram.com',75:'youtube.com'}
        link = area.locator(f'a[href*="{domains[index]}"]:visible').first
        href = link.get_attribute('href')
        self.audit.record({'advertisedURL': href})
        opened = []
        def capture(page):
            opened.append(page)
        p.context.on('page', capture)
        self.audit.destination()
        try:
            link.click()
            modal = p.locator('#ext-modal-overlay:visible')
            self.poll(lambda: bool(opened) or modal.is_visible())
            if not opened:
                from urllib.parse import urlparse
                expect(modal).to_contain_text(urlparse(href).hostname)
                modal.locator('#ext-modal-confirm').click()
            self.poll(lambda: bool(opened), timeout=35000)
            target = opened[0]
            self.audit.record({'externalFlow': 'new tab opened', 'popupURL': target.url})
        finally:
            p.context.remove_listener('page', capture)
        target.wait_for_load_state('domcontentloaded')
        target.wait_for_timeout(2500)
        return target
