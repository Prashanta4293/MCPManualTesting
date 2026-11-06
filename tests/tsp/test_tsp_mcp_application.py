"""Single sequential TSP entry point; currently stops at the source-evidence gate.

No UI validation trigger has a verified write contract. The executed gate records
BLOCKED; later scenarios remain NOT EXECUTED. This is not an implemented/passed
full E2E. No workbook readiness flag can authorize a UI action.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

import allure
import pytest
from playwright.sync_api import expect

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / 'data/tsp_sequential_scenarios.json'
ENTRY_BLOCKER = (
    'Application Type preflight BLOCKED: application initialization and #nextBtn '
    'Save & Continue handler/API write ordering are not established. This may '
    'create/update application selections, progress or a draft. No safe reset or '
    'non-persistent validation trigger is verified. Stop before browser/login/Apply; '
    'do not click Save & Continue or Save Draft. Source evidence and explicit '
    'progression authorization are required.'
)


def _blocked(reason):
    # Fixed public messages only; used by retained passive helpers.
    pytest.skip('BLOCKED: ' + reason)


@pytest.mark.tsp_application
@pytest.mark.regression
@pytest.mark.manual_captcha
@pytest.mark.flaky(reruns=0)
@allure.epic('Odisha Tourism')
@allure.feature('Sequential TSP application')
class TestTSPApplicationFlow:
    @allure.title('TSP-SEQ-001 Sequential negative and positive section flow')
    @allure.description('One ordered flow with source-evidence gates. No application '
                        'operation is enabled until its side effects and scenario '
                        'expectations are verified. Final submission is prohibited.')
    def test_tsp_sequential_flow(self, request):
        # Intentionally no tsp_session/tsp_data fixture argument: the entry safety
        # gate runs before any browser, credential loading or application setup.
        inventory = json.loads(INVENTORY.read_text(encoding='utf-8'))
        assert len(inventory['sections']) == 8
        assert len({r['id'] for r in inventory['records']}) == len(inventory['records'])
        self.results = [dict(r, status='NOT EXECUTED', actual='Not executed: sequential entry gate not cleared.',
                             evidence='No UI evidence; no screenshot captured.')
                        for r in inventory['records']]
        self.stopping_point = 'Execution configuration preflight'
        try:
            if os.getenv('PYTEST_XDIST_WORKER') or getattr(request.config.option, 'numprocesses', 0):
                pytest.skip('BLOCKED: sequential attended flow prohibits parallel execution.')
            if getattr(request.config.option, 'reruns', 0):
                pytest.skip('BLOCKED: sequential flow prohibits automatic retries.')
            if not request.config.getoption('--tsp-attended') or request.config.getoption('capture') != 'no':
                pytest.skip('BLOCKED: attended flow requires --tsp-attended and -s.')
            for section in inventory['sections']:
                self.run_section(section)
            # No false pass if future edits accidentally remove all section gates.
            raise AssertionError('Sequential UI completion is not implemented or verified.')
        except pytest.skip.Exception:
            raise
        except Exception:
            raise AssertionError('Sequential flow failed; private details suppressed.') from None
        finally:
            self.record_results()

    def run_section(self, section):
        """Order negative checks before positive completion; fail closed on missing contract."""
        self.stopping_point = section + ' / before validation or navigation'
        if section == 'Application Type':
            with allure.step('TSP-APP-001: inspect required-selection execution prerequisites'):
                for row in self.results:
                    if row['canonical_id'] == 'TSP-APP-001':
                        row['status'] = 'BLOCKED'
                        row['actual'] = ENTRY_BLOCKER
                        row['evidence'] = 'Source preflight only; neither required-field message was exercised.'
                allure.attach(ENTRY_BLOCKER, 'Sanitized source-preflight blocker', allure.attachment_type.TEXT)
                pytest.skip('BLOCKED: ' + ENTRY_BLOCKER)
        # Defense in depth: no implicit fill_all_sections(), next_section(), upload,
        # retry or save calls. Reaching a later section cannot authorize its actions.
        pytest.skip('BLOCKED: section entry, validation/reset and persistence contract unverified.')

    def record_results(self):
        pending = sys.exc_info()[0] is not None
        payload = {
            'test': 'TestTSPApplicationFlow::test_tsp_sequential_flow',
            'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
            'stopping_point': self.stopping_point,
            'browser_started': False,
            'ui_scenarios_executed': 0,
            'note': 'Source-preflight execution only. Aliases are not additional test executions. '
                    'Readiness is distinct from actual scenario status.',
            'scenarios': self.results,
        }
        try:
            body = json.dumps(payload, indent=2)
            output = Path(os.environ['TSP_SEQUENTIAL_RESULT_PATH']).resolve()
            assert output.is_relative_to((ROOT / 'artifacts').resolve())
            output.parent.mkdir(parents=True, exist_ok=True)
            # Never overwrite an earlier run's ledger.
            with output.open('x', encoding='utf-8') as stream:
                stream.write(body + '\n')
            allure.attach(body, 'Scenario-level execution ledger (sanitized)', allure.attachment_type.JSON)
        except Exception:
            if not pending:
                raise AssertionError('Sequential evidence recording failed; private details suppressed.') from None


    def check_applicant_conditional_fields(self, form):
        constitution = form.content.locator('select').first
        same_address = form.content.locator('input[type=checkbox]')
        if constitution.count() != 1 or same_address.count() != 1:
            _blocked('Existing applicant control mapping is ambiguous.')
        selected = constitution.evaluate('(e) => e.selectedOptions[0]?.textContent.trim() || ""')
        if not constitution.input_value().strip():
            _blocked('A constitution selection is required for this read-only conditional check.')
        other = form.content.get_by_placeholder('Specify constitution type', exact=True)
        if selected in ('Other', 'Others'):
            expect(other).to_be_visible(timeout=5000)
        else:
            expect(other).not_to_be_visible(timeout=5000)
        separate = not same_address.is_checked()
        for placeholder in ('Flat / House No., Street, Locality', 'Enter Block / ULB', 'Enter Gram Panchayat / Ward', 'Enter Village'):
            fields = form.content.get_by_placeholder(placeholder, exact=True)
            expect(fields.first).to_be_visible(timeout=5000)
            if separate:
                expect(fields).to_have_count(2, timeout=5000)
                expect(fields.nth(1)).to_be_visible(timeout=5000)
            else:
                expect(fields.nth(1)).not_to_be_visible(timeout=5000)

    def check_form_accessibility(self, form):
        name = form.content.get_by_placeholder('Full legal name of the firm or applicant', exact=True)
        expect(name).to_have_count(1, timeout=5000)
        expect(name).to_be_visible(timeout=5000)
        semantics = name.evaluate("e => ({\n            labelled: !!(e.getAttribute('aria-label') || '').trim()\n                || [...(e.labels || [])].some(l => !!l.textContent.trim())\n                || (e.getAttribute('aria-labelledby') || '').split(/\\s+/).filter(Boolean)\n                    .some(id => !!document.getElementById(id)?.textContent.trim()),\n            required: e.required || e.getAttribute('aria-required') === 'true'\n        })")
        assert semantics['labelled'], 'Applicant-name programmatic label is missing.'
        assert semantics['required'], 'Applicant-name required semantics are missing.'
