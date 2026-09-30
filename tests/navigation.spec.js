const { test, expect, home, reveal, imageAudit, healthy, rows } = require('./fixtures');
const inventory = require('../manual_test_cases/odisha_evidence/navigation_inventory.json');
const externalIds = [55, 71, 72, 73, 74, 75];
const canonical = url => { const u = new URL(url); return u.origin + u.pathname.replace(/\/$/, ''); };
const normalize = s => s.replace(/[’‘]/g, "'").replace(/\s+/g, ' ').trim().toLowerCase();

for (const row of rows.filter(r => r['Test Case ID'].startsWith('NAV'))) {
  const id = row['Test Case ID'];
  const index = Number(id.slice(4));
  test(`${id} ${row['Test Scenario']}`, async ({ page, context, audit }) => {
    await test.step('Start from home and open the recorded header menu', async () => { await home(page); });
    let target = page;
    if (externalIds.includes(index)) {
      await test.step('Click external header link and confirm its destination', async () => {
        let area = page.locator('.main-nav-fixed');
        if (index !== 71) area = await reveal(page, 'Hamburger');
        const domains = {55:'dot.odisha.gov.in',71:'bookodisha.com',72:'facebook.com',73:'x.com/',74:'instagram.com',75:'youtube.com'};
        const link = area.locator(`a[href*="${domains[index]}"]:visible`).first();
        const href = await link.getAttribute('href');
        audit.record({ advertisedURL: href });
        const opened=[];
        const capture=p=>opened.push(p);
        context.on('page',capture);
        audit.destination();
        try {
          await link.click();
          const modal = page.locator('#ext-modal-overlay:visible');
          // The site can attach its confirmation handler after DOMContentLoaded.
          // Both observed paths must still resolve to the recorded official destination.
          await expect.poll(async()=>opened.length>0 || await modal.isVisible(),{timeout:15000}).toBe(true);
          if (!opened.length) {
            await expect(modal).toContainText(new URL(href).hostname);
            await modal.locator('#ext-modal-confirm').click();
          }
          await expect.poll(()=>opened.length,{timeout:35000}).toBeGreaterThan(0);
          target=opened[0];
          audit.record({externalFlow:await modal.isVisible()?'confirmation remained visible':'new tab opened',popupURL:target.url()});
        } finally {
          context.off('page',capture);
        }
        await target.waitForLoadState('domcontentloaded');
        await target.waitForTimeout(2500);
      });
      await test.step('Verify external URL, content, images and diagnostics', async () => {
        const body = await target.locator('body').innerText();
        const title = await target.title();
        audit.record({ url: target.url(), title, content: body.slice(0, 12000), breadcrumb: 'Not applicable to external home/profile' });
        expect.soft(canonical(target.url()), 'External destination including approved canonical redirects').toBe(canonical(row['Tested URL']));
        expect.soft(body, 'No TLS interstitial, blocked page or page error').not.toMatch(/your connection is not private|ERR_CERT_|access denied|internal server error|page not found/i);
        expect.soft(title + ' ' + body, 'Official Odisha identity visible').toMatch(/odisha|tourism/i);
        expect.soft(body.length, 'External content is populated').toBeGreaterThan(100);
        await imageAudit(target, audit);
        healthy(audit);
      });
      return;
    }
    const recorded = inventory.find(n => n.index === index);
    const menu = recorded?.menu || 'Hamburger';
    const url = row['Test Data'];
    const heading = row['Actual Result'].match(/Heading\(s\): (.*?)(?:;|\. Breadcrumb:)/s)?.[1];
    const breadcrumb = row['Actual Result'].match(/Breadcrumb: (.*?)\. Content:/s)?.[1];
    await test.step(`Click ${menu} > ${recorded?.name || row['Test Scenario'].replace(/^Open /, '')}`, async () => {
      const area = await reveal(page, menu);
      const link = area.locator(`a[href="${url}"]:visible`);
      await expect(link).toHaveCount(1);
      audit.destination();
      await link.click();
      await page.waitForLoadState('domcontentloaded');
      await expect(page).toHaveURL(url);
    });
    await test.step('Verify title, page heading, breadcrumb and populated content', async () => {
      await page.waitForTimeout(650);
      const body = await page.locator('body').innerText();
      const headings = await page.locator('h1:visible,h2:visible,h3:visible').allTextContents();
      const crumbs = await page.locator('[class*="breadcrumb"]:visible').allTextContents();
      audit.record({ url: page.url(), title: await page.title(), headings, breadcrumbs: crumbs, content: body.slice(0, 16000) });
      expect.soft(await page.title(), 'Nonempty document title').not.toBe('');
      expect.soft(body, 'No page-level server error').not.toMatch(/\b404\s*(?:error|not found)|\b500\s*(?:error|internal)|internal server error/i);
      if (index === 29) {
        expect.soft(await page.locator('img:visible').count(), 'Map viewer renders an image').toBeGreaterThan(0);
      } else {
        expect.soft(headings.map(normalize), `Expected heading: ${heading}`).toContain(normalize(heading));
        const expectedCrumbs = breadcrumb?.replace(/^\s*\/\s*/, '')?.split('/').map(normalize) || [];
        expect.soft(crumbs.length, 'Breadcrumb present').toBeGreaterThan(0);
        for (const text of expectedCrumbs) expect.soft(normalize(crumbs.join(' ')), `Breadcrumb segment: ${text}`).toContain(text);
        expect.soft(body.length, 'Substantial page content').toBeGreaterThan(250);
      }
      // Explicit regressions for observed editorial defects; never bless the saved failure as expected.
      if (index === 1) expect.soft(/nearly\s*480\s*km/i.test(body) && /nearly\s*574\s*km/i.test(body), 'Coastline figures must not contradict').toBe(false);
      if (index === 3) expect.soft(body).not.toContain('information displayed should reflect');
      if ([18,20].includes(index)) expect.soft(body).not.toMatch(/DISTRICTS THAT SHAPE THE COAST/i);
      if (index === 36) expect.soft(body).not.toContain('Government Approved Tour Guides');
      if (index === 49) expect.soft(/Varanasi/i.test(body) && /Ahmedabad/i.test(body), 'Single event edition location').toBe(false);
      if (index === 50) expect.soft(body).not.toMatch(/LEGENDARY SWEET/i);
    });
    await test.step('Scroll through images and inspect browser diagnostics', async () => { await imageAudit(page, audit); healthy(audit); });
  });
}
