## Eight-section sequential implementation - static review only

Entry point: `test_tsp_mcp_application.py::TestTSPApplicationFlow::test_tsp_sequential_flow`.
Section/scenario helpers: `tests/tsp/sequential_flow_support.py`.
Mapping: `data/tsp_sequential_scenarios.json` (69 stable records, including aliases).

All eight section methods now have ordered negative checks and guarded positive
completion. Existing positive POM methods are composed, not modified. Applicant
fill-only setup is separated from navigation to support one-invalid-field checks.
Unsupported cases are explicitly reported with their existing reason; a missing
business rule or status selector is never fabricated. A BLOCKED before-action
contract can allow continued inspection. A failure or uncertain state stops the flow.

**Not runtime ready:** VERIFIED_CONTRACTS is deliberately empty. It can be changed
only after reviewed source/UI evidence and explicit authorization, not via runtime
environment flags. Current fresh-account status is unverified. The test asks for
FRESH VERIFIED before requesting Playwright or opening any browser. Without it,
it stops. Even confirmation alone cannot bypass the initialization contract gate.
No complete eight-section success is claimed.

Implemented negative/passive helpers cover APP-001 (alias014),018,021,023,003,013,
026,031,037,008 (alias043),010 (aliases051/052),060. Remaining IDs are explicit
blocked requirements, not silent skips or stub passes. Exact empty/reset contracts
and business validity remain prerequisites even where assertion code exists.
Positive checkpoints POS-002..009 invoke guarded current POM functionality;
certificate/document uploads retain their existing hard blocker. Save Draft is
never introduced as a fallback and Final Submit is never activated.

### Attended execution command (prepared, NOT run in this implementation phase)

```powershell
$env:PYTEST_ADDOPTS = ''
.\venv\Scripts\python.exe -m pytest --confcutdir=tests/tsp tests/tsp/test_tsp_mcp_application.py::TestTSPApplicationFlow::test_tsp_sequential_flow -o addopts= -p no:cacheprovider -s --headed --tsp-attended --reruns 0 -n 0 --tb=short --alluredir=allure-results/tsp-sequential-REPLACE_WITH_UNIQUE_RUN_ID
```

One headed Chromium context is created only after preflight. A dynamically chosen
loopback CDP endpoint is printed and saved to the new run directory. MCP must attach
to that endpoint and verify it is the SAME browser before `MCP ATTACHED` confirmation.
For example, the MCP Playwright code tool can use its browser type's
`connectOverCDP(endpoint)` and inspect the resulting browser's context/page; do not
use MCP's separate default tab for UAT. Do not close the shared browser through MCP.
This bridge is implemented but NOT runtime verified; if attachment cannot be
established, stop rather than proceed with a second application session.

Existing login keeps CAPTCHA manual with terminal CONFIRM. Each section pauses
for read-only MCP inspection and `MCP INSPECTED`. Navigation requires a reviewed
contract and a section-specific `PROCEED SECTION` approval; no assumption that
Save & Continue is non-persistent. Existing upload/state blockers remain in force.

Runtime artifacts use a new timestamp/UUID directory under artifacts. Every
scenario has expected/actual/status/reason in Allure and the JSON ledger. UI counts
are tracked, not hard-coded. Aliases share a canonical result. Workbook updates
occur only during a future execution; current-run cells match the ledger and
previous outcomes are retained in remarks. Locked workbook leaves the ledger
authoritative and reports synchronization as blocked. Reporting errors prevent an
overall PASS. Safety gates appear as skipped Allure steps, never successful UI
executions. The ledger is finalized after bounded browser cleanup. Failure evidence
contains traceback frame chains and exception types, with messages, source lines,
locals and private paths suppressed; this is not an unredacted traceback.
No screenshots are captured: safe masking is not established. No black placeholder
is presented as visual proof. Console/runtime/network evidence uses counts only.
Bounded browser hold defaults to60seconds (maximum300); both closes are attempted.
No retries, parallel execution, Visitor tests or shared fixture changes.

The old positive/diagnostic material below is historical; current guarded source
has precedence over stale descriptions of unconditional saves or visual screenshots.

---

# Attended positive TSP application flow

## Current normal HR workflow: IITTM No (pending review/execution)

The normal staff flow now uploads the configured Qualification Certificate and retains the existing qualification-success verification gate. Only after that gate succeeds does it select No, assert No checked/Yes unchecked, and require the IITTM upload label, input and its immediate parent (if present) to be hidden. It never selects Yes or uploads an IITTM certificate. The input alone is insufficient visibility evidence because native file inputs are normally hidden even when their upload component is available.

Staff matching now requires an exact table cell name and a single unique record. Duplicate or unrelated rows block the operation. A matching existing record uses Edit/Save Staff Details; an empty list uses Add Staff Member. Counts are checked again before the action and afterward, and the result must display certification No and document N/A. Afterward the existing guarded Save & Continue action verifies Transport Details. Save & Continue may persist application data; staff add/edit and uploads may also persist data. The Documents section has a separate Save Draft checkpoint; final submission remains prohibited.

Qualification success remains BLOCKED/UNVERIFIED because its component/status selector is not established; therefore the current helper intentionally prevents No selection, staff add/save and progression until qualification is verified. No assertion is removed or bypassed. No runtime success is claimed. The optional two-checkpoint DOM diagnostic is unchanged and remains separate from this normal No workflow. Local TSP PDF preflight requires the IITTM file only in diagnostic mode; test data and shared/Visitor fixtures are unchanged.

## Temporary upload DOM diagnostic (opt-in; not yet executed)

The helper is `tests/tsp/upload_dom_diagnostic.py`. Its entry point is the environment-gated branch at the start of `test_tsp_all_fields_without_submission`, immediately after constructing the page object. It reuses `tsp_session` and `form.page`; it does not connect to a separate Chrome session. In normal execution, `office()` reaches Step 4 through its final `next_section('HR & Certification')`, then `staff()` selects and uploads files. Diagnostic mode deliberately bypasses that normal execution path because those actions are not authorized for a read-only diagnostic.

Only after explicit approval to execute the attended diagnostic:

```powershell
$env:TSP_UPLOAD_DOM_DIAGNOSTIC = "1"
.\venv\Scripts\python.exe -m pytest --confcutdir=tests/tsp tests/tsp/test_tsp_application.py -o addopts= -s --headed --tsp-attended --reruns 0 --alluredir=allure-results/tsp-upload-dom-diagnostic
Remove-Item Env:TSP_UPLOAD_DOM_DIAGNOSTIC
```

The existing fixture launches the headed Playwright browser for that approved run. Enter CAPTCHA in that browser and type CONFIRM at the existing login prompt. Manually navigate to an already accessible HR & Certification section with IITTM Yes already selected. Do not save, continue, submit, add staff, delete/replace documents or change other form values. If this state is inaccessible without prohibited actions, type BLOCKED; do not force access. Otherwise type READY to capture the sanitized baseline.

Checkpoint 1: if qualification is not already uploaded, manually choose the configured qualification PDF (default test_data/PDF files/test4.pdf). Wait for its Uploaded successfully status, then type CAPTURE. If upload needs Save Draft or cannot complete safely, type BLOCKED; available DOM for both components is attached and the diagnostic stops.

Checkpoint 2: if IITTM is not already uploaded, manually choose the configured IITTM PDF (default test_data/PDF files/test5.pdf). Wait for its Uploaded successfully status, then type CAPTURE. Use BLOCKED if unsafe/unavailable. Manual file selection may persist uploaded documents; it is the only permitted data-changing action in this diagnostic. The automation itself never uploads and cannot create an application record to unblock uploads.

At each capture, the helper verifies the exact UAT form URL and Step 4 heading, then reads both inputs and up to four ancestor levels, stopping after a shared file-input ancestor. It records a candidate only when one ancestor contains exactly one file input, a visible expected-filename match and a visible Uploaded successfully indicator, without observed pending/error/invalid/busy/draft-required indicators. This is evidence for review, not a production selector or assertion change. No save, navigation, checkbox, upload, staff-add or delete actions are issued by the helper.

Allure receives a sanitized baseline and separate `Checkpoint 1 Qualification Certificate DOM (sanitized)` / `Checkpoint 2 IITTM Certificate DOM (sanitized)` attachments: input attributes, structural paths, immediate-parent separation, filename-match booleans, success/pending/error/draft-blocker flags, uploader/parent visibility, radio checked states, candidate common ancestor and sanitized ancestor outerHTML. If checkpoint 1 blocks, checkpoint 2 is labelled not attempted and includes only the DOM available at that point. Text is retained only for known UI labels/status phrases; exact expected filenames become [EXPECTED_FILENAME], and values/all other text are redacted. Unknown IDs/classes use consistent redacted aliases; known input IDs and conservative generic classes/roles are retained. Aliases are not selectors. Structural paths refer only to that snapshot. Sanitization uses a detached document; live form values are unchanged. No screenshot or document content is captured. Required attributes alone do not prove conditional business validation.

The diagnostic deliberately ends as pytest Skipped: either both checkpoints captured for review, or BLOCKED with available evidence. Neither outcome is a positive-flow pass. Existing configured browser hold/cleanup still runs. A blank/inaccessible uploader, missing success indicator, ambiguous shared container or missing input after rerender is reported as Blocked rather than guessed. The production wait_for_upload implementation is unchanged. The two-checkpoint diagnostic has not been executed.

To disable: remove TSP_UPLOAD_DOM_DIAGNOSTIC from the shell (and from .env if you independently configured it there). To remove the temporary implementation after evidence collection: delete the environment-gated branch and its `import os` from `tests/tsp/test_tsp_application.py`, remove `tests/tsp/upload_dom_diagnostic.py`, and remove this documentation section. No Visitor test or shared fixture changes are needed. Existing upload handling remains unchanged.

This test uses the existing Python Playwright/pytest/Allure dependencies. It opens only `https://apptourlfr-stg.estpl.net/en/home`, uses TSP login, and attempts to fill all eight sections and upload the authorized PDFs. Navigation uses Save & Continue. Save Draft is permitted where explicitly required, particularly for document uploads. The current Documents method invokes its Save Draft checkpoint before iterating document rows, including for resumed drafts. Submit Application (Final Submit) remains prohibited. The final submission confirmation is intentionally unchecked. Reaching preview is not reported as success unless inspection and completed-form screenshot capture succeed.

## Save Draft action reporting

Each page-object instance starts with no Save Draft attempts (`not_attempted`). Each checkpoint records a fresh attempt: `attempted` before button checks, `clicked` only after Playwright's click returns, and `confirmed` only after the existing success-toast assertions pass. Any exception marks that attempt `failed` and is re-raised; completed-click and confirmation flags are retained independently. Repeated calls have separate records, so a previous confirmation cannot hide a later failed attempt.

The normal test attaches Actual result in `finally`, including completed, failed and skipped/blocked outcomes. Action confirmation is distinct from overall test completion. If the click itself raises, its delivery is unknown and reported as UNKNOWN, not NO. No toast text, application identifiers or credentials are included in the action record. Confirmation proves the expected UI notification was observed, not independent backend persistence. The opt-in DOM diagnostic remains unchanged and does not call Save Draft.

This reporting correction does not change application actions, upload handling, manual CAPTCHA or fixture lifecycle. Historical reports are unchanged; their prior hard-coded no-Save-Draft claim is not reliable action evidence.

## Persistence findings and completion limit

The saved MCP observations in `manual_test_cases/tsp_phase2_20261030/upload_continuation/observations.json` and `inventory.json` show that earlier Save & Continue actions advanced sections, but selected files displayed **Save Draft To Upload** and **Please save the draft first**. Explicit Save Draft then triggered actual uploads. The current Documents workflow performs an explicit Save Draft checkpoint before uploads. This is not an automatic fallback from an upload error: the existing upload blocker still stops the workflow if a Save Draft-required message is encountered. Completion is not guaranteed.

Available evidence does not establish whether Save & Continue persists some fields, nor whether it creates/updates a backend draft or another status. No application handler source or request/response evidence proving that status was available in this review. Treat Save & Continue as potentially persistent; it is NOT a promise of local-only navigation. Verifying exact backend status requires a separately reviewed UAT/network inspection, not an assumption from the button label or completion percentage.

Actions with persistence implications:

- Save & Continue: may save application fields/progress; backend behavior/status unverified.
- Selecting staff-certificate and checklist files: can upload and persist documents when an application record exists. Prior checklist uploads were observed as Uploaded after explicit draft creation.
- Add Staff Member / Save Staff Details and Add Vehicle: change form data; immediate versus deferred server persistence is unverified.
- Text, selection and declaration edits: update the UI; any background autosave is unverified.
- Save Draft: the explicit Documents checkpoint may persist application data. Allure records each attempt, completed click and observed success notification.
- Submit Application / Final Submit: prohibited; no submission action is invoked.

No status such as Submitted, Approved or persisted Draft is inferred from reaching preview.

## Run from the project root

```powershell
.\venv\Scripts\python.exe -m pytest --confcutdir=tests/tsp tests/tsp/test_tsp_application.py -o addopts= -s --headed --tsp-attended --reruns 0 --alluredir=allure-results/tsp-positive
```

Use a dedicated TSP test account with no submitted application. An existing synthetic `UAT TEST ONLY -` draft may be resumed. Do not run concurrently or with xdist. The script skips without explicit `--tsp-attended`, terminal input (`-s`), or configured TSP credentials. Set `TSP_EMAIL` and `TSP_PASSWORD` privately in the root `.env`; the script never reads `.env.example`. Disable DEBUG/PWDEBUG.

At the terminal prompt, enter the CAPTCHA in the visible browser and type `CONFIRM` in the terminal. Never type CAPTCHA text or credentials in the terminal. Only one login click is made. A failed login ends the test; reruns are disabled.

After successful preview inspection/capture, failure, or a blocker, automation stops and the browser stays open. Close all test-browser windows manually when inspection is complete. Pytest teardown and final report completion wait for that closure; the process must remain running to keep the browser alive. No terminal ENTER is needed to release the browser hold.

`--confcutdir=tests/tsp` isolates this run from the legacy Visitor-specific fixtures and collection hook that writes migration files. Shared fixtures/settings are unchanged. The local fixture also overrides the legacy autouse audit if the test is discovered during ordinary project collection; the new test is opt-in and skips by default.

## Data and coverage

Edit `data/tsp_application_data.json` for synthetic form values and PDF paths. Do not put credentials there. Defaults populate:

1. Experienced TSP / Tourist Transport Operator.
2. All applicant fields, Others constitution detail, and a separate complete communication address; mobile, email, website, PAN, GSTIN, incorporation number, establishment date.
3. Experience, capital, turnover, all geographic areas and service checkboxes, Other Services description, office Yes, full address/area and Other Ownership detail.
4. One staff member with qualification/designation and verified qualification PDF, then IITTM No with the uploader hidden. No IITTM certificate upload. An exact, unique existing staff match is edited rather than duplicated; ambiguous or unrelated rows block the operation.
5. Transport Yes with vehicle type, registration, capacity and ownership. A matching existing vehicle is verified rather than duplicated.
6. All 11 checklist entries, including optional documents, using existing authorized PDFs. The last entry uses a PDF below 1 MB. A stable row-specific selector avoids the positional input-index issue observed manually.
7. Declaration accepted for this UAT test draft.
8. Preview values and absence of Pending/Not provided/Not Attached verified. Final submission confirmation remains unchecked; Submit Application is never invoked.

Mutually exclusive controls cannot all be selected simultaneously. One valid option is used per radio/select; conditional Yes/Other branches expose additional fields. Blank staff/vehicle composer controls after adding an entry are not missing saved data. The only intentionally unfilled final control is submission authorization.

Visible applicable text/select controls are checked for nonempty values. This catches unexpected new fields rather than silently skipping them. Synthetic PAN/GST/CIN values and sample PDFs are test fixtures, not verified government records; any stronger UAT validation failure must be investigated, not bypassed. Existing document rows must have the expected fixture filename or the test fails instead of replacing unknown attachments.

## Evidence and validation

Allure includes step metadata, expected/actual outcome and sanitized diagnostic counts. Screenshot policy is fail-closed: the entire form, including all inputs, applicant/staff/vehicle details, identification/contact data, displayed text and uploaded filenames, is masked opaque black using Playwright's native screenshot mask. There is no unmasked or partial-mask fallback and no assumption that existing records are synthetic. The former evidence_allowed flag is no longer used.

Before any screenshot attachment, Pillow verifies every captured pixel is opaque black. Only a metadata-free black image with the verified dimensions is attached; original browser bytes are never saved or attached. This privacy-only image intentionally does not show layout or values. Completed-preview DOM assertions remain required and run independently before capture. Success is recorded only after both preview inspection and required evidence verification. If prerequisites, masking or verification fail, no image is attached: evidence is Blocked. Required completion evidence then makes the test Blocked (pytest skipped); optional failure evidence does not replace the original failure.

Pillow is an optional verification dependency, not installed or added to shared requirements by this change. Offline inspection found `venv/Lib/site-packages/PIL/Image.py` absent. Until an approved verifier is available, screenshots are suppressed and completion evidence is Blocked. No login screenshot, video, trace, credential value, raw network body or console text is recorded. Browser session/storage is not exported.

## Upload and selection safety corrections

Offline readiness investigation (30 October 2026): neither requirements.txt nor requirements-lock.txt declares Pillow, and the project venv has no PIL/Image.py. The smallest proposed dependency-file change is to add `Pillow` to requirements.txt. This is a proposal only: no dependency file or environment was changed. After a separately approved installation/validation, record the actually validated version in requirements-lock.txt; no version is guessed here. Required screenshot evidence remains Blocked until the verifier is available and masking succeeds at runtime.

No application implementation source for handleFileSelect/toggleAreaOp or additional saved selected-button DOM was found in the local source/artifact search. In manual_test_cases/tsp_phase2_20261030/observations.json, step5attempt shows the qualification/IITTM controls and conditional uploader; step5.staffAdded shows `Not Attached`, certification `No`, and IITTM document `N/A`. Those records establish no staff-upload success state. Checklist Uploaded evidence cannot be substituted for staff success. Required missing evidence: each staff upload container's pending/uploading/success/blocker DOM, with the expected file associated with a server-confirmed completion signal.

The same observations file (step3) lists State, National and International but records no selected-state attributes or selected accessible names for National/International. Their selected-state assertions remain runtime-unverified. To verify them, obtain before/after accessible names and selected-button outerHTML for each control. The State icon evidence alone does not establish their implementation.

Final offline review: Save & Continue remains allowed solely through guarded section navigation. The current Documents method includes an explicit Save Draft checkpoint; final submission remains prohibited. The success path ends with eighth-section preview assertions and verified masked capture; inability to establish evidence or upload success prevents success. The existing browser hold keeps the Playwright fixture alive until manual closure. Visitor tests and shared fixtures were not modified. This investigation changes only this README and performs no pytest/browser/UAT/package-install actions. Full positive-flow UAT readiness remains Blocked by the missing image verifier and staff-success evidence; National/International selection is additionally runtime-unverified. Save & Continue persistence and backend application status remain unknown.

Every upload-dependent operation waits in a bounded 90-second poll. Visible “Save Draft To Upload” / “Please save the draft first” messages take precedence, including delayed messages and a final deadline recheck. The workflow immediately records a sanitized Blocked reason and stops, without an additional Save Draft fallback, alternate save API or dependent staff action. This blocker is separate from the explicit Documents Save Draft checkpoint; Documents also retains its existing conditional Retry Upload action.

Checklist success requires the exact expected filename and an exact `Uploaded` or `- Uploaded` line in the corresponding `.doc-item`. A filename alone, “Not Uploaded”, a progress indicator or another document's success is insufficient. This state is supported by saved MCP upload observations. Unknown states at the deadline are Blocked, not claimed as success or reported as a generic assertion timeout.

Saved evidence does not establish a row/container-specific completed-upload state for the qualification certificate. Its wait intentionally cannot return success yet: it detects any delayed draft blocker, otherwise stops as Blocked at the deadline. No selection, Add/Save Staff Details and progression are not reached after unresolved qualification verification. The normal workflow no longer uploads IITTM. To enable verified qualification success, obtain its container DOM for pending, uploading, successful and draft-required states (or an approved equivalent server-confirmed signal); bind the wait to that container and expected filename. Do not infer success from the file chooser value or filename preview.

Office selection now uses the observed check-icon accessible name (`U+F00C` followed by the area name), not `active`, `aria-pressed`, or an assumed checked property. The existing failure accessibility snapshot (`button "\uf00c State"`) and `allure-results/15c19974-fc12-4ede-882f-afeff080a91c-attachment.png` establish State's visual selected indicator. The generic locator tolerates the icon; a separate exact selected-name locator must resolve to one visible button after selection. This verifies the displayed selection only, not backend persistence. National/International must exhibit the same indicator during a controlled run or the assertion fails; they are not silently accepted.

The revised full flow is not ready to complete a controlled UAT run until staff success-state evidence and screenshot verification availability are resolved. No tests, browser launch, login, UAT access, uploads, drafts or submission were executed to make these code-only changes. Manual CAPTCHA, Save & Continue navigation and the browser inspection hold are unchanged.

Safe collection (does not execute tests or invoke the legacy collection writer):

```powershell
.\venv\Scripts\python.exe -m pytest --confcutdir=tests/tsp tests/tsp/test_tsp_application.py --collect-only -q -o addopts= -p no:cacheprovider
```

This workflow revision is reviewed using offline syntax and safety checks only. No pytest collection, test execution, browser launch or UAT access was performed for the revision. Previous checks/results do not establish that this revised end-to-end flow passes. Optional/conditional branches and backend persistence still require controlled verification after review.

After an attended execution, use the existing Allure installation:

```powershell
allure generate allure-results/tsp-positive --clean -o allure-report/tsp-positive
allure open allure-report/tsp-positive
```

Use a fresh results subdirectory for each run to avoid combining historical results. Test data and uploaded draft files remain in UAT after execution; the script does not submit or delete the draft.
