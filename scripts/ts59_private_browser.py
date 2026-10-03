"""Private credential/storage bridge for a visible browser controlled by Playwright MCP.

No tests run here. MCP performs the manual interactions; this process keeps secrets
out of MCP arguments, logs and conversation output. Control messages contain actions only.
"""
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT/'.auth/ts59'

def main():
    load_dotenv(ROOT/'.env',override=True)
    for key in ('DEBUG','PWDEBUG'):
        os.environ.pop(key,None)
    if not all(os.getenv(k) for k in ('VISITOR_EMAIL','VISITOR_PASSWORD')):
        print('BLOCKED: Visitor credentials unavailable.',flush=True)
        return
    PRIVATE.mkdir(parents=True,exist_ok=True)
    control=PRIVATE/'control.json'
    seen=None
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=False,args=['--remote-debugging-port=9333','--remote-debugging-address=127.0.0.1'])
        context=browser.new_context(viewport={'width':1366,'height':900})
        page=context.new_page()
        print('PRIVATE_BROWSER_READY: localhost:9333',flush=True)
        while not page.is_closed():
            if control.exists():
                message=json.loads(control.read_text(encoding='utf-8'))
                if message.get('nonce')!=seen:
                    seen=message.get('nonce')
                    try:
                        action=message['action']
                        if action=='fill':
                            username=page.locator('#otLoginEmail')
                            username.evaluate("e=>e.style.setProperty('-webkit-text-security','disc','important')")
                            username.fill(os.environ['VISITOR_EMAIL'])
                            page.locator('#otLoginPassword').fill(os.environ['VISITOR_PASSWORD'])
                            page.locator('#otLoginCaptchaInput').focus()
                            print('CREDENTIALS_FILLED: Await explicit human CAPTCHA confirmation; not submitted.',flush=True)
                        elif action=='save':
                            assert page.evaluate('() => window.Liferay?.ThemeDisplay?.isSignedIn?.() === true')
                            context.storage_state(path=str(PRIVATE/'state.json'))
                            print('AUTHENTICATED_STATE_SAVED_PRIVATELY',flush=True)
                        elif action=='stop':
                            break
                    except Exception:
                        print('PRIVATE_ACTION_BLOCKED: details suppressed to protect credentials.',flush=True)
            page.wait_for_timeout(200)
        browser.close()

if __name__=='__main__':
    main()
