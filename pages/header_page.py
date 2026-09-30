import re
from playwright.sync_api import expect
from .home_page import HomePage
from .data import HOME

class HeaderPage(HomePage):
    def verify_case(self, case):
        p, a = self.page, self.audit
        id = case['Test Case ID']
        if id == 'HOME-001':
            expect(p).to_have_url(HOME)
            expect(p).to_have_title('Odisha Tourism: Official Website to Plan Your Travel & Holiday')
            text = p.locator('body').inner_text()
            for section in ['Uniquely Odisha','Odisha Walks','Navigate Odisha','Glimpses of Odisha','Video Gallery']:
                a.check(section in text, f'Home contains {section}', text)
        elif id == 'HOME-002':
            icons = p.locator('link[rel~="icon"]').evaluate_all('es => es.map(e => e.href)')
            assert icons, 'Favicon links must exist'
            for url in set(icons):
                image = p.evaluate("url => new Promise(resolve => { const i=new Image(); i.onload=()=>resolve({url,width:i.naturalWidth,height:i.naturalHeight}); i.onerror=()=>resolve({url,width:0}); i.src=url; })", url)
                a.record(image)
                a.check(image['width'] > 0, 'Favicon asset decodes', image)
        elif id == 'HOME-003':
            self.image_audit()
            self.healthy('home')
        elif id == 'HDR-001':
            logo = p.locator('.main-nav-fixed a').filter(has=p.locator('img')).first
            assert logo.locator('img').evaluate('i => i.complete && i.naturalWidth > 0'), 'Logo must decode'
            logo.click()
            expect(p).to_have_url(case['Tested URL'])
            expect(p).to_have_title(re.compile('Odisha Tourism'))
        elif id in ('HDR-002','HDR-003'):
            menu = self.reveal('Discover' if id == 'HDR-002' else 'Experience')
            expect(menu.locator('a:visible')).to_have_count(8)
        elif id == 'HDR-004':
            p.set_viewport_size({'width':1366,'height':577})
            item = self.reveal('Plan Your Trip').locator('a[href$="/international-sand-art-festival"]')
            item.scroll_into_view_if_needed()
            box = item.bounding_box()
            a.record({'viewport':p.viewport_size,'itemBounds':box})
            assert box and box['y'] + box['height'] <= 577, 'Last event link remains reachable in the viewport'
            item.click()
            expect(p).to_have_url(re.compile('international-sand-art-festival'))
        elif id == 'HDR-005':
            menu = self.reveal('Hamburger')
            for name in ['About Odisha Tourism','Media & Updates','Policies & Legal','Help & Support']:
                expect(menu).to_contain_text(name)
            menu.locator('button[aria-label="Close"]').click()
            expect(menu).not_to_be_in_viewport()
        elif id.startswith('LANG-'):
            lang = id[5:]
            p.locator('#otLangBtn').click()
            p.locator(f'#otLangOpt{lang}').click()
            prefix = {'Hi':'hi','Od':'or','En':'en'}[lang]
            expect(p.locator('html')).to_have_attribute('lang', re.compile(f'^{prefix}(?:-|$)'))
            assert re.search({'Hi':r'[\u0900-\u097f]','Od':r'[\u0b00-\u0b7f]','En':'Experience Odisha'}[lang], p.locator('body').inner_text()), 'Selected-language content must be present'
        elif id.startswith('SEARCH-'):
            self.open_search()
            if id == 'SEARCH-001':
                self.healthy()
            elif id == 'SEARCH-002':
                p.locator('#searchInput').fill('Puri')
                p.get_by_role('button', name='Search', exact=True).click()
                expect(p).to_have_url(case['Tested URL'])
                expect(p).to_have_title('Search Result')
                expect(p.get_by_role('heading', name='Search', exact=True).first).to_be_visible()
                expect(p.locator('body')).to_contain_text('Puri')
                expect(p.locator('[class*="breadcrumb"]').first).to_contain_text('Search Results')
            else:
                p.locator('#closeSearchBtn').click()
                expect(p.locator('#searchInput')).not_to_be_visible()
                expect(p).to_have_url(HOME)
        elif id == 'ACC-001':
            p.get_by_role('button', name='Accessibility Options', exact=True).click()
            panel = p.locator('#accessibilitySidebar')
            expect(panel).to_be_in_viewport()
            expect(panel).to_contain_text(re.compile(r'Dark\s*/\s*Light', re.I))
            p.locator('#acc-close-btn').click()
            expect(panel).not_to_be_in_viewport()
        elif id == 'TOP-001':
            p.locator('#toggleTopbarBtn').click()
            expect(p.locator('#restoreTopbarBtn')).to_be_in_viewport()
            expect(p.locator('#toggleTopbarBtn')).not_to_be_in_viewport()
            p.locator('#restoreTopbarBtn').click()
            expect(p.locator('#toggleTopbarBtn')).to_be_in_viewport()
        elif id == 'TOP-002':
            a.destination()
            p.locator('.topbar-link').filter(has_text='Events Of Odisha').click()
            expect(p).to_have_url(case['Tested URL'])
            expect(p.get_by_role('heading', name='Events & Festivals', exact=True).first).to_be_visible()
            self.image_audit()
            self.healthy()
        elif id == 'A11Y-001':
            p.get_by_role('link', name='Skip to Main Content', exact=True).focus()
            p.keyboard.press('Enter')
            p.keyboard.press('Tab')
            focus = p.evaluate("() => ({html:document.activeElement.outerHTML,inMain:!!document.activeElement.closest('main,#main-content,[role=\"main\"]')})")
            a.record(focus)
            assert focus['inMain'], 'Next focus target should be in main content'
        elif id == 'HDR-006':
            p.locator('.main-nav-fixed a[href*="bookodisha.com"]:visible').click()
            modal = p.locator('#ext-modal-overlay:visible')
            expect(modal).to_be_visible()
            modal.locator('#ext-modal-cancel').click()
            expect(modal).to_have_count(0)
            assert len(p.context.pages) == 1
            expect(p).to_have_url(HOME)
        else:
            raise AssertionError(f'No migrated implementation for {id}')
        a.record({'url':p.url,'title':p.title(),'language':p.locator('html').get_attribute('lang'),'content':p.locator('body').inner_text()[:10000]})
