"""Summarize actual pytest attempts and compare by preserved manual case ID."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    latest = {}
    for path in (ROOT/'test-results/python').glob('events-*.jsonl'):
        for line in path.read_text(encoding='utf-8').splitlines():
            r = json.loads(line)
            key = r['name']
            rank = (r['attempt'], {'setup':0,'call':1,'teardown':2}[r['phase']])
            if key not in latest or rank >= latest[key][0]:
                latest[key] = (rank,r)
    tests = []
    for _,r in latest.values():
        r['blocked'] = r['outcome'] == 'skipped' and 'BLOCKED:' in r['error']
        r['category'] = 'None'
        if r['blocked']:
            r['category'] = 'Environment / manual prerequisite'
        elif r['outcome'] == 'failed':
            text = r['error']
            if any(s in text for s in ('ERR_CERT','ERR_NETWORK_ACCESS_DENIED','Executable doesn\'t exist','BrowserType.launch','browserType.launch')):
                r['category'] = 'Environment defect'
            elif any(s in text for s in ('AttributeError','TypeError:','NameError','fixture','No migrated implementation','strict mode violation')):
                r['category'] = 'Automation defect (needs review)'
            elif r['name'].split()[0] in ('NAV-055','NAV-071','NAV-072','NAV-073','NAV-074','NAV-075'):
                r['category'] = 'External destination / environment defect'
            else:
                r['category'] = 'Product assertion failure (review attached evidence)'
        tests.append(r)
    tests.sort(key=lambda r:r['name'])
    summary = {'total':len(tests),'passed':sum(r['outcome']=='passed' for r in tests),'failed':sum(r['outcome']=='failed' for r in tests),'skipped':sum(r['outcome']=='skipped' for r in tests),'blocked':sum(r['blocked'] for r in tests),'countNote':'Blocked is a subset of pytest/Allure skipped, not an additional test.','tests':tests}
    old_path = ROOT/'migration/javascript-outcomes.json'
    old = json.loads(old_path.read_text(encoding='utf-8-sig')) if old_path.exists() else {}
    previous = {r['name'].split()[0]:r for r in old.get('tests',[])}
    comparisons = []
    for r in tests:
        prior = previous.get(r['name'].split()[0])
        old_status = {'expected':'passed','flaky':'passed','unexpected':'failed','skipped':'skipped'}.get(prior['status']) if prior else 'New case'
        comparisons.append({'name':r['name'],'javascript':old_status,'python':r['outcome'],'category':r['category']})
    summary['comparison'] = comparisons
    provenance = ROOT/'test-results/merge-provenance.json'
    if provenance.exists():
        summary['provenance'] = json.loads(provenance.read_text(encoding='utf-8'))
    out = ROOT/'test-results'
    out.mkdir(exist_ok=True)
    (out/'python-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    text = f"# Python execution\n\nTotal: {summary['total']} | Passed: {summary['passed']} | Failed: {summary['failed']} | Skipped: {summary['skipped']} | Blocked: {summary['blocked']} (subset of skipped).\n\nAll counts come from actual pytest reports; retries do not increase the case count.\n\n## Failed or blocked tests\n\n"
    text += '\n'.join(f"- {r['name']}: {r['outcome']} — {r['category']}" for r in tests if r['outcome']!='passed')
    text += '\n\n## JavaScript / Python comparison\n\n| Test | JavaScript | Python | Classification |\n|---|---|---|---|\n'
    text += '\n'.join(f"| {r['name']} | {r['javascript']} | {r['python']} | {r['category']} |" for r in comparisons)
    (out/'python-summary.md').write_text(text+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('tests','comparison')},indent=2))

if __name__ == '__main__':
    main()
