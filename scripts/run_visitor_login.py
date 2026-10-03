"""Fresh scoped execution; preserve previous reports and run negative cases first."""
import os
from pathlib import Path
import subprocess
import sys
from run_tests import archive_results, metadata

ROOT = Path(__file__).resolve().parents[1]

def main():
    if sys.argv[1:]:
        raise SystemExit('This runner has no arguments. Use direct pytest for an attended targeted rerun.')
    print(f'Archived previous outputs: {archive_results()}',flush=True)
    metadata()
    base = [sys.executable,'-m','pytest','tests/test_visitor_login.py::test_workbook_visitor_login','--reruns','0']
    env = dict(os.environ,PYTHONIOENCODING='utf-8')
    groups = [
        ('Negative stable cases',['-m','negative and not manual_captcha']),
        ('Invalid-credential attended case',['-m','negative and manual_captcha','--manual-login','--headed','-s']),
        ('Remaining stable cases',['-m','not negative and not manual_captcha']),
        ('Separate positive attended cases',['-m','positive and manual_captcha','--manual-login','--headed','-s']),
    ]
    codes=[]
    for name,args in groups:
        print(name,flush=True)
        code=subprocess.call(base+args,cwd=ROOT,env=env)
        codes.append(code)
        if code not in (0,1):
            break
    subprocess.call([sys.executable,'scripts/visitor_login_report.py'],cwd=ROOT,env=env)
    return max(codes)

if __name__=='__main__':
    raise SystemExit(main())
