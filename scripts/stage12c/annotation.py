"""Persist human-readable semantic review decisions; never infer labels from length."""
from scripts.stage12c.common import ROOT, load, save, now


def record(task_id, outcome, positives=(), reason='', details=None):
    packet = load(ROOT / 'audit/technical_packets' / f'{task_id}.json')
    path = ROOT / 'audit/technical_annotations' / f'{task_id}.json'
    assert not path.exists(), 'Preserve first-pass decisions; adjudicate separately'
    reasons = {
        'R1': 'Full trace does not repeatedly cycle without meaningful progress.',
        'R2': 'No task answer followed by a renewed derivation/interpretation; finite verification is not reopening.',
        'R3': 'No prolonged incompatible hypotheses without convergence; finite corrections do not qualify.',
        'R4': 'No substantial advancing computation lasting at least4096 generated tokens.',
        'R5': 'One task answer remains uniquely committed at the end.',
    }
    if details: reasons.update(details)
    assert all(f'R{i}' in (details or {}) for i in positives)
    save(path, dict(task_id=task_id, generation_sha256=packet['generation_sha256'],
        scoreable=outcome is not None, extracted_outcome=outcome, reason=reason,
        quotes=[packet['raw'][-1200:]], labels={f'R{i}': i in positives for i in range(1,6)},
        label_reasons=reasons, at=now(),
        review_scope='All unique exact paragraphs in first-occurrence order and original-order ending; no source-answer comparison.'))


def show(task_id, start=0, end=None, tail=0):
    p = load(ROOT / 'audit/technical_packets' / f'{task_id}.json')
    text = '\n\n'.join(x['text'] for x in p['unique_paragraphs'] if x['offset']==x['first_occurrence'])
    print(task_id, 'TOKENS', p['tokens'], 'CAP', p['cap_hit'], 'UNIQUE_CHARS', len(text), 'QUESTION', p['question'])
    print(text[start:end])
    if tail: print('ORIGINAL-ORDER TAIL',p['raw'][-tail:])
