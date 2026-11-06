# TSP Phase 2 resumed manual inspection

Login: **Pass**. Fresh visible UAT session, manual CAPTCHA and explicit user confirmation, one Login click. Authenticated TSP Dashboard verified.

Apply Form: **Blocked**. The account already has an application under process. The visible message permits a new application only after rejection or when renewal is due. Application identifier omitted. This is an eligibility/prerequisite blocker, not a confirmed form defect.

| Order | Actual section name | Status |
|---|---|---|
| 1 | Application Type | Blocked |
| 2 | Applicant Details | Blocked |
| 3 | Office Details | Blocked |
| 4 | HR & Certification | Blocked |
| 5 | Transport Details | Blocked |
| 6 | Documents | Blocked |
| 7 | Declaration | Blocked |
| 8 | Preview & Submit | Blocked |

Section names were observed in the earlier visible eight-step navigation. During this resumed inspection the entire form is hidden. Fields, constraints, dropdowns, validation, backward/forward persistence and section layouts were not tested. No hidden sections were revealed or bypassed.

Evidence: application-access-blocked.png (masked identifiers and account details); tsp_test_inventory.json. Current console/network diagnostics were not captured before navigation, so absence of errors is not asserted.

No drafts saved, documents uploaded, applications submitted, or approval/rejection workflows triggered. No pytest, automation development, shared configuration changes or Allure generation. Only this dedicated manual inventory and safe screenshot were created.

Required prerequisite: an authorized TSP account eligible to start a new application, or an existing application state that legitimately allows read-only inspection. Do not reject or modify the existing application solely to bypass this restriction without separate authorization.
