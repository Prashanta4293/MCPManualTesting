# Python migration verification ? 2026-10-01

The Python migration and user-approved cleanup are complete. The active project no longer contains the 13 approved JavaScript/package files or local node_modules. Backups, data, evidence, spreadsheets, reports, the virtual environment and global Allure/Node support were retained.

## Fresh post-cleanup Chromium execution

| Total | Passed | Failed | Skipped | Blocked (included in skipped) |
|---:|---:|---:|---:|---:|
| 100 | 71 | 28 | 1 | 1 |

The full post-cleanup run executed via Python pytest with two Chromium workers, taking 20m 53s with 28 retries. All 99 original cases match their recorded JavaScript outcomes. The new positive Visitor login remains skipped/blocked: it requires configured credentials and human CAPTCHA entry. Successful authenticated login remains unverified.

The initial artifact audit found missing screenshots on one attempt each of NAV-044 and NAV-049. A Chromium viewport screenshot fallback was added for full-page screenshot failures, without changing test assertions. Both cases were actually rerun, retained their failures, and all four fresh attempts passed the artifact audit. These actual targeted results replace those two cases in the combined report. The complete original post-cleanup run remains in run-history/python-20261001T052938715783Z. See ../test-results/merge-provenance.json.

## Verification

- Python collection after cleanup: 100 cases; zero missing original cases.
- Backup checksum errors: zero; approved removal paths remaining: zero.
- Final Allure audit: 128 attempt records checked, zero metadata or attachment problems.
- First-retry trace files: 28. Failure screenshots/videos, console/network diagnostics, expected/actual results and tested URLs retained.
- Historical manual Excel/Markdown generation previously verified under manual-report-check/, preserving original reports. These historical outputs do not represent fresh browser execution.
- Existing hotel evidence extraction verified without changing saved match data.
- Python tests and report utilities do not invoke the removed JavaScript test runner. HTML generation uses the retained global Allure CLI.

## Defects and limitations

The same 28 original cases still fail. See ../test-results/python-summary.md for every failed test name, provisional classification and baseline comparison, and Allure for evidence. Failure classifications are triage aids, not confirmed root causes. No assertions were weakened to pass these cases.

The positive login success assertion remains unverified until credentials and manual CAPTCHA participation are available. No CAPTCHA bypass is implemented. Original scope exclusions remain exclusions, not passes.

## Reports

- HTML: ../allure-report/index.html; serve using python scripts/report.py open.
- Raw results: ../allure-results/.
- Fresh execution summary and failed names: ../test-results/python-summary.md.
- Coverage and mapping: coverage.json and mapping.md.
- Approved removal record: removal-proposal.md and removal-manifest.json.

HTML generation succeeded and widget counts match: 100 total, 71 passed, 28 failed, one skipped, zero broken. Allure CLI analytics connections were sandbox-blocked; this did not prevent local report generation.
