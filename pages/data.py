import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = 'https://apptourlfr-stg.estpl.net/home'

def read_json(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8-sig'))

ROWS = read_json('manual_test_cases/odisha_evidence/consolidated_test_rows.json')
INVENTORY = read_json('manual_test_cases/odisha_evidence/navigation_inventory.json')
HOTEL_CASE = {'Test Case ID': 'HOTEL-DATA-001', 'Test Scenario': 'Recheck confirmed workbook hotel names and phone numbers', 'Module': 'Hotel data comparison', 'Expected Result': 'Confirmed hotel names and phone numbers match the supplied source workbook.', 'Severity': 'Medium', 'Preconditions': 'Anonymous visitor; supplied hotel source workbook and exact-match browser evidence.', 'Test Data': 'tests/data/hotel-matches.json'}
LOGIN_CASE = {'Test Case ID': 'VISITOR-LOGIN-001', 'Test Scenario': 'Positive Visitor login with manual CAPTCHA', 'Module': 'Visitor login', 'Expected Result': 'Valid credentials and manually entered CAPTCHA authenticate the visitor and expose an authenticated logout control.', 'Severity': 'High', 'Preconditions': 'VISITOR_EMAIL and VISITOR_PASSWORD configured; attended headed Chromium; --manual-login enabled.', 'Test Data': 'Environment credentials; human-entered CAPTCHA only.'}

def case_name(case):
    return f"{case['Test Case ID']} {case['Test Scenario']}"
