"""Explicitly merge real targeted pytest results with an archived Python run."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    base = (ROOT / sys.argv[1]).resolve()
    if not base.is_relative_to(ROOT/'run-history'):
        raise SystemExit('Source must be inside run-history')
    selected = {json.loads(p.read_text(encoding='utf-8'))['name'] for p in (ROOT/'allure-results').glob('*-result.json')}
    uuids = set()
    for p in (base/'allure-results').glob('*-result.json'):
        r = json.loads(p.read_text(encoding='utf-8'))
        if r['name'] not in selected:
            shutil.copy2(p,ROOT/'allure-results'/p.name)
            uuids.add(r['uuid'])
    # Preserve attachments and fixture containers. They carry no synthesized outcomes.
    for p in (base/'allure-results').iterdir():
        if p.name.endswith('-result.json'):
            continue
        if p.name.endswith('-container.json'):
            c = json.loads(p.read_text(encoding='utf-8'))
            c['children'] = [u for u in c.get('children',[]) if u in uuids]
            if c['children']:
                (ROOT/'allure-results'/p.name).write_text(json.dumps(c),encoding='utf-8')
        elif not (ROOT/'allure-results'/p.name).exists():
            shutil.copy2(p,ROOT/'allure-results'/p.name)
    with (ROOT/'test-results/python/events-retained.jsonl').open('w',encoding='utf-8') as out:
        for p in (base/'test-results/python').glob('events-*.jsonl'):
            for line in p.read_text(encoding='utf-8').splitlines():
                if json.loads(line)['name'] not in selected:
                    out.write(line+'\n')
    selected_ids = {name.split()[0] for name in selected}
    for directory in (base/'test-results/python').iterdir():
        if directory.is_dir() and not any(directory.name.startswith(id+'-attempt-') for id in selected_ids):
            shutil.copytree(directory,ROOT/'test-results/python'/directory.name,dirs_exist_ok=True)
    with (ROOT/'allure-results/environment.properties').open('a',encoding='utf-8') as out:
        out.write('Execution.Scope=Full Python regression plus explicit targeted verification; see test-results/merge-provenance.json\n')
    (ROOT/'test-results/merge-provenance.json').write_text(json.dumps({'base':str(base),'replacedCases':sorted(selected),'note':'Actual targeted results replace selected cases; other actual results retained.'},indent=2),encoding='utf-8')
