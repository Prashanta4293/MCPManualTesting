import re
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

class BasePage:
    def __init__(self, page, audit):
        self.page, self.audit = page, audit

    def poll(self, predicate, timeout=15000):
        deadline = time.monotonic() + timeout / 1000
        while time.monotonic() < deadline:
            if predicate():
                return
            self.page.wait_for_timeout(100)
        raise AssertionError(f'Browser condition not satisfied within {timeout} ms')

    def image_audit(self):
        p = self.page
        height = p.evaluate('() => document.body.scrollHeight')
        for y in range(0, height, 700):
            p.evaluate('(y) => window.scrollTo(0,y)', y)
            p.wait_for_timeout(80)
        eligible = "i => { const r=i.getBoundingClientRect(); return r.width && r.height && r.right>0 && r.left<innerWidth && getComputedStyle(i).visibility !== 'hidden' && (i.currentSrc || i.getAttribute('src')); }"
        try:
            p.wait_for_function(f'() => [...document.images].filter({eligible}).every(i => i.complete)', timeout=10000)
        except PlaywrightTimeoutError:
            pass  # The assertion below records pending images as failures.
        p.wait_for_timeout(800)
        images = p.locator('img').evaluate_all(f"imgs => imgs.filter({eligible}).map(i => ({{src:i.currentSrc || i.src,alt:i.alt,complete:i.complete,width:i.naturalWidth}}))")
        p.evaluate('() => window.scrollTo(0,0)')
        self.audit.record({'images': images})
        self.audit.check(not [i for i in images if not i['complete'] or i['width'] == 0], 'Rendered images must finish loading and decode', images)

    def healthy(self, phase='destination'):
        errors = [e for e in self.audit.console if e['phase'] == phase]
        network = [e for e in self.audit.network if e['phase'] == phase and not (e.get('error') == 'net::ERR_ABORTED' and re.search(r'analytics\.google\.com|google-analytics\.com', e['url']))]
        self.audit.check(not errors, 'Browser console/runtime errors', errors)
        self.audit.check(not network, 'Failed requests or HTTP 4xx/5xx (only cancelled Google analytics excluded)', network)
