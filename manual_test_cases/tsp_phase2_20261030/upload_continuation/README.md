# Authorized PDF upload continuation

The existing authenticated UAT session was resumed. The user authorized test PDFs from `test_data/PDF files`; saving drafts was already authorized. Final submission remains excluded.

Five document rows show Uploaded after an explicit Save Draft: incorporation (test1.pdf), PAN (test2.pdf), GST (test2.pdf), brochure (test3.pdf), vehicle documents (test3.pdf). These are test fixtures only. Initial positional file-input selection shifted when controls re-rendered and attached two files to additional rows; required rows were then targeted explicitly. This execution mapping issue is recorded in inventory.json, not as an application defect.

Documents progression is now unblocked. Declaration rejected an unchecked agreement with “Please accept the declaration.” Checking the agreement allowed Preview & Submit, and the selection survived backward navigation. All seven preview Edit buttons were executed and opened their respective sections; preview was restored each time.

All eight sections have now been opened across this phase. Coverage remains partial; the earlier two blocked sections are now inspected. Existing accessibility findings remain. No new defect was conclusively established in this continuation.

The 1.1 MB supporting-PDF selection left its row Pending Upload; no clear validation message was captured. This check is inconclusive, not Passed. File format/content validation, exact size boundaries, and final submission were not verified.

Final state: Preview & Submit, application completion 88%, five uploaded rows, upload progress 45%. Final confirmation remains unchecked. Submit Application was never clicked. No pytest, automation development or Allure generation occurred.

Evidence:
- documents-uploaded.png
- declaration-validation.png
- preview.png
- observations.json — captured UI observations
- inventory.json — fresh checks, actual results, file mapping and limitations

Checklist: five Passed, two Not Tested (one inconclusive size-feedback check and one intentionally excluded submission); no Failed or Blocked checks in this continuation. These counts are checks, not full-section certification.

Only the new manual evidence/inventory files were created, plus a continuation link in the parent README. Existing source, tests, fixtures, dependencies, secrets and shared configuration remain unchanged. Draft and test files remain in UAT.
