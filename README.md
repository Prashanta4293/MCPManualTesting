# Odisha Tourism — Python Playwright / pytest

This project runs Python Playwright's sync API through pytest and pytest-playwright. It targets https://apptourlfr-stg.estpl.net/home. The 99 original executable JavaScript cases are preserved, plus one requested attended positive Visitor login case.

**Migration status:** Python migration and approved cleanup are complete. The post-cleanup Chromium regression recorded 100 cases: 71 passed, 28 failed and one skipped/blocked attended positive login. All 99 original outcomes match the JavaScript baseline. Two failed cases were re-executed to recover missing screenshots; the combined report records this provenance. Original sources remain under `javascript_backup/`; mapping, verification and the approved removal manifest are under `migration/`.

## Setup

### Visitor Login workbook phase (TC16–TC41)

The selected specification is imported from `test_data/Odisha_Tourism_Web_Portal_Test_Cases_v1.0_2026-06-01.xlsx`, worksheet `Test_Cases`. Existing workbook Actual Result/Status values are excluded. See `manual_test_cases/visitor_login_20261003/selected_cases.md` and `data/visitor_login_data.json` for the selected rows. Historical tests and migration backups are preserved.

```powershell
.\venv\Scripts\python.exe scripts/import_visitor_login_cases.py
.\venv\Scripts\python.exe -m pytest tests/test_visitor_login.py::test_workbook_visitor_login --collect-only -q
.\venv\Scripts\python.exe scripts/run_visitor_login.py
.\venv\Scripts\python.exe scripts/verify_allure.py
.\venv\Scripts\python.exe scripts/report.py generate
.\venv\Scripts\python.exe scripts/report.py open
```

The scoped runner archives previous generated reports, executes negative cases first, and runs attended cases separately in headed Chromium. It records one fresh result for each selected case, without automatic retries. JSON, Markdown and Excel execution records are generated under `manual_test_cases/visitor_login_20261003/`; browser artifacts are under `test-results/visitor-login/` and `allure-results/`.

TC36, TC39 and TC40 are semi-automated. The suite loads the project-root `.env` using python-dotenv into `VISITOR_EMAIL` and `VISITOR_PASSWORD` (local values take precedence). It never reads `.env.example` or modifies `.env`. Keep `.env` ignored by Git and never print the credential values. Never pass a password as a command-line argument. For an attended run:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_visitor_login.py::test_workbook_visitor_login -k TC40 --manual-login --headed -s --reruns 0
.\venv\Scripts\python.exe -m pytest tests/test_visitor_login.py::test_workbook_visitor_login -k TC39 --manual-login --headed -s --reruns 0
```

Enter CAPTCHA in the browser, then type `CONFIRM` in the terminal. A filled field or focus change is never treated as confirmation. For agent-assisted execution, `--captcha-confirm-dir test-results/captcha-confirmation` creates a per-case token handshake; the agent writes the matching confirmation only after the tester explicitly confirms in chat. Stale confirmations are rejected. CAPTCHA is never decoded or solved by the suite.

Attended login is never traced or video-recorded. No screenshot is captured while the login form is visible. After authenticated login is verified and the form is hidden, evidence uses a fully masked screenshot and sanitized observations; email and password are never attached. Stable cases use disposable password input and record failure traces/videos. Missing roles and initial CAPTCHA generation failures remain failed assertions; refresh recovery is tested independently.

Use the existing virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
```

If PowerShell activation is restricted, use `venv\Scripts\python.exe` directly. `requirements-lock.txt` pins the tested top-level package versions; `requirements.txt` declares compatible ranges. Java and the independent global Allure CLI are needed only for HTML reporting. The global CLI was found at `C:\Tools\allure-2.46.1\bin\allure.bat`; Node.js and node_modules are not required by pytest.

## Collect and execute

```powershell
python -m pytest --collect-only
python scripts/verify_migration.py
python scripts/run_tests.py -n 2
python scripts/run_tests.py --headed
python scripts/test_report.py -n 2
```

The wrapper archives previous generated outputs under `run-history/`, recreates Allure executor/environment metadata, runs pytest, and writes actual result counts and comparison with the preserved JavaScript baseline. It does not delete historical evidence. Avoid simultaneous runs writing the same result directory.

Direct pytest is also supported:

```powershell
pytest --alluredir=allure-results
```

Direct runs append to existing Allure results and event logs. Use the Python wrapper for an isolated execution. By default all 100 cases are collected; the positive login case is explicitly blocked/skipped unless its attended prerequisites are enabled. Blocked is reported as a subset of pytest/Allure skipped, not an extra test.

One retry is configured for migrated failures; the positive authentication test has no retry to avoid duplicate login submissions. Test counts exclude retry attempts. Ordinary cases use isolated Chromium contexts at 1366×900, 15-second action waits, 35-second navigation waits and 10-second assertions; the overflow regression uses 1366×577.

## Positive Visitor login and credential privacy

Configure `VISITOR_EMAIL` and `VISITOR_PASSWORD` privately in the process environment or an untracked local `.env` based on `.env.example`. Never add real credentials to code, test data, reports or command arguments.

Run the attended case separately, with a single worker:

```powershell
python scripts/run_tests.py tests/test_visitor_login.py -m positive --manual-login --headed -s
```

The test launches headed Chromium, fills credentials from the environment, focuses the CAPTCHA input, and waits up to 120 seconds for the human to enter it. Enter the complete CAPTCHA and press Tab when finished; this prevents submitting after the first typed character. Once non-empty and focus leaves the input, Login is submitted once. Automation never extracts, solves, supplies, disables, changes or bypasses the CAPTCHA. Missing prerequisites or no completed manual CAPTCHA entry are reported as blocked, never passed. A visible authenticated logout control is required to prove success; modal disappearance alone is insufficient. That new success locator still requires verification with valid credentials.

Videos, traces, DOM dumps, browser console and network diagnostics are disabled for the credential-bearing case. Failure screenshots mask the entire page body, including account identity. Positive-login exceptions are sanitized before reaching Allure; credentials are never pytest/Allure parameters. Ordinary anonymous-case textual attachments also redact configured credential values.

All other cases remain read-only except the existing destination search. Registration, password-reset OTP, booking, payment and contact submissions are not performed.

## Allure reports

```powershell
allure generate allure-results --clean -o allure-report
allure open allure-report
python scripts/report.py generate
python scripts/report.py open
python scripts/verify_allure.py
python scripts/report_summary.py
```

If a global Allure CLI is unavailable, the optional report-only fallback is:

```powershell
npx.cmd allure-commandline generate allure-results --clean -o allure-report
npx.cmd allure-commandline open allure-report
```

The fallback requires Node/npm, but does not run JavaScript tests. Keep required Allure support until a working global CLI is available.

Raw results: `allure-results/`. HTML: `allure-report/index.html` (serve with Allure open). Browser artifacts and execution summaries: `test-results/python/`, `test-results/python-summary.json`, `test-results/python-summary.md`.

Allure includes preserved IDs/names, suite, feature, story, severity, descriptions, steps, expected result, actual observations, tested URLs, and console/network errors. Anonymous failures retain screenshots and videos; first retries capture traces. Positive-login recording exceptions are described above. Prior results are not imported as new passes or expected failures.

## Structure and evidence

- `pages/`: reusable home/header, navigation, hotel, visitor-login and image/diagnostic page objects.
- `tests/conftest.py`: browser contexts, metadata, privacy, attachments, retry artifacts and actual pytest event records.
- `tests/test_header.py`: 19 migrated home/header/control cases.
- `tests/test_navigation.py`: 75 migrated navigation cases.
- `tests/test_hotels.py`: one migrated confirmed-workbook-match case.
- `tests/test_visitor_login.py`: four migrated account-control cases and one new positive login.
- `scripts/*.py`: execution, reporting, verification, evidence extraction and explicit targeted-result merging.
- Existing JSON/CSV/Excel data, screenshots and evidence remain in their original directories. `server.py` is an unrelated retained Python MCP utility.

The manual report data, navigation inventory and reviewed headings are the same evidence-based baseline as the JavaScript suite. Strict URL/content/image and diagnostic assertions are retained, including the known editorial regressions. Cancelled Google Analytics requests remain the sole network-health exception. Destination checks exclude home setup diagnostics; isolated control checks collect unrelated diagnostics without declaring every homepage resource healthy.

External links may open a confirmation dialog or a new tab directly. Both paths must lead to the recorded official destination. Certificate errors are not bypassed. Failure classifications distinguish product assertions, external/environment errors and suspected automation errors; changed outcomes require review of fresh attachments.

Hidden carousel states, exhaustive CSS backgrounds, native browser-tab favicon appearance, mobile accessibility, native screen readers and media playback remain outside the original coverage. LIMIT-001 and LIMIT-002 remain historical exclusions, not passing tests.

## Historical Excel/manual reports

```powershell
python scripts/extract-evidence.py
python manual_test_cases/build_odisha_report.py --output-dir migration/manual-report-check
```

These regenerate from saved evidence; they do not claim new browser execution. The output-directory option verifies generation without overwriting the original manual reports. The Python migration's fresh outcomes are recorded separately.

## Approved cleanup

See `migration/removal-proposal.md` and `migration/removal-manifest.json` for every proposed source/dependency file. The user approved Phase 3 removal on 2026-10-01. The listed active JavaScript/package files and local node_modules were removed. Backups, evidence, test data, screenshots, spreadsheets, reports, the virtual environment and global Allure support are retained. Post-cleanup regression results are recorded in migration/verification-summary.md.

References: [Playwright pytest plugin](https://playwright.dev/python/docs/test-runners), [Allure pytest](https://allurereport.org/docs/pytest/).
