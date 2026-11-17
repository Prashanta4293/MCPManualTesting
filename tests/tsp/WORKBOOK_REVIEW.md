# Workbook-based TSP suite — implementation review, 2026-11-16

The current workbook contains one worksheet, `TSP Test Cases`, with 214 records.
All 32 columns, including recommendations, original data and review findings,
were inspected. The previously described other worksheets are not present in the
current file. The workbook was not modified by this implementation.

## Scope and classification

`data/tsp_workbook_automation.json` records an individual classification, original
ID, section, scenario type, source review status, exact clarification reason,
reuse candidates, missing requirement, side-effect risk, authorization requirement
and proposed pytest node for every row. Overlap IDs remain separate.

| Primary classification | Cases |
| --- | ---: |
| READY FOR IMPLEMENTATION REVIEW | 3 |
| REQUIRES CLARIFICATION | 112 |
| REQUIRES TEST DATA | 5 |
| REQUIRES FIXTURE / LOCATOR | 43 |
| REQUIRES EXPLICIT MUTATION AUTHORIZATION | 51 |
| UNSUPPORTED / DO NOT AUTOMATE | 0 |

These categories are exclusive for counting, not an assertion that each case has
only one prerequisite. Clarification takes precedence; other safety restrictions
still apply. No final-submission case is authorized by this classification.

## Implemented assertions, not runnable end-to-end tests

- `TSPDoc-005`: exactly the View/Upload buttons on document rows 1, 3, 5, 6, 7, 8;
  no Not Applicable control or other button accepted.
- `TSPDoc-006`: exactly View/Upload/Not Applicable on rows 2, 4, 9, 10.
- `TSPPrev-002`: exact public Preview banner wording from the workbook.

The document row scope reuses `.doc-item` and
`button[onclick="viewDoc(N)"]` from `TspApplicationPage.documents()`; the handler
is never invoked. Button accessible names are specified by the workbook and have
not been runtime verified. The Preview locator uses workbook-provided exact text
inside the existing `#stepContent` scope. `TspApplicationPage.at()` is the only
page method intended for reuse by these assertions: it checks URL and heading.

`prepared_readonly_form()` deliberately skips before requesting a browser fixture.
The current `tsp_session` launches a new browser, while preparing Documents or
Preview requires navigation/persistence whose safe setup is not established.
There is no environment override or silent manual-navigation workaround. A
separately reviewed read-only fixture must establish authorized ownership and
safe access/state, preserve fresh-account/CAPTCHA/CONFIRM checks and initialization
gates, and avoid mutating existing drafts. Thus there are **3 partial assertion
implementations, 0 runtime-ready cases**, not 3 completed UI tests.

The other 211 cases have no UI implementation: each produces an explicit BLOCKED
skip with its classification reason if invoked. All 112 clarification reasons are
retained exactly. No empty body can return PASS. Test IDs appear in pytest nodes
and Allure ID/title/section metadata. No raw source test data, DOM, screenshots,
URLs or Playwright error text are attached.

## Preserved code and safety

The old `TestTSPApplicationFlow` implementation remains in the target file with
`__test__ = False`; its obsolete IDs are not collected. The positive E2E file,
shared page object, fixtures, configuration and old sequential support/data remain
unchanged. Do not run the legacy flow as a workaround: it is not mapped to this
workbook. The current page object's `require_verified_upload_contract()` returns
without blocking; none of its upload, staff, vehicle, progression or save methods
are used by the new suite.

The workbook SHA-256 is pinned in the classification manifest. A changed workbook
stops collection until the mapping is reviewed again; stale expectations are not
silently executed. Legacy runtime ledger/workbook writers are not called. No
workbook status or Allure runtime report was changed/generated in this task.

## Collection verification

```powershell
$env:PYTEST_ADDOPTS = ''
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
.\venv\Scripts\python.exe -m pytest --collect-only --confcutdir=tests/tsp tests/tsp/test_tsp_mcp_application.py -o addopts= -p no:cacheprovider -q
```

This process-local configuration excludes root/legacy collection hooks and
automatic plugins, avoids cache/bytecode writes, and performs no fixture setup.
It is a collection command, not a recommendation for browser execution. Imports
and syntax succeeded. Programmatic inspection verified 214 unique pytest nodes,
214 exact workbook IDs, matching proposed class mappings and no legacy flow node.
Section totals: 34 / 26 / 24 / 24 / 25 / 26 / 15 / 40.

No browser tests were executed; no application was opened, modified or submitted.
