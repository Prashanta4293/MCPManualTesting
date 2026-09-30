"""Non-destructive inventory and source backup before migration."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'node_modules', 'venv', '.git', '__pycache__', '.pytest_cache', 'javascript_backup', 'allure-results', 'allure-report', 'test-results', 'run-history', 'artifacts', 'migration'}

def main():
    out = ROOT / 'migration'
    out.mkdir(exist_ok=True)
    sources = []
    inventory = []
    for directory, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDED]
        for name in files:
            p = Path(directory) / name
            rel = p.relative_to(ROOT)
            inventory.append(str(rel))
            if p.suffix in {'.js', '.cjs', '.mjs'} or str(rel) in {'package.json', 'package-lock.json', 'README.md', '.gitignore'}:
                target = ROOT / 'javascript_backup' / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() and target.read_bytes() != p.read_bytes():
                    raise RuntimeError(f'Refusing to overwrite existing backup: {rel}')
                if not target.exists():
                    shutil.copy2(p, target)
                sources.append({'source': rel.as_posix(), 'backup': target.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    (out / 'source-inventory.json').write_text(json.dumps({'rootEntries': [p.name for p in ROOT.iterdir()], 'sourceAndEvidenceFiles': inventory, 'excludedGeneratedTrees': sorted(EXCLUDED), 'backedUp': sources}, indent=2), encoding='utf-8')
    result = subprocess.run(['npx.cmd', 'playwright', 'test', '--list', '--reporter=list'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    (out / 'javascript-collection.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
    if result.returncode:
        raise RuntimeError('JavaScript collection failed; see migration/javascript-collection.txt')
    previous = ROOT / 'test-results/summary.json'
    if previous.exists() and not (out / 'javascript-outcomes.json').exists():
        shutil.copy2(previous, out / 'javascript-outcomes.json')
    for name in ['executor.json', 'environment.properties']:
        p = ROOT / 'allure-results' / name
        if p.exists() and not (out / f'original-{name}').exists():
            shutil.copy2(p, out / f'original-{name}')
    print(f'Backed up {len(sources)} source/config files; no files deleted.')
    print(result.stdout.splitlines()[-1])

if __name__ == '__main__':
    main()
