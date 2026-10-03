# Final verification ? 2026-10-03

- Workbook checksum unchanged; only its eight specification columns imported.
- All 26 selected cases discoverable. Full project collection: 126 (100 existing plus 26 new); unrelated tests not executed in this phase.
- MCP manual: 19 passed, four failed, three blocked.
- Pytest Chromium: 19 passed, four failed, three blocked. No successful login claim.
- Failed: TC21, TC22, TC23, TC34. Blocked: TC36, TC39, TC40 (credentials absent; no human CAPTCHA confirmation).
- The negative group ran first. After discovering pytest-playwright's default output cleanup, its output was isolated under test-results/pytest-native and five negative cases were re-executed to restore standalone records. All original Allure attempts remain; 31 attempts resolve to 26 unique cases.
- Allure audit: 31 attempts, zero problems. Epic/feature/story/severity/descriptions verified. 23 screenshots and four failure traces/videos exist.
- Final HTML widget counts verified: 26 total, 19 passed, four failed, three skipped, zero broken. Skips represent the three blocked cases.
- Excel verified: 26 records each on MCP Manual and Python Execution sheets. Terminal escape characters are stripped for Excel only; full evidence remains in JSON/Allure.
- Allure CLI's analytics requests were sandbox-blocked; local HTML generation succeeded.

## Files created

- conftest.py
- data/visitor_login_data.json
- utilities/__init__.py
- utilities/visitor_fixtures.py
- scripts/import_visitor_login_cases.py
- scripts/run_visitor_login.py
- scripts/visitor_login_report.py
- manual_test_cases/visitor_login_20261003/ (selection, collection, manual attempts/results, screenshots, summary, Excel and verification)
- test-results/visitor-login/ and fresh allure-results/, allure-report/ artifacts

## Existing files changed

- pages/visitor_login_page.py: workbook Page Object methods; old methods retained.
- tests/test_visitor_login.py: 26 data-driven cases; old tests retained.
- tests/conftest.py: delegate workbook evidence fixture and isolate collection output.
- pytest.ini: manual_captcha marker and safe plugin temporary output location.
- README.md: scoped commands, environment prerequisites and explicit confirmation workflow.

Previous generated reports were archived under run-history/python-20261003T060807981704Z. JavaScript backups and unrelated tests were retained.

## Additional verification command used

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_visitor_login.py::test_workbook_visitor_login -m negative --manual-login --reruns 0
```

The full command sequence is in summary.md. Setup/collection failures were not counted as browser passes. No credentials were printed, stored or attached.
