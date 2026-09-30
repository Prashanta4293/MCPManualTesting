const { test, expect, home, reveal } = require('./fixtures');
const matches = require('./data/hotel-matches.json');
const cards = require('../artifacts/hotels-cards.json');
test('HOTEL-DATA-001 Recheck confirmed workbook hotel names and phone numbers', async ({ page,audit }) => {
  await test.step('Open Hotels through the home header', async () => {
    await home(page); const menu=await reveal(page,'Plan Your Trip'); audit.destination(); await menu.locator('a[href$="/hotels"]').click(); await expect(page).toHaveURL(/\/hotels$/);
  });
  await test.step('Expand the saved listing and verify confirmed source records', async () => {
    const more=page.getByRole('button',{name:/load more/i});
    await expect(more).toBeVisible();
    for(let i=0;i<30 && await more.isVisible();i++) { await more.click(); await page.waitForTimeout(350); }
    await expect(more).not.toBeVisible();
    const body=await page.locator('body').innerText();
    for (const match of matches) {
      const saved=cards.find(c=>c.name === match.name); expect(saved,'Match must exist in saved browser evidence').toBeTruthy();
      const heading=page.getByText(match.name,{exact:true}); await expect(heading).toBeVisible();
      const text=await heading.locator('..').innerText();
      audit.record({source:match,liveCard:text});
      expect.soft(text.replace(/\D/g,''),`${match.name} phone from source workbook`).toContain(match.phone.replace(/\D/g,''));
    }
    audit.record({expandedListing:body});
  });
});
