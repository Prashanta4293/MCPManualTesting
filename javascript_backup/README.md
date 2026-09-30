# Odisha Tourism Playwright regression project

Tests target https://apptourlfr-stg.estpl.net/home using anonymous Chromium contexts. They click header navigation from home, check destination URLs, headings, breadcrumbs, content, rendered images and browser diagnostics. The suite performs no login, registration, contact, booking or payment submissions. Search is read-only.

## Run and view results

Node.js, the Playwright Chromium browser and Java (for Allure 2) must be installed.

```powershell
npm.cmd ci
npx.cmd playwright install chromium
npm.cmd test
npm.cmd run test:headed
npm.cmd run report:generate
npm.cmd run report:open
npm.cmd run test:report
```

`test:report` generates the HTML report even when tests fail, then returns a nonzero status for failures. `npm.cmd run report:summary` regenerates the counts and failed names from the actual Playwright JSON output. HTML: `allure-report/index.html`; raw Allure: `allure-results/`; execution JSON, concise summary and browser artifacts: `test-results/`. Use `report:open` to serve the HTML report; opening the index directly may be restricted by the browser.

Each test command archives previous generated results/reports under `run-history/` to prevent stale Allure cases from contaminating a new execution. Do not run two npm test processes simultaneously. A filtered run intentionally reports only its selected cases. Two workers limit load; each failure receives one retry. Counts are test cases, not retry attempts; a retry recovery is explicitly reported as flaky.

## Evidence and coverage

- `manual_test_cases/odisha_evidence/consolidated_test_rows.json`: IDs, descriptions, expected outcomes, breadcrumbs and reviewed heading baseline for the 98 executable homepage scenarios. All 75 navigation cases and 23 home/header/control cases are implemented. Previous statuses are never imported as new outcomes or marked expected failures.
- `manual_test_cases/odisha_evidence/navigation_inventory.json`: reviewed menu names and exact destination hrefs.
- `artifacts/`: older header snapshots and hotel browser extraction. `hotels-cards.json` verifies provenance of the supplemental hotel comparison case.
- `comparison_results/hotel_web_excel_comparison.xlsx`: only the three exact name matches are selected. Ambiguous matches, old mismatch outcomes and spreadsheet-only records are not asserted as correct live data.
- `test_data/Hotels Under Tourism List.xlsx`: original names and phone numbers for those matched records. `tests/data/hotel-matches.json` is a checked-in export with source rows; regenerate with `venv\Scripts\python.exe scripts/extract-evidence.py` (requires openpyxl). The supplemental case expands the live listing and rechecks these records in Chromium.

The earlier currency-converter workbook is a separate execution; this homepage conversion covers navigation to its page, not its internal calculator scenarios. Likewise, the supplemental hotel test is not a complete rerun of the workbook reconciliation.

## Reporting and assertion policy

`playwright.config.js` configures allure-playwright, screenshots on failure, retained failure videos and a trace on first retry. Tests provide Allure suite, feature, story, severity, description and named steps. Every attempt attaches expected result, actual observations/errors, tested URLs, console errors and network errors. Failure screenshots include popup tabs. Native Playwright screenshots/videos/traces are also attached by the reporter.

Diagnostics distinguish home setup from destination activity. Navigation health assertions apply to the destination phase so a known home resource error does not falsely identify every destination as broken. The home health scenario checks the home phase. All diagnostics remain attached. Only cancelled Google Analytics `net::ERR_ABORTED` requests are excluded from health assertions; HTTP failures and other runtime/network errors fail them. Isolated header behavior tests collect diagnostics without requiring every unrelated homepage resource to pass. SEARCH-001 explicitly checks search-opening runtime errors; SEARCH-002 independently checks the search result flow.

External navigation observes either the site's confirmation modal or a direct new tab, then verifies the official destination, allowing the previously observed Facebook/YouTube canonical URL. The site's confirmation handler can attach after initial page readiness, so tests accept either observed navigation path. Certificate errors are not bypassed. An inaccessible external page is a failed automated check with evidence, not a passing or silently skipped result. External failures may be browser/network restrictions rather than staging application defects.

If test-code corrections require a targeted rerun, `node scripts/merge-rerun.js run-history/<full-run-directory>` can assemble its actual outcomes with the unchanged full-run cases. It records the source timestamps and replaced case names in `test-results/execution-provenance.json`; original full results remain archived. This is an explicit combined execution, not a claim that every case ran again at the rerun timestamp.

## Explicit limitations

The two manual scope rows LIMIT-001 and LIMIT-002 are exclusions, not executable tests: prohibited submissions and deep mobile/accessibility/media assessment. They are not included in pass or skip counts. Native tab favicon rendering, native screen readers, hidden carousel slides, exhaustive CSS background images and media playback are not claimed as verified. The favicon test checks the referenced asset can decode. Image checks scroll the document and examine rendered, nonempty-src IMG elements; carousel interaction is outside scope. Headings and hrefs are evidence-based baselines, not an independently supplied product specification. A failed prerequisite prevents later steps of that individual test from executing; the actual attachment records the failure rather than marking those steps passed.

Official configuration references: [Playwright test use options](https://playwright.dev/docs/test-use-options), [Allure Playwright](https://allurereport.org/docs/playwright/).
