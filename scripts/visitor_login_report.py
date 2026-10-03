"""Report current Visitor Login evidence without importing workbook outcomes."""
from collections import Counter
import json
import re
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'manual_test_cases/visitor_login_20261003'

def excel_value(value):
    if isinstance(value,(dict,list)):
        value=json.dumps(value,ensure_ascii=False)
    if isinstance(value,str):
        value=re.sub(r'\x1b\[[0-9;]*m','',value)
        value=ILLEGAL_CHARACTERS_RE.sub('',value)
        if len(value)>32000:
            value=value[:31900]+' [truncated for Excel; complete evidence in JSON/Allure]'
    return value

def main():
    cases = json.loads((ROOT/'data/visitor_login_data.json').read_text(encoding='utf-8'))['cases']
    manual = json.loads((OUT/'manual_results.json').read_text(encoding='utf-8'))
    automated=[]
    for c in cases:
        path=ROOT/'test-results/visitor-login'/f"{c['Test Case ID']}.json"
        automated.append(json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'id':c['Test Case ID'],'status':'Not Executed','expected_result':c['Expected Result'],'actual':'No fresh pytest record','automation':c['automation']})
    counts = {phase:dict(Counter(r['status'] for r in rows)) for phase,rows in [('manual',manual),('pytest',automated)]}
    summary={'selected':26,'automated':23,'semi_automated':3,'manual_only':0,'counts':counts,'tests':automated}
    (OUT/'execution_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    text='# Visitor Login TC16–TC41 execution\n\nSpecification: Test_Cases worksheet; historical outcomes ignored.\n\nSelected: 26; fully automated: 23; semi-automated: 3; manual-only: 0.\n\n'
    for phase,status in counts.items():
        text+=f"{phase}: "+', '.join(f'{s}: {status.get(s,0)}' for s in ['Passed','Failed','Blocked','Not Executed'])+'.\n\n'
    text+='| ID | Scenario | Approach | MCP manual | Fresh pytest |\n|---|---|---|---|---|\n'
    prior={r['id']:r for r in manual}
    for c,r in zip(cases,automated):
        text+=f"| {r['id']} | {c['Test Case Description']} | {c['automation']} | {prior[r['id']]['status']} | {r['status']} |\n"
    text+='\n## Defects and observations\n\n- VL-001: Required Hotelier and Travel Agent tabs are absent; affects TC21, TC22 and TC23. Workbook/staging discrepancy.\n- VL-002: Initial CAPTCHA can remain empty for at least 10 seconds; TC34. Refresh recovers the display and changes it on a subsequent click (TC35).\n- OBS-001: Repeated console error: Cannot read properties of null (reading classList). Recorded without assuming its root cause.\n- OBS-002: Homepage hero request aborts and loremflickr resource blocking. These are retained diagnostics, not additional failures of unrelated field-display expectations.\n- Expected HTTP 400 responses accompanying required-field validation are recorded, not classified as unexpected defects.\n'
    text+='\n## Limitations and provenance\n\nTC36, TC39 and TC40 require process environment credentials and explicit human CAPTCHA confirmation. A CAPTCHA rejection does not prove invalid-credential handling. No successful authentication is claimed for blocked cases. Test input values for email/mobile and disposable password input were chosen because workbook Test Data is empty; these do not identify a real test account.\n\nTC35 first refreshes to establish its loaded-CAPTCHA precondition, then verifies another refresh changes rendered pixels. TC34 separately verifies initial generation without recovery. No CAPTCHA value is read, decoded or solved.\n\nManual exploration initially assumed native required-field focus; the observed server-side message was subsequently checked against the workbook expectation. All manual attempts are retained in all_manual_attempts.json; manual_results.json contains the reviewed latest outcomes.\n\nReal credential entry is excluded from traces and videos. Attended failures retain only the anonymous pre-credential trace, a fully masked screenshot, sanitized diagnostics and safe observations. Stable-case traces can contain disposable input, never environment passwords.\n'
    text+='\n## Commands\n\n```powershell\n.\\venv\\Scripts\\python.exe scripts/import_visitor_login_cases.py\n.\\venv\\Scripts\\python.exe -m pytest tests/test_visitor_login.py::test_workbook_visitor_login --collect-only -q\n.\\venv\\Scripts\\python.exe scripts/run_visitor_login.py\n.\\venv\\Scripts\\python.exe scripts/verify_allure.py\n.\\venv\\Scripts\\python.exe scripts/report.py generate\n.\\venv\\Scripts\\python.exe scripts/report.py open\n```\n'
    (OUT/'summary.md').write_text(text,encoding='utf-8')
    book=Workbook();book.remove(book.active)
    fields=['id','status','actual','expected_result','duration_seconds','tested_url','screenshot','console_errors','failed_network_requests','defect_description']
    for name,rows in [('MCP Manual',manual),('Python Execution',automated)]:
        sheet=book.create_sheet(name);sheet.append(fields)
        for r in rows:
            sheet.append([excel_value(r.get(f)) for f in fields])
        sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
        for cell in sheet[1]:cell.font=Font(bold=True)
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width=40
            for cell in col:cell.alignment=Alignment(wrap_text=True,vertical='top')
    book.save(OUT/'visitor_login_execution.xlsx')
    print(json.dumps({k:v for k,v in summary.items() if k!='tests'},indent=2))

if __name__=='__main__':
    main()
