"""Generate/open Allure with global CLI, retaining npx as a documented fallback only."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    action = sys.argv[1] if len(sys.argv)>1 else 'generate'
    if action not in ('generate','open'):
        raise SystemExit('Usage: python scripts/report.py [generate|open]')
    cli = shutil.which('allure') or shutil.which('allure.bat')
    if not cli:
        raise SystemExit('Install global Allure CLI or use: npx.cmd allure-commandline generate allure-results --clean -o allure-report')
    args = ['generate','allure-results','--clean','-o','allure-report'] if action=='generate' else ['open','allure-report']
    return subprocess.call([cli,*args],cwd=ROOT)

if __name__ == '__main__':
    raise SystemExit(main())
