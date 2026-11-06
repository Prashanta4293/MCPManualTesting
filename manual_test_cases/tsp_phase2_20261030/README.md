# TSP manual inspection — 30 October 2026

Latest: [Authorized upload continuation](upload_continuation/README.md) supersedes the Documents blocker and final state below. The following is the earlier pre-upload execution record.

Entry: https://apptourlfr-stg.estpl.net/en/home  
Tested form: https://apptourlfr-stg.estpl.net/en/tsp-registration-form

Login passed after one explicitly confirmed login click. User authorized saving test draft data. No documents were uploaded and no application was submitted. No pytest, automation development or Allure generation occurred.

| Section | Status | Coverage |
|---|---|---|
| Application Type | Pass | Empty required validation and selected category/type progression |
| Applicant Details | Fail | Tested required/format validation passes; accessibility semantics fail |
| Office Details | Pass | Required service and conditional office validation; No branch progression |
| HR & Certification | Pass | Required staff validation, one synthetic staff entry, certification toggle |
| Transport Details | Pass | Yes conditional fields, empty vehicle validation, No branch progression |
| Documents | Pass | Visible checklist and mandatory-upload gate only; no upload testing |
| Declaration | Blocked | Requires documents; contents not inspected |
| Preview & Submit | Blocked | Requires documents; contents not inspected |

Counts are section-level: 8 total, 5 pass within tested scope, 1 fail, 2 blocked. Pass does not imply exhaustive section coverage. Six sections were opened and partially inspected.

## Findings

1. Applicant controls lack associated HTML labels/aria-label; visually required fields lack native/ARIA required state. This does not imply application required validation is absent: tested required validation worked.
2. Unavailable step buttons use a disabled CSS class without native/ARIA disabled semantics; clicking them leaves the current section unchanged without explanation.

Potential stale staff validation text appeared immediately after adding the first staff member; it did not persist after navigation. Retained as an observation, not a confirmed persistent defect.

An unsaved website value survived step-link navigation between Applicant Details and Office Details. It was restored to blank afterward. Saved applicant name and staff entry also survived backward/forward navigation. Persistence across reload/new sessions was not tested.

Final UI: Documents, application completion 63%, zero files uploaded. Save & Continue is natively disabled with the tooltip “Upload all required documents to continue.” Declaration and Preview links do not advance. No disabled control was bypassed.

## Evidence and limits

- [Detailed inventory](inventory.json): per-section actual results, constraints, defects and limits.
- [Observed UI data](observations.json): field lists, dropdown options, conditional text, validation and navigation observations.
- section-1.png through section-6.png: form-only captures for inspected sections.
- step1-validation.png, step2-validation.png, step2-invalid-format.png, step3-validation.png, step4-validation.png, step4-staff.png, step5-validation.png, step6-required-documents.png: targeted evidence.

Evidence contains synthetic form data only, not login credentials or CAPTCHA. Console/network errors were not instrumented during this resumed inspection; absence of errors is not asserted. Numeric/file boundaries, full accessibility, mobile layout, uploads, declaration and submission are untested. Desktop checks found no horizontal overflow.

Only this evidence directory was created. Existing tests, fixtures, shared configuration, dependencies and .env were not changed. No cleanup or deletion of the approved draft data was performed.
