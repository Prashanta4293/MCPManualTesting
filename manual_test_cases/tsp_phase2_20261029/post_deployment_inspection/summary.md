# TSP manual inspection after deployment

Fresh login and Apply Form access: **Pass**. One login click after human CAPTCHA confirmation. Exact UAT entry `/en/home`; form `/en/tsp-registration-form`.

| Section | Status | Scope |
|---|---|---|
| Application Type | Fail | Partially inspected; accessibility defects; saving-dependent validation not tested |
| Applicant Details | Blocked | Pending; section link does not advance without completing the saving flow |
| Office Details | Blocked | Pending; section link does not advance without completing the saving flow |
| HR & Certification | Blocked | Pending; section link does not advance without completing the saving flow |
| Transport Details | Blocked | Pending; section link does not advance without completing the saving flow |
| Documents | Blocked | Pending; section link does not advance without completing the saving flow |
| Declaration | Blocked | Pending; section link does not advance without completing the saving flow |
| Preview & Submit | Blocked | Pending; section link does not advance without completing the saving flow |

## Findings

- Both application categories work, as does TSP type selection. No conditional fields appeared when switching categories.
- Visible required TSP dropdown lacks an associated programmatic label and native/ARIA required state. This does not establish whether server-side required validation works.
- Unavailable steps use a disabled CSS class without disabled/aria-disabled semantics and remain keyboard-focusable. Clicking each leaves Step 1 active without explanation.
- Desktop screenshot shows readable, aligned controls without horizontal overflow at 1366x900.
- Progress remains 0%. The only forward control is **Save & Continue**. It was not clicked under the no-saving restriction.
- All 11 dropdown options are recorded in inventory.json.

## Limits and evidence

No drafts saved, documents uploaded, application submitted, or workflow triggered. No pytest, automation development, source/configuration change or Allure generation. Cross-section persistence and validation are not tested. No hidden sections were exposed or bypassed. Unsaved local selections remain Start-Up / Green Shoot TSP and Tour Operator.

Evidence: section-1.png; navigation_observations.json; inventory.json. Console/network monitoring during the selected interactions found no errors; earlier navigation was outside that capture window.

Further section inspection requires a legitimate non-saving preview/navigation path or a separately authorized change to the current no-saving restriction.
