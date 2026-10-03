# TC39 diagnosis and verification — 2026-10-03

Confirmed root cause: the post-login check attempted to click the homepage-only `#otUserIconBtn` after successful authentication redirected to `/visitor-landing`. The dashboard did not expose that control, so the click timed out. The expected result remains successful Visitor login.

## Diagnostic rerun evidence

- Login button clicked: true, after explicit human CAPTCHA confirmation through terminal input.
- Authentication API `/o/user-login/login`: HTTP 200.
- Visitor landing navigation: HTTP 200, after HTTP 302 redirects.
- Liferay signed-in state: true.
- Login popup visible: false.
- Homepage profile control visible: false.
- Failure stage: Open header profile control.
- Error page / 404 / 500 indicators: false in the authenticated session.

| Candidate cause | Conclusion |
|---|---|
| Invalid or expired CAPTCHA | Ruled out for the diagnostic rerun: authentication completed. |
| Invalid credentials | Ruled out: the session was signed in. |
| Login button not submitted | Ruled out by the click and authentication response checkpoints. |
| Authentication API failure | Ruled out: HTTP 200 and signed-in state. |
| Timeout | Immediate failure mechanism was waiting for the wrong profile control. |
| Incorrect post-login URL or locator assertion | Confirmed locator defect; the authenticated URL was correct. |

An anonymous request to `/visitor-landing` returned 404, but authenticated navigation returned 200. The anonymous response was not treated as proof of a broken dashboard. The observed image 404 and aborted/blocked homepage or analytics requests were not the cause of the failed assertion. Console content remained suppressed for credential privacy.

## Fix and verification

Replaced the homepage profile-icon/logout check with the expected Visitor dashboard URL, Liferay signed-in state, visible `body.signed-in` main content and absence of the error-page wrapper. The login popup must also be hidden. No authentication or CAPTCHA handling expectation was relaxed.

Verification: **one passed, 25 deselected**, headed Chromium, no pytest-xdist, `-s`, no automatic retry. The tester entered a fresh CAPTCHA and explicitly confirmed before terminal `CONFIRM` was sent.

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_visitor_login.py::test_workbook_visitor_login -m 'visitor_login and positive and manual_captcha' -k TC39 --headed -s --manual-login --reruns 0 --visitor-evidence-dir test-results/attended-visitor
.\venv\Scripts\python.exe scripts/report.py generate
```

DEBUG/PWDEBUG were removed only from the test subprocess environment. No `.env` modification was made. Credentials were not printed or attached. Trace/video remained disabled; a fully masked screenshot was captured only after authenticated dashboard verification. Text evidence was checked for credential disclosure with no matches.

## Files changed for diagnosis

- `pages/visitor_login_page.py`: sanitized diagnostic checkpoints and corrected dashboard verification.
- `tests/test_visitor_login.py`: attach safe state diagnostics when an attended assertion fails.
- This diagnosis document.

The failed diagnostic run is preserved under `run-history/python-20261003T104630870929Z/`. Current verified results are under `test-results/attended-visitor/TC39.json`, `allure-results/` and `allure-report/`.
