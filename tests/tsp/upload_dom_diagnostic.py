"""Opt-in, read-only capture from the attended test's own page; no screenshots."""
import json
from pathlib import Path

import allure
import pytest


def read_upload_dom(form):
    """Read one snapshot without clicking, filling, uploading or saving."""
    form.at('HR & Certification')
    evidence = form.page.evaluate(r'''(expected) => {
      const root = document.querySelector('#stepContent');
      if (!root) return {blocked: 'Step content unavailable'};
      const ids = ['fileInput_tempQualCert', 'fileInput_tempIittmDoc'];
      const knownText = new Set([
        'Qualification Certificate (Latest)', 'IITTM TSP Certification',
        'Is IITTM Certified?', 'Upload IITTM Certificate Document',
        'Uploaded successfully', 'Uploaded', '- Uploaded', 'Uploading...',
        'Pending Upload', 'Upload failed', 'Save Draft To Upload',
        'Yes', 'No', 'Browse Files', 'Remove', 'Cancel', 'Retry Upload'
      ]);
      const safeClasses = new Set(['active', 'selected', 'disabled', 'hidden',
        'd-none', 'form-control', 'is-invalid', 'is-valid', 'text-danger',
        'text-success', 'alert', 'alert-danger', 'alert-success']);
      const aliases = new Map();
      const detached = document.implementation.createHTMLDocument('');
      function alias(value) {
        if (!aliases.has(value)) aliases.set(value, `redacted-token-${aliases.size + 1}`);
        return aliases.get(value);
      }
      function path(node) {
        if (node === root) return '#stepContent';
        const parts = [];
        while (node && node !== root) {
          const siblings = [...node.parentElement.children].filter(e => e.localName === node.localName);
          parts.unshift(`${node.localName}:nth-of-type(${siblings.indexOf(node) + 1})`);
          node = node.parentElement;
        }
        return node === root ? '#stepContent > ' + parts.join(' > ') : null;
      }
      function attrs(e) {
        const result = {};
        if (e.id) result.id = ids.includes(e.id) ? e.id : alias(e.id);
        if (e.classList.length) result.class = [...e.classList].map(c => safeClasses.has(c) ? c : alias(c)).join(' ');
        const allowed = {
          type: ['file', 'radio', 'checkbox', 'text', 'button', 'hidden'],
          role: ['status', 'alert', 'progressbar', 'button', 'group'],
          'aria-live': ['polite', 'assertive', 'off'],
          'aria-invalid': ['true', 'false'], 'aria-required': ['true', 'false'],
          'aria-busy': ['true', 'false']
        };
        for (const [key, values] of Object.entries(allowed)) {
          if (e.hasAttribute(key)) result[key] = values.includes(e.getAttribute(key)) ? e.getAttribute(key) : '[REDACTED]';
        }
        for (const key of ['required', 'disabled', 'hidden', 'multiple'])
          if (e.hasAttribute(key)) result[key] = '';
        return result;
      }
      function clean(node) {
        if (node.nodeType === Node.TEXT_NODE) {
          const t = node.textContent.trim();
          return detached.createTextNode(!t ? '' : expected.includes(t) ? '[EXPECTED_FILENAME]' : knownText.has(t) ? t : '[REDACTED]');
        }
        if (node.nodeType !== Node.ELEMENT_NODE) return detached.createTextNode('');
        if (['script', 'style', 'iframe', 'object', 'embed', 'canvas', 'svg', 'img'].includes(node.localName))
          return detached.createTextNode('[OMITTED]');
        const copy = detached.createElement(node.localName);
        for (const [k,v] of Object.entries(attrs(node))) copy.setAttribute(k,v);
        for (const child of node.childNodes) copy.appendChild(clean(child));
        return copy;
      }
      const visible = e => !!e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden';
      function details(e, expectedName) {
        const direct = [...e.childNodes].filter(n => n.nodeType === Node.TEXT_NODE).map(n => n.textContent).join(' ').trim();
        return {path: path(e), attributes: attrs(e), visible: visible(e),
          text: knownText.has(direct) ? direct : direct ? '[REDACTED]' : '',
          expectedFilenameInDirectText: direct.includes(expectedName),
          successText: /^Uploaded successfully[.!]?$/i.test(direct),
          possiblePendingText: /\b(uploading|pending)\b/i.test(direct),
          possibleErrorText: /\b(error|failed|failure)\b/i.test(direct),
          invalid: e.getAttribute('aria-invalid') === 'true',
          draftRequiredText: /Save Draft To Upload|Please save the draft first/i.test(direct)};
      }
      const components = ids.map((id,i) => {
        const input = root.querySelector('#' + id);
        if (!input) return {id, present: false};
        const ancestors = [];
        for (let e=input.parentElement,level=1; e && root.contains(e) && e !== root && level<=4; e=e.parentElement,level++) {
          ancestors.push({levelsAboveInput: level, path: path(e),
            fileInputCount: e.querySelectorAll('input[type=file]').length,
            attributes: attrs(e), sanitizedOuterHTML: clean(e).outerHTML,
            elements: [e,...e.querySelectorAll('*')].map(n => details(n, expected[i]))});
          if (e.querySelectorAll('input[type=file]').length > 1) break;
        }
        return {id, present: true, inputAttributes: attrs(input),
          inputVisible: visible(input), inputDisabled: input.disabled,
          inputRequired: input.required, selectedFileCount: input.files?.length || 0,
          parentVisible: visible(input.parentElement), ancestors};
      });
      const first=root.querySelector('#'+ids[0]), second=root.querySelector('#'+ids[1]);
      const radios = [...root.querySelectorAll('input[type=radio]')].map(e => {
        const label=[...(e.labels || [])].map(l=>l.textContent.trim()).join(' ').trim();
        return {path:path(e), label:['Yes','No'].includes(label)?label:'[REDACTED]', checked:e.checked, visible:visible(e)};
      });
      return {section:'HR & Certification', separateImmediateParents:first&&second ? first.parentElement!==second.parentElement : null,
        components, radios,
        note:'Unknown identifiers/classes are consistent redacted aliases, not executable selectors. Structural paths reference this snapshot only. Required attributes do not establish business validation.'};
    }''', [Path(form.data['staff']['qualification_file']).name,
           Path(form.data['staff']['iittm_file']).name])
    return evidence


def _reply(prompt):
    print(prompt, flush=True)
    try:
        return input().strip()
    except (EOFError, OSError):
        return 'BLOCKED'


def _snapshot(form):
    try:
        return read_upload_dom(form)
    except Exception:
        # No raw exception/DOM fallback if the form is inaccessible or navigated away.
        return {'blocked': 'Step 4 DOM unavailable; sanitized component evidence could not be captured.'}


def _candidate(evidence, input_id):
    """Evidence candidate only, not production upload-verification logic."""
    for component in evidence.get('components', []):
        if component.get('id') != input_id:
            continue
        for ancestor in component.get('ancestors', []):
            nodes = [n for n in ancestor['elements'] if n['visible']]
            if (ancestor['fileInputCount'] == 1
                    and any(n['expectedFilenameInDirectText'] for n in nodes)
                    and any(n['successText'] for n in nodes)
                    and not any(n['possiblePendingText'] or n['attributes'].get('aria-busy') == 'true' or n['possibleErrorText']
                                or n['invalid'] or n['draftRequiredText'] for n in nodes)):
                return ancestor['path']
    return None


def capture_upload_dom(form):
    ready = _reply(
        'DIAGNOSTIC: In this Playwright browser navigate to an already accessible Step 4. '
        'Do not save, continue, submit or add staff. IITTM Yes must already be selected. '
        'Type READY when available, or BLOCKED to capture available evidence and stop.')
    initial = _snapshot(form)
    allure.attach(json.dumps(initial, indent=2), 'Upload diagnostic baseline (sanitized)', allure.attachment_type.JSON)
    yes = any(r.get('label') == 'Yes' and r.get('checked') and r.get('visible')
              for r in initial.get('radios', []))
    if ready != 'READY' or initial.get('blocked') or not yes:
        allure.attach('Both successful-upload checkpoints BLOCKED: an accessible Step 4 with IITTM Yes was not confirmed. Baseline contains any available evidence.',
                      'Upload checkpoint outcome', allure.attachment_type.TEXT)
        pytest.skip('BLOCKED: Safe upload diagnostic prerequisites unavailable.')

    for number, label, input_id in (
        (1, 'Qualification Certificate', 'fileInput_tempQualCert'),
        (2, 'IITTM Certificate', 'fileInput_tempIittmDoc'),
    ):
        answer = _reply(
            f'Checkpoint {number}: {label}. If not already uploaded, manually choose only '
            'the configured test PDF from test_data/PDF files in this component. '
            'Do not replace/delete existing files, save, continue, submit or add staff. '
            'When Uploaded successfully is displayed, type CAPTURE. '
            'If reaching that state requires a prohibited action, type BLOCKED.')
        evidence = _snapshot(form)
        candidate = _candidate(evidence, input_id)
        # Reject blockers anywhere in either observed component, not only the candidate.
        blocker = any(n['visible'] and n['draftRequiredText']
                      for c in evidence.get('components', [])
                      for a in c.get('ancestors', []) for n in a['elements'])
        confirmed = answer == 'CAPTURE' and candidate is not None and not blocker
        report = {'checkpoint': number, 'component': label,
                  'status': 'Evidence captured - review required' if confirmed else 'BLOCKED',
                  'commonAncestorCandidate': candidate, 'dom': evidence}
        allure.attach(json.dumps(report, indent=2),
                      f'Checkpoint {number} {label} DOM (sanitized)', allure.attachment_type.JSON)
        if not confirmed:
            if number == 1:
                allure.attach(json.dumps({'checkpoint': 2, 'status': 'BLOCKED - not attempted',
                                         'dom': evidence}, indent=2),
                              'Checkpoint 2 available DOM only (sanitized)', allure.attachment_type.JSON)
            pytest.skip('BLOCKED: Successful component state not safely established; available sanitized evidence attached.')
    pytest.skip('Both upload checkpoints captured for review only; positive form test not executed.')
