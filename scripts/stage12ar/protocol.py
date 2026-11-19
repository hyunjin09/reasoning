"""Source-only selection and output-only gates; never consult correctness."""
import hashlib
import statistics

SELECTION_SEED = 'stage12ar-validation-v1'
D_MC = ('Solve the problem silently.\nDo not show any reasoning or explanation.\n'
        'Respond with exactly one option letter: A, B, C, D, or E.\nOutput nothing else.')
D_OPEN = ('Solve the problem silently.\nDo not show any reasoning or explanation.\n'
          'Respond with exactly one final value or mathematical expression.\nOutput nothing else.')
C0 = "Let's think step by step."
C1 = ("Let's think step by step.\nAfter your reasoning, end with exactly one line of the form "
      'Final answer: X, where X is the final option letter, value, or expression.')


def select_validation(rows, development_ids):
    pool = [r for r in rows if r['item_id'] not in set(development_ids)]
    key = lambda r: (hashlib.sha256((SELECTION_SEED + '|' + r['family_id']).encode()).hexdigest(), r['family_id'])
    mc = sorted([r for r in pool if r['answer_type'] == 'multiple_choice'], key=key)
    op = sorted([r for r in pool if r['answer_type'] == 'open_ended'], key=key)
    if len(mc) >= 5 and len(op) >= 7:
        chosen = mc[:5] + op[:7]
    else:
        chosen = sorted(pool, key=key)[:12]
    assert len(chosen) == 12 and len({r['family_id'] for r in chosen}) == 12
    return [r['item_id'] for r in sorted(chosen, key=key)]


def build_prompt(row, arm):
    suffix = {'D': D_MC if row['answer_type'] == 'multiple_choice' else D_OPEN,
              'C0': C0, 'C1': C1}[arm]
    return row['question'] + '\n\n' + suffix


def gate(arm, rows):
    assert arm in ['D', 'C0', 'C1'] and len(rows) == 12
    s = {k: sum(r[k] for r in rows) for k in
         ['format_valid', 'visible_reasoning', 'committed_final', 'cap_hit', 'severe_repetition']}
    s.update(n=12, median_tokens=statistics.median(r['tokens'] for r in rows))
    if arm == 'D':
        passed = (s['format_valid'] >= 10 and s['committed_final'] >= 11
                  and s['visible_reasoning'] <= 1 and s['cap_hit'] == 0 and s['severe_repetition'] == 0)
    else:
        passed = (s['format_valid'] >= 10 and s['committed_final'] >= 10
                  and s['visible_reasoning'] >= 10 and s['cap_hit'] <= 1 and s['severe_repetition'] <= 1)
    return {'pass': passed, 'summary': s}


def select_candidate(candidates):
    valid = [a for a, r in candidates.items() if r['pass']]
    def key(a):
        s = candidates[a]['summary']
        return (s['severe_repetition'], s['cap_hit'], -s['committed_final'],
                -s['format_valid'], s['median_tokens'], a != 'C0')
    return min(valid, key=key) if valid else None


def authorize_manifest(m):
    from scripts.stage12ar.common import ROOT, load
    dev = load(ROOT / 'stage12ar_development_manifest.json')
    val = load(ROOT / 'stage12ar_validation_manifest.json')
    phase = m['phase']
    if phase == 'development_D':
        expected = [t for t in dev['rows'] if t['arm'] == 'D']
    elif phase == 'development_C':
        assert load(ROOT / 'audit/development_D_review.json')['gates']['D']['pass']
        expected = [t for t in dev['rows'] if t['arm'] in ['C0', 'C1']]
    elif phase == 'validation':
        selection = load(ROOT / 'stage12ar_candidate_selection.json')
        assert selection['D_development_pass'] and selection['selected_C'] in ['C0', 'C1']
        expected = [t for t in val['prospective_tasks'] if t['arm'] in ['D', selection['selected_C']]]
    else:
        raise AssertionError('No scientific or unplanned phase authorized')
    assert m['rows'] == expected
