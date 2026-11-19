"""Frozen Stage12B prompts, gates, and candidate labels."""
from scripts.stage12b.common import ROOT, CAPS, load


def build_prompt(row, arm):
    if arm == 'N':
        return row['question']
    if arm == 'O':
        facts = '\n'.join(f'- E{i}: {f["probe_request"]} {f["gold_value"]}' for i, f in enumerate(row['facts'], 1))
        return ('Use the following facts from the image as given.\nDo not question or reinterpret them.\n\n'
                f'Visual facts:\n{facts}\n\nOriginal question:\n{row["question"]}')
    assert arm == 'E'
    requests = '\n'.join(f'E{i}: {f["probe_request"]}' for i, f in enumerate(row['facts'], 1))
    schema = '\n'.join(f'E{i}: [value]' for i in range(1, len(row['facts']) + 1))
    return ('Inspect the image and report only the requested visual facts.\n'
            'Do not solve the original problem.\nDo not explain or show reasoning.\n'
            f'Requested facts:\n{requests}\nReturn exactly:\n{schema}')


def technical_gate(rows):
    assert set(rows) == set('ENO') and all(len(rr) == 12 for rr in rows.values())
    summaries = {a: dict(n=12, parseable=sum(r['parseable'] for r in rr),
                        committed_finals=sum(r['committed_final'] for r in rr),
                        caps=sum(r['cap_hit'] for r in rr),
                        repetitions=sum(r['repetition_pathology'] for r in rr)) for a, rr in rows.items()}
    passed = {}
    for arm, s in summaries.items():
        passed[arm] = s['repetitions'] <= 1 and (s['parseable'] >= 10 if arm == 'E' else
                                                s['committed_finals'] >= 10 and s['caps'] <= 1)
    return dict(summaries=summaries, pass_by_arm=passed, **{'pass': all(passed.values())})


def profile(e, n, o):
    if any(v is None for v in (e, n, o)) or n:
        return None
    return {(False, True): 'B1', (True, True): 'B2', (True, False): 'B3', (False, False): 'B4'}[e, o]


def authorize_manifest(m, gate=None, integrity=None):
    if integrity is None:
        integrity = load(ROOT / 'stage12b_oracle_integrity_review.json')['pass']
    assert integrity, 'Oracle integrity is mandatory before generation'
    if m['phase'] != 'technical':
        if gate is None:
            gate = load(ROOT / 'stage12b_technical_sanity.json')['pass']
        assert gate and m['phase'] == 'main'
    for task in m['rows']:
        a = task['arm']
        assert a in CAPS
        if a == 'O':
            assert task['image'] is None and task['image_sha256'] is None
        else:
            assert task['image'] and task['image_sha256']
        assert task['cap'] == CAPS[a]
