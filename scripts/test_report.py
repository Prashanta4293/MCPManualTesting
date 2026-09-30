import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    tests = subprocess.call([sys.executable,str(ROOT/'scripts/run_tests.py'),*sys.argv[1:]],cwd=ROOT)
    report = subprocess.call([sys.executable,str(ROOT/'scripts/report.py'),'generate'],cwd=ROOT)
    raise SystemExit(tests or report)
