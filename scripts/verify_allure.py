import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    problems = []
    results = [json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'allure-results').glob('*-result.json')]
    fixtures = {}
    for container in (ROOT/'allure-results').glob('*-container.json'):
        c = json.loads(container.read_text(encoding='utf-8'))
        for child in c.get('children',[]):
            fixtures.setdefault(child,[]).extend(c.get('befores',[]) + c.get('afters',[]))
    for r in results:
        attachments = []
        def walk(node):
            attachments.extend(node.get('attachments',[]))
            for step in node.get('steps',[]):
                walk(step)
        walk(r)
        # pytest stores fixture attachments in separate containers. Include matching child containers.
        for node in fixtures.get(r['uuid'],[]):
            walk(node)
        for label in ('suite','feature','story','severity'):
            if not any(l['name']==label for l in r.get('labels',[])):
                problems.append(f"{r['name']}: missing {label}")
        if not r.get('description'):
            problems.append(f"{r['name']}: missing description")
        expected = ['Expected result','Actual result','Console errors','Network errors']
        if r['status']!='skipped':
            expected.append('Tested URL')
        for name in expected:
            if not any(a['name']==name for a in attachments):
                problems.append(f"{r['name']}: missing {name}")
        for a in attachments:
            if not (ROOT/'allure-results'/a['source']).exists():
                problems.append(f"{r['name']}: missing attachment file {a['source']}")
        if r['status'] in ('failed','broken'):
            types = ['image/png'] if r['name'].startswith('VISITOR-LOGIN') else ['image/png','video/webm']
            for kind in types:
                if not any(a['type']==kind for a in attachments):
                    problems.append(f"{r['name']}: missing {kind}")
    print(json.dumps({'attemptsChecked':len(results),'problems':problems},indent=2))
    return bool(problems)

if __name__ == '__main__':
    raise SystemExit(main())
