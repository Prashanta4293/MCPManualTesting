# JavaScript to Python migration mapping

| JavaScript source | Python replacement | Tests | Fixtures / utilities |
|---|---|---:|---|
| tests/header.spec.js | tests/test_header.py (19); tests/test_visitor_login.py (4) | 23 | HomePage, HeaderPage, VisitorLoginPage, audit, context, page |
| tests/hotels.spec.js | tests/test_hotels.py | 1 | HotelsPage, existing JSON/Excel source match data, audit |
| tests/navigation.spec.js | tests/test_navigation.py | 75 | NavigationPage, HomePage, BasePage, audit |
| tests/fixtures.js | tests/conftest.py; pages/base_page.py; pages/home_page.py; pages/data.py | 0 | pytest fixtures/hooks; context isolation; diagnostics; failure media; first-retry trace; soft checks |
| playwright.config.js | pytest.ini; tests/conftest.py; requirements.txt | 0 | Chromium, viewport/timeouts, retries, Allure, failure artifacts |
| scripts/run-tests.js | scripts/run_tests.py | 0 | Archive generated results; pytest subprocess |
| scripts/test-report.js | scripts/test_report.py; scripts/report.py | 0 | Run pytest and generate report even on failures |
| scripts/report-summary.js | scripts/report_summary.py | 0 | Actual attempt aggregation; comparison; blocked subset of skips |
| scripts/inspect-results.js | scripts/inspect_results.py | 0 | Read latest actual Allure outcomes |
| scripts/verify-allure.js | scripts/verify_allure.py | 0 | Verify metadata and result/fixture attachments |
| scripts/merge-rerun.js | scripts/merge_rerun.py | 0 | Explicit real-result merge and provenance |
| package.json; package-lock.json | requirements.txt; requirements-lock.txt; README.md | 0 | Python dependency and command equivalents |
| New requested scenario | tests/test_visitor_login.py (VISITOR-LOGIN-001) | 1 | Headed Chromium, environment credentials, human CAPTCHA, no retries/recordings |

Original: 99; Python: 100. Missing original cases: 0. Backup checksum errors: 0.

All existing IDs, test names, source data and expected results are preserved. Positive Visitor login is new. LIMIT-001 and LIMIT-002 remain historical scope exclusions.

Browser DOM evaluation uses Playwright's browser API; no Python test imports or invokes the JavaScript test runner, .spec.js files, package.json or playwright.config.js.
