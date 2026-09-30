const base = require('@playwright/test');
const allure = require('allure-js-commons');
const rows = require('../manual_test_cases/odisha_evidence/consolidated_test_rows.json');
const HOME = 'https://apptourlfr-stg.estpl.net/home';
const test = base.test.extend({
  audit: [async ({ context }, use, info) => {
    const id = info.title.split(' ')[0];
    const row = rows.find(r => r['Test Case ID'] === id);
    const audit = { console: [], network: [], observations: [], page: null, phase: 'home',
      record: (value) => audit.observations.push(value),
      destination: () => { audit.phase = 'destination'; },
    };
    context.on('page', page => {
      audit.page = page;
      page.on('console', msg => { if (msg.type() === 'error') audit.console.push({ phase: audit.phase, page: page.url(), text: msg.text(), location: msg.location() }); });
      page.on('pageerror', error => audit.console.push({ phase: audit.phase, page: page.url(), text: error.message, type: 'uncaught' }));
    });
    context.on('requestfailed', r => audit.network.push({ phase: audit.phase, url: r.url(), method: r.method(), error: r.failure()?.errorText }));
    context.on('response', r => { if (r.status() >= 400) audit.network.push({ phase: audit.phase, url: r.url(), status: r.status() }); });
    await allure.parentSuite('Odisha Tourism');
    await allure.suite(row?.Module || 'Hotel data comparison');
    await allure.feature(id.startsWith('NAV') ? 'Header navigation' : row?.Module || 'Hotels');
    await allure.story(row?.['Test Scenario'] || info.title);
    await allure.severity(({ High: 'critical', Medium: 'normal', Low: 'minor' })[row?.Severity] || 'normal');
    await allure.description(row ? `${row['Test Scenario']}\nPreconditions: ${row.Preconditions}\nManual steps: ${row['Test Steps']}\nEvidence: ${row['Evidence/Screenshot']}\nHistorical outcomes are not used as automated results.` : 'Recheck names and normalized phone numbers for the three exact matches in the saved hotel comparison against the original source workbook.');
    await info.attach('Expected result', { body: row?.['Expected Result'] || 'Confirmed hotel names and phone numbers match the supplied source workbook.', contentType: 'text/plain' });
    await use(audit);
    const urls = context.pages().map(p => p.url());
    await info.attach('Tested URL', { body: JSON.stringify(urls, null, 2), contentType: 'application/json' });
    await info.attach('Console errors', { body: JSON.stringify(audit.console, null, 2), contentType: 'application/json' });
    await info.attach('Network errors', { body: JSON.stringify(audit.network, null, 2), contentType: 'application/json' });
    await info.attach('Actual result', { body: JSON.stringify({ status: info.status, retry: info.retry, observations: audit.observations, errors: info.errors.map(e => e.message), urls }, null, 2), contentType: 'application/json' });
    if (info.status !== info.expectedStatus) {
      for (const [i, page] of context.pages().entries()) {
        try { await info.attach(`Failure screenshot page ${i + 1}`, { body: await page.screenshot({ fullPage: true, timeout: 10000 }), contentType: 'image/png' }); }
        catch (error) { await info.attach('Screenshot capture limitation', { body: String(error), contentType: 'text/plain' }); }
      }
    }
    // A fresh context starts each scenario at home. Return after capturing destination evidence.
    const p = context.pages()[0];
    if (p && !p.isClosed() && p.url() !== HOME) {
      try { await p.goto(HOME, { waitUntil: 'domcontentloaded', timeout: 15000 }); }
      catch (e) { await info.attach('Return home error', { body: String(e), contentType: 'text/plain' }); }
    }
  }, { auto: true }],
});

async function home(page) {
  const response = await page.goto(HOME, { waitUntil: 'domcontentloaded' });
  base.expect(response?.status(), 'Home document HTTP status').toBeLessThan(400);
  await base.expect(page.locator('.main-nav-fixed')).toBeVisible();
  const close = page.locator('#closeCookieBtn');
  if (await close.isVisible()) await close.click();
}
async function reveal(page, name) {
  if (name === 'Hamburger') { await page.locator('#hamburgerBtn').click(); return page.locator('#hamburgerMenu'); }
  const item = page.locator('.main-nav-fixed .nav-item-wrapper').filter({ has: page.locator('.highlight-text', { hasText: new RegExp(`^${name}$`, 'i') }) });
  await item.locator(':scope > a').hover();
  await base.expect(item.locator('.mega-menu-container')).toBeVisible();
  return item.locator('.mega-menu-container');
}
async function imageAudit(page, audit) {
  // Exercise lazy images by scrolling; do not claim coverage of hidden carousel slides/backgrounds.
  const height = await page.evaluate(() => document.body.scrollHeight);
  for (let y = 0; y < height; y += 700) { await page.evaluate(y => window.scrollTo(0, y), y); await page.waitForTimeout(80); }
  await page.waitForFunction(() => [...document.images].filter(i => { const r=i.getBoundingClientRect(); return r.width && r.height && r.right>0 && r.left<innerWidth && getComputedStyle(i).visibility !== 'hidden' && (i.currentSrc || i.getAttribute('src')); }).every(i => i.complete), { }, { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(800);
  const images = await page.locator('img').evaluateAll(imgs => imgs.filter(i => { const r=i.getBoundingClientRect(); return r.width && r.height && r.right>0 && r.left<innerWidth && getComputedStyle(i).visibility !== 'hidden' && (i.currentSrc || i.getAttribute('src')); }).map(i => ({ src: i.currentSrc || i.src, alt: i.alt, complete: i.complete, width: i.naturalWidth })));
  await page.evaluate(() => window.scrollTo(0, 0));
  audit.record({ images });
  base.expect.soft(images.filter(i => !i.complete || i.width === 0), 'Rendered images must finish loading and decode').toEqual([]);
}
function healthy(audit, phase = 'destination') {
  const net = audit.network.filter(e => e.phase === phase && !(e.error === 'net::ERR_ABORTED' && /analytics\.google\.com|google-analytics\.com/.test(e.url)));
  base.expect.soft(audit.console.filter(e => e.phase === phase), 'Browser console/runtime errors').toEqual([]);
  base.expect.soft(net, 'Failed requests or HTTP 4xx/5xx (only cancelled Google analytics excluded)').toEqual([]);
}
module.exports = { test, expect: base.expect, home, reveal, imageAudit, healthy, rows, HOME };
