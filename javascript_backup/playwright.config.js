const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 1,
  workers: 2,
  timeout: 90000,
  expect: { timeout: 10000 },
  outputDir: 'test-results/artifacts',
  reporter: [
    ['list'],
    ['json', { outputFile: 'test-results/execution.json' }],
    ['allure-playwright', { resultsDir: 'allure-results', detail: true, suiteTitle: false }],
  ],
  use: {
    baseURL: 'https://apptourlfr-stg.estpl.net',
    viewport: { width: 1366, height: 900 },
    actionTimeout: 15000,
    navigationTimeout: 35000,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'on-first-retry',
    ignoreHTTPSErrors: false,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1366, height: 900 } } }],
});
