"""Python-only runner; archive previous generated outputs without deleting evidence."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def archive_results():
    folder = ROOT / 'run-history' / ('python-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    for name in ('allure-results','allure-report','test-results'):
        source = (ROOT / name).resolve()
        if source.parent != ROOT:
            raise RuntimeError('Output path escaped workspace')
        if source.exists():
            folder.mkdir(parents=True,exist_ok=True)
            source.rename(folder / name)
    return folder

def metadata():
    out = ROOT / 'allure-results'
    out.mkdir(exist_ok=True)
    original = ROOT / 'migration/original-executor.json'
    executor = json.loads(original.read_text(encoding='utf-8-sig')) if original.exists() else {}
    executor.update({'type':'local','buildName':'Odisha Tourism Python pytest execution','reportName':'Odisha Tourism Python Allure Report','buildUrl':'https://apptourlfr-stg.estpl.net/home'})
    (out / 'executor.json').write_text(json.dumps(executor,indent=2),encoding='utf-8')
    (out / 'environment.properties').write_text('Application=Odisha Tourism\nEnvironment=Staging\nBase.URL=https://apptourlfr-stg.estpl.net/home\nExecution.Tool=Python Playwright sync API\nTest.Framework=pytest + pytest-playwright\nBrowser=Chromium\nOperating.System=Windows\nCredentials=Environment variables; never attached\nExecution.Date='+datetime.now(timezone.utc).isoformat()+'\n',encoding='utf-8')

def main():
    args = sys.argv[1:]
    collect = '--collect-only' in args
    if not collect:
        archive = archive_results()
        metadata()
        print(f'Previous generated outputs preserved in {archive.relative_to(ROOT)}',flush=True)
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    code = subprocess.call([sys.executable,'-m','pytest',*args],cwd=ROOT,env=env)
    if not collect:
        subprocess.call([sys.executable,str(ROOT/'scripts/report_summary.py')],cwd=ROOT,env=env)
    return code

if __name__ == '__main__':
    raise SystemExit(main())
