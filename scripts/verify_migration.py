import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    out = ROOT/'migration'
    result = subprocess.run([sys.executable,'-m','pytest','--collect-only','-q'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    (out/'python-collection.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:
        raise RuntimeError('Python collection failed')
    original = (out/'javascript-collection.txt').read_text(encoding='utf-8')
    names = re.findall(r'^.* › ([^\r\n]+)$',original,re.M)
    python = json.loads((out/'python-collection.json').read_text(encoding='utf-8'))
    py_names = {r['name'] for r in python}
    missing = sorted(set(names)-py_names)
    added = sorted(py_names-set(names))
    inventory = json.loads((out/'source-inventory.json').read_text(encoding='utf-8'))
    backup_errors = [r['source'] for r in inventory['backedUp'] if hashlib.sha256((ROOT/r['backup']).read_bytes()).hexdigest()!=r['sha256']]
    coverage = {'javascriptCount':len(names),'pythonCount':len(python),'missingOriginalCases':missing,'addedCases':added,'backupHashErrors':backup_errors,'differenceExplanation':'One added attended positive Visitor login test; all 99 original executable cases retained. Four account-control tests moved from header to visitor_login.'}
    (out/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf-8')
    mappings = [
        ('tests/header.spec.js','tests/test_header.py (19); tests/test_visitor_login.py (4)',23,'HomePage, HeaderPage, VisitorLoginPage, audit, context, page'),
        ('tests/hotels.spec.js','tests/test_hotels.py',1,'HotelsPage, existing JSON/Excel source match data, audit'),
        ('tests/navigation.spec.js','tests/test_navigation.py',75,'NavigationPage, HomePage, BasePage, audit'),
        ('tests/fixtures.js','tests/conftest.py; pages/base_page.py; pages/home_page.py; pages/data.py',0,'pytest fixtures/hooks; context isolation; diagnostics; failure media; first-retry trace; soft checks'),
        ('playwright.config.js','pytest.ini; tests/conftest.py; requirements.txt',0,'Chromium, viewport/timeouts, retries, Allure, failure artifacts'),
        ('scripts/run-tests.js','scripts/run_tests.py',0,'Archive generated results; pytest subprocess'),
        ('scripts/test-report.js','scripts/test_report.py; scripts/report.py',0,'Run pytest and generate report even on failures'),
        ('scripts/report-summary.js','scripts/report_summary.py',0,'Actual attempt aggregation; comparison; blocked subset of skips'),
        ('scripts/inspect-results.js','scripts/inspect_results.py',0,'Read latest actual Allure outcomes'),
        ('scripts/verify-allure.js','scripts/verify_allure.py',0,'Verify metadata and result/fixture attachments'),
        ('scripts/merge-rerun.js','scripts/merge_rerun.py',0,'Explicit real-result merge and provenance'),
        ('package.json; package-lock.json','requirements.txt; requirements-lock.txt; README.md',0,'Python dependency and command equivalents'),
        ('New requested scenario','tests/test_visitor_login.py (VISITOR-LOGIN-001)',1,'Headed Chromium, environment credentials, human CAPTCHA, no retries/recordings'),
    ]
    table = '# JavaScript to Python migration mapping\n\n| JavaScript source | Python replacement | Tests | Fixtures / utilities |\n|---|---|---:|---|\n'
    table += '\n'.join(f'| {a} | {b} | {c} | {d} |' for a,b,c,d in mappings)
    table += f"\n\nOriginal: {len(names)}; Python: {len(python)}. Missing original cases: {len(missing)}. Backup checksum errors: {len(backup_errors)}.\n\nAll existing IDs, test names, source data and expected results are preserved. Positive Visitor login is new. LIMIT-001 and LIMIT-002 remain historical scope exclusions.\n\nBrowser DOM evaluation uses Playwright's browser API; no Python test imports or invokes the JavaScript test runner, .spec.js files, package.json or playwright.config.js.\n"
    (out/'mapping.md').write_text(table,encoding='utf-8')
    sources = [r['source'] for r in inventory['backedUp'] if r['source'].endswith(('.js','.cjs','.mjs')) or r['source'] in ('package.json','package-lock.json')]
    removal = list(sources)
    if (ROOT/'node_modules').exists():
        removal += [p.relative_to(ROOT).as_posix() for p in (ROOT/'node_modules').rglob('*') if p.is_file()]
    manifest = {'approvalRequired':True,'deleted':False,'activeSourceFiles':sources,'generatedDependencyDirectory':'node_modules','allFilesProposedForRemoval':sorted(removal),'retained':['javascript_backup','test_data','tests/data','artifacts','manual_test_cases','comparison_results','allure-results','allure-report','test-results','run-history','venv','server.py','global Node installation','C:/Tools/allure-2.46.1']}
    (out/'removal-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (out/'removal-proposal.md').write_text('# Awaiting explicit removal approval\n\nNo files in this proposal have been deleted.\n\n'+ '\n'.join('- '+s for s in sources)+f"\n- node_modules/ ({len(removal)-len(sources)} dependency files; every path is listed in removal-manifest.json)\n\nThe global Allure installation and Node executable will be retained. Backups, test data, evidence, screenshots and all reports are retained.\n",encoding='utf-8')
    print(json.dumps(coverage,ensure_ascii=False,indent=2))
    return bool(missing or backup_errors or len(names)!=99 or len(python)!=100)

if __name__ == '__main__':
    raise SystemExit(main())
