const { test, expect, home, reveal, imageAudit, healthy, rows, HOME } = require('./fixtures');
const login = page => page.locator('[role="dialog"][aria-labelledby="otlxTitle"]');

for (const row of rows.filter(r => !/^(NAV|LIMIT)-/.test(r['Test Case ID']))) {
  const id = row['Test Case ID'];
  test(`${id} ${row['Test Scenario']}`, async ({ page, context, audit }) => {
    await test.step('Load home in a fresh anonymous browser context', () => home(page));
    await test.step(row['Test Scenario'], async () => {
      if (id === 'HOME-001') {
        await expect(page).toHaveURL(HOME);
        await expect(page).toHaveTitle('Odisha Tourism: Official Website to Plan Your Travel & Holiday');
        const text = await page.locator('body').innerText();
        for (const section of ['Uniquely Odisha','Odisha Walks','Navigate Odisha','Glimpses of Odisha','Video Gallery']) expect.soft(text).toContain(section);
      } else if (id === 'HOME-002') {
        const icons = await page.locator('link[rel~="icon"]').evaluateAll(es => es.map(e => e.href));
        expect(icons.length).toBeGreaterThan(0);
        for (const url of [...new Set(icons)]) {
          const image = await page.evaluate(url => new Promise(resolve => { const i = new Image(); i.onload = () => resolve({ url, width:i.naturalWidth, height:i.naturalHeight }); i.onerror = () => resolve({ url, width:0 }); i.src=url; }), url);
          audit.record(image); expect.soft(image.width).toBeGreaterThan(0);
        }
      } else if (id === 'HOME-003') { await imageAudit(page, audit); healthy(audit, 'home'); }
      else if (id === 'HDR-001') {
        const logo = page.locator('.main-nav-fixed a').filter({ has: page.locator('img') }).first();
        expect(await logo.locator('img').evaluate(i => i.complete && i.naturalWidth > 0)).toBe(true);
        await logo.click(); await expect(page).toHaveURL(row['Tested URL']); await expect(page).toHaveTitle(/Odisha Tourism/);
      } else if (['HDR-002','HDR-003'].includes(id)) {
        const menu = await reveal(page, id === 'HDR-002' ? 'Discover' : 'Experience');
        await expect(menu.locator('a:visible')).toHaveCount(8);
      } else if (id === 'HDR-004') {
        await page.setViewportSize({ width:1366,height:577 });
        const menu = await reveal(page, 'Plan Your Trip');
        const item = menu.locator('a[href$="/international-sand-art-festival"]');
        await item.scrollIntoViewIfNeeded();
        const box = await item.boundingBox(); audit.record({ viewport:page.viewportSize(), itemBounds:box });
        expect(box.y + box.height, 'Last event link remains reachable in the viewport').toBeLessThanOrEqual(577);
        await item.click(); await expect(page).toHaveURL(/international-sand-art-festival/);
      } else if (id === 'HDR-005') {
        const menu = await reveal(page,'Hamburger');
        for (const name of ['About Odisha Tourism','Media & Updates','Policies & Legal','Help & Support']) await expect(menu).toContainText(name);
        await menu.locator('button[aria-label="Close"]').click(); await expect(menu).not.toBeInViewport();
      } else if (id.startsWith('LANG-')) {
        const lang = id.slice(5); await page.locator('#otLangBtn').click(); await page.locator(`#otLangOpt${lang}`).click();
        const prefix = {Hi:'hi',Od:'or',En:'en'}[lang];
        await expect(page.locator('html')).toHaveAttribute('lang',new RegExp(`^${prefix}(?:-|$)`));
        const body = await page.locator('body').innerText();
        expect(body).toMatch({Hi:/[\u0900-\u097f]/,Od:/[\u0b00-\u0b7f]/,En:/Experience Odisha/}[lang]);
      } else if (id.startsWith('SEARCH-')) {
        audit.destination(); await page.locator('#searchTriggerBtn').click(); await expect(page.locator('#searchInput')).toBeVisible();
        if (id === 'SEARCH-001') healthy(audit);
        if (id === 'SEARCH-002') {
          await page.locator('#searchInput').fill('Puri'); await page.getByRole('button',{name:'Search',exact:true}).click();
          await expect(page).toHaveURL(row['Tested URL']); await expect(page).toHaveTitle('Search Result');
          await expect(page.getByRole('heading',{name:'Search',exact:true}).first()).toBeVisible();
          await expect(page.locator('body')).toContainText('Puri'); await expect(page.locator('[class*="breadcrumb"]').first()).toContainText('Search Results');
        }
        if (id === 'SEARCH-003') { await page.locator('#closeSearchBtn').click(); await expect(page.locator('#searchInput')).not.toBeVisible(); await expect(page).toHaveURL(HOME); }
      } else if (id.startsWith('ACCOUNT-')) {
        audit.destination(); await page.locator('#otUserIconBtn').click(); await expect(login(page)).toBeVisible();
        if (id === 'ACCOUNT-001') {
          for (const name of ['Email ID / Mobile Number','Password','Enter Captcha']) await expect(login(page).getByPlaceholder(name,{exact:true})).toBeVisible();
          for (const text of ['Forgot Password','Sign Up','Official Login']) await expect(login(page)).toContainText(text);
          await login(page).locator('button[aria-label="Close"]').click(); await expect(login(page)).not.toBeVisible();
        } else {
          const names = {'ACCOUNT-ForgotPassword':'Forgot Password?','ACCOUNT-SignUp':'Sign Up','ACCOUNT-OfficialLogin':'Official Login'};
          await login(page).getByText(names[id],{exact:true}).click();
          await expect(page).toHaveURL(row['Tested URL']);
          const content = {'ACCOUNT-ForgotPassword':'Back to Login','ACCOUNT-SignUp':'Register Here','ACCOUNT-OfficialLogin':'Official Portal Login'};
          await expect(page.locator('body')).toContainText(content[id]);
          if (id === 'ACCOUNT-SignUp') await expect(page.locator('[class*="breadcrumb"]').first()).toContainText('Visitor Registration');
          if (id !== 'ACCOUNT-ForgotPassword') await imageAudit(page,audit);
          else await expect(login(page).getByPlaceholder('Email ID / Mobile Number',{exact:true})).toBeVisible();
          healthy(audit);
        }
      } else if (id === 'ACC-001') {
        await page.getByRole('button',{name:'Accessibility Options',exact:true}).click();
        await expect(page.locator('#accessibilitySidebar')).toBeInViewport();
        await expect(page.locator('#accessibilitySidebar')).toContainText(/Dark\s*\/\s*Light/i);
        await page.locator('#acc-close-btn').click(); await expect(page.locator('#accessibilitySidebar')).not.toBeInViewport();
      } else if (id === 'TOP-001') {
        await page.locator('#toggleTopbarBtn').click(); await expect(page.locator('#restoreTopbarBtn')).toBeInViewport();
        await expect(page.locator('#toggleTopbarBtn')).not.toBeInViewport(); await page.locator('#restoreTopbarBtn').click(); await expect(page.locator('#toggleTopbarBtn')).toBeInViewport();
      } else if (id === 'TOP-002') {
        audit.destination(); await page.locator('.topbar-link').filter({hasText:'Events Of Odisha'}).click(); await expect(page).toHaveURL(row['Tested URL']);
        await expect(page.getByRole('heading',{name:'Events & Festivals',exact:true}).first()).toBeVisible(); await imageAudit(page,audit); healthy(audit);
      } else if (id === 'A11Y-001') {
        const skip = page.getByRole('link',{name:'Skip to Main Content',exact:true}); await skip.focus(); await page.keyboard.press('Enter'); await page.keyboard.press('Tab');
        const focus = await page.evaluate(() => ({ html: document.activeElement.outerHTML, inMain: !!document.activeElement.closest('main,#main-content,[role="main"]') }));
        audit.record(focus); expect(focus.inMain,'Next focus target should be in main content').toBe(true);
      } else if (id === 'HDR-006') {
        await page.locator('.main-nav-fixed a[href*="bookodisha.com"]:visible').click();
        const modal=page.locator('#ext-modal-overlay:visible'); await expect(modal).toBeVisible(); await modal.locator('#ext-modal-cancel').click();
        await expect(modal).toHaveCount(0); expect(context.pages()).toHaveLength(1); await expect(page).toHaveURL(HOME);
      } else { throw new Error(`No implementation for ${id}`); }
      audit.record({ url:page.url(), title:await page.title(), language:await page.locator('html').getAttribute('lang'), content:(await page.locator('body').innerText()).slice(0,10000) });
    });
  });
}
