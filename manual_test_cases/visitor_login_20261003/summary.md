# Visitor Login TC16–TC41 execution

Specification: Test_Cases worksheet; historical outcomes ignored.

Selected: 26; fully automated: 23; semi-automated: 3; manual-only: 0.

manual: Passed: 19, Failed: 4, Blocked: 3, Not Executed: 0.

pytest: Passed: 19, Failed: 4, Blocked: 3, Not Executed: 0.

| ID | Scenario | Approach | MCP manual | Fresh pytest |
|---|---|---|---|---|
| TC16 | Verify login popup display | Automated | Passed | Passed |
| TC17 | Verify login title display | Automated | Passed | Passed |
| TC18 | Verify welcome message display | Automated | Passed | Passed |
| TC19 | Verify popup close functionality | Automated | Passed | Passed |
| TC20 | Verify Visitor tab display and selection | Automated | Passed | Passed |
| TC21 | Verify Hotelier tab selection | Automated | Failed | Failed |
| TC22 | Verify Travel Agent tab selection | Automated | Failed | Failed |
| TC23 | Verify switching between user types | Automated | Failed | Failed |
| TC24 | Verify input field display | Automated | Passed | Passed |
| TC25 | Verify email input acceptance | Automated | Passed | Passed |
| TC26 | Verify mobile number input acceptance | Automated | Passed | Passed |
| TC27 | Verify mandatory field validation | Automated | Passed | Passed |
| TC28 | Verify password field display | Automated | Passed | Passed |
| TC29 | Verify password entry | Automated | Passed | Passed |
| TC30 | Verify password masking | Automated | Passed | Passed |
| TC31 | Verify password visibility toggle | Automated | Passed | Passed |
| TC32 | Verify mandatory password validation | Automated | Passed | Passed |
| TC33 | Verify captcha field display | Automated | Passed | Passed |
| TC34 | Verify captcha generation | Automated | Failed | Failed |
| TC35 | Verify captcha refresh functionality | Automated | Passed | Passed |
| TC36 | Verify valid captcha submission | Semi-automated | Blocked | Blocked |
| TC37 | Verify invalid captcha validation | Automated | Passed | Passed |
| TC38 | Verify login button display | Automated | Passed | Passed |
| TC39 | Verify login with valid credentials | Semi-automated | Blocked | Blocked |
| TC40 | Verify login with invalid credentials | Semi-automated | Blocked | Blocked |
| TC41 | Verify submission without data | Automated | Passed | Passed |

## Defects and observations

- VL-001: Required Hotelier and Travel Agent tabs are absent; affects TC21, TC22 and TC23. Workbook/staging discrepancy.
- VL-002: Initial CAPTCHA can remain empty for at least 10 seconds; TC34. Refresh recovers the display and changes it on a subsequent click (TC35).
- OBS-001: Repeated console error: Cannot read properties of null (reading classList). Recorded without assuming its root cause.
- OBS-002: Homepage hero request aborts and loremflickr resource blocking. These are retained diagnostics, not additional failures of unrelated field-display expectations.
- Expected HTTP 400 responses accompanying required-field validation are recorded, not classified as unexpected defects.

## Limitations and provenance

TC36, TC39 and TC40 require process environment credentials and explicit human CAPTCHA confirmation. A CAPTCHA rejection does not prove invalid-credential handling. No successful authentication is claimed for blocked cases. Test input values for email/mobile and disposable password input were chosen because workbook Test Data is empty; these do not identify a real test account.

TC35 first refreshes to establish its loaded-CAPTCHA precondition, then verifies another refresh changes rendered pixels. TC34 separately verifies initial generation without recovery. No CAPTCHA value is read, decoded or solved.

Manual exploration initially assumed native required-field focus; the observed server-side message was subsequently checked against the workbook expectation. All manual attempts are retained in all_manual_attempts.json; manual_results.json contains the reviewed latest outcomes.

Real credential entry is excluded from traces and videos. Attended failures retain only the anonymous pre-credential trace, a fully masked screenshot, sanitized diagnostics and safe observations. Stable-case traces can contain disposable input, never environment passwords.

## Commands

```powershell
.\venv\Scripts\python.exe scripts/import_visitor_login_cases.py
.\venv\Scripts\python.exe -m pytest tests/test_visitor_login.py::test_workbook_visitor_login --collect-only -q
.\venv\Scripts\python.exe scripts/run_visitor_login.py
.\venv\Scripts\python.exe scripts/verify_allure.py
.\venv\Scripts\python.exe scripts/report.py generate
.\venv\Scripts\python.exe scripts/report.py open
```
