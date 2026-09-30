import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    latest = {}
    for path in (ROOT/'allure-results').glob('*-result.json'):
        r = json.loads(path.read_text(encoding='utf-8'))
        if r['name'] not in latest or r.get('stop',0)>latest[r['name']].get('stop',0):
            latest[r['name']] = r
    for r in sorted(latest.values(),key=lambda r:r['name']):
        if r['status']!='passed':
            print(json.dumps({'name':r['name'],'status':r['status'],'error':r.get('statusDetails',{}).get('message','')[:1600]},ensure_ascii=False))
    print(json.dumps({'finishedCases':len(latest)}))
