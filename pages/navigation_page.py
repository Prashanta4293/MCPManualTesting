import re
from urllib.parse import urlsplit
from playwright.sync_api import expect
from .home_page import HomePage
from .base_page import BasePage
from .data import INVENTORY

def normalize(text):
    return ' '.join(text.replace('’', "'").replace('‘', "'").split()).lower()

def canonical(url):
    p = urlsplit(url)
    return f'{p.scheme}://{p.netloc}{p.path.rstrip("/")}'

class NavigationPage(HomePage):
    def navigate(self, case):
        index = int(case['Test Case ID'][4:])
        if index in (55,71,72,73,74,75):
            return self.open_external(index)
        recorded = next((x for x in INVENTORY if x['index'] == index), None)
        menu = self.reveal(recorded['menu'] if recorded else 'Hamburger')
        link = menu.locator(f'a[href="{case["Test Data"]}"]:visible')
        expect(link).to_have_count(1)
        self.audit.destination()
        link.click()
        self.page.wait_for_load_state('domcontentloaded')
        expect(self.page).to_have_url(case['Test Data'])
        return self.page

    def verify(self, case, target):
        index = int(case['Test Case ID'][4:])
        a = self.audit
        if index in (55,71,72,73,74,75):
            body, title = target.locator('body').inner_text(), target.title()
            a.record({'url':target.url,'title':title,'content':body[:12000],'breadcrumb':'Not applicable to external home/profile'})
            a.check(canonical(target.url) == canonical(case['Tested URL']), 'External destination including approved canonical redirects', target.url)
            a.check(not re.search(r'your connection is not private|ERR_CERT_|access denied|internal server error|page not found', body, re.I), 'No TLS interstitial, blocked page or page error', body)
            a.check(bool(re.search('odisha|tourism', title+' '+body, re.I)), 'Official Odisha identity visible', title)
            a.check(len(body)>100, 'External content is populated', len(body))
        else:
            target.wait_for_timeout(650)
            body = target.locator('body').inner_text()
            headings = target.locator('h1:visible,h2:visible,h3:visible').all_text_contents()
            crumbs = target.locator('[class*="breadcrumb"]:visible').all_text_contents()
            heading = re.search(r'Heading\(s\): (.*?)(?:;|\. Breadcrumb:)',case['Actual Result'],re.S).group(1)
            breadcrumb = re.search(r'Breadcrumb: (.*?)\. Content:',case['Actual Result'],re.S).group(1)
            a.record({'url':target.url,'title':target.title(),'headings':headings,'breadcrumbs':crumbs,'content':body[:16000]})
            a.check(bool(target.title()), 'Nonempty document title')
            a.check(not re.search(r'\b404\s*(?:error|not found)|\b500\s*(?:error|internal)|internal server error', body,re.I), 'No page-level server error', body)
            if index == 29:
                a.check(target.locator('img:visible').count()>0, 'Map viewer renders an image')
            else:
                a.check(normalize(heading) in [normalize(x) for x in headings], f'Expected heading: {heading}', headings)
                a.check(bool(crumbs), 'Breadcrumb present', crumbs)
                for text in re.sub(r'^\s*/\s*','',breadcrumb).split('/'):
                    a.check(normalize(text) in normalize(' '.join(crumbs)), f'Breadcrumb segment: {text}',crumbs)
                a.check(len(body)>250, 'Substantial page content',len(body))
            if index == 1:
                a.check(not (re.search(r'nearly\s*480\s*km',body,re.I) and re.search(r'nearly\s*574\s*km',body,re.I)), 'Coastline figures must not contradict')
            if index == 3:
                a.check('information displayed should reflect' not in body, 'Editorial instruction must not appear in public content')
            if index in (18,20):
                a.check(not re.search('DISTRICTS THAT SHAPE THE COAST',body,re.I), 'Inland region must not use coastal template heading')
            if index == 36:
                a.check('Government Approved Tour Guides' not in body, 'Tour operators must not be labelled tour guides')
            if index == 49:
                a.check(not (re.search('Varanasi',body,re.I) and re.search('Ahmedabad',body,re.I)), 'Single event edition location')
            if index == 50:
                a.check(not re.search('LEGENDARY SWEET',body,re.I), 'Mahaprasad meal must not be labelled a legendary sweet')
        destination = BasePage(target,a)
        destination.image_audit()
        destination.healthy()
