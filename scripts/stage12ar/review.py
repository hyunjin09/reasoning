"""Manual output-only technical review with immutable raw-output binding."""
import argparse
from scripts.stage12ar.common import ROOT, load, save, sha, now
from scripts.stage12ar.protocol import gate, select_candidate
from scripts.stage11cr.protocol import repetition_metrics


def packet(label):
    rows = []
    m = load(ROOT / 'audit' / f'{label}.json')
    for t in m['rows']:
        f = ROOT / 'generations' / t['task_id']
        if not (f / 'result.json').exists():
            continue
        assert load(f / 'result.json')['generation_sha256'] == sha(f / 'generation.json')
        g = load(f / 'generation.json')
        rows.append(dict(task_id=t['task_id'], arm=t['arm'], item_id=t['item_id'],
            answer_type=t['answer_type'], raw=g['raw_decoded_response'], tokens=g['tokens'],
            cap_hit=g['cap_hit'], normal_stop=g['normal_stop'],
            generation_sha256=sha(f / 'generation.json'),
            repetition_metrics=repetition_metrics(g['generated_token_ids'])))
    path = ROOT / 'audit/review_packets' / f'{label}_{now().replace(":", "")}.json'
    save(path, dict(at=now(), correctness_opened=False, rows=rows, expected=len(m['rows'])))
    print(path)
    for r in rows:
        print(r['task_id'], r['tokens'], r['cap_hit'], r['repetition_metrics'])


def seal(label, decisions):
    m = load(ROOT / 'audit' / f'{label}.json')
    d = load(decisions)
    assert d['correctness_opened'] is False
    tasks = {t['task_id']: t for t in m['rows']}
    assert len(d['rows']) == len(tasks) and {r['task_id'] for r in d['rows']} == set(tasks)
    rows = []
    for r in d['rows']:
        t = tasks[r['task_id']]
        p = ROOT / 'generations' / r['task_id'] / 'generation.json'
        g = load(p)
        assert r['generation_sha256'] == sha(p)
        for k in ['format_valid', 'visible_reasoning', 'committed_final', 'severe_repetition']:
            assert isinstance(r[k], bool)
        assert r['reason'] and r['quote'] and r['quote'] in g['raw_decoded_response']
        rows.append(dict(r, item_id=t['item_id'], family_id=t['family_id'], arm=t['arm'],
            tokens=g['tokens'], cap_hit=g['cap_hit'], normal_stop=g['normal_stop']))
    gates = {a: gate(a, [r for r in rows if r['arm'] == a]) for a in sorted({r['arm'] for r in rows})}
    save(ROOT / 'audit' / f'{label}_review.json', dict(at=now(), correctness_opened=False,
        decisions_path=decisions, decisions_sha256=sha(decisions), rows=rows, gates=gates))
    print('SEALED', label, gates)


def select():
    d = load(ROOT / 'audit/development_D_review.json')
    assert d['gates']['D']['pass']
    c = load(ROOT / 'audit/development_C_review.json')
    assert set(c['gates']) == {'C0', 'C1'}
    selected = select_candidate(c['gates'])
    save(ROOT / 'stage12ar_candidate_selection.json', dict(at=now(), correctness_opened=False,
        D_development_pass=True, candidate_gates=c['gates'], selected_C=selected,
        priority=['fewer severe repetitions', 'fewer caps', 'more committed finals',
                  'more format-valid responses', 'shorter median token count', 'C0'],
        development_reviews_sha256={str(ROOT / 'audit' / f'{x}_review.json'): sha(ROOT / 'audit' / f'{x}_review.json') for x in ['development_D','development_C']}))
    if selected:
        val = load(ROOT / 'stage12ar_validation_manifest.json')
        save(ROOT / 'audit/validation.json', dict(at=now(), frozen=True, phase='validation',
            config_sha256=sha(ROOT / 'config.json'),
            rows=[t for t in val['prospective_tasks'] if t['arm'] in ['D', selected]]))
    print('SELECTED_C', selected)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['packet', 'seal', 'select'])
    p.add_argument('label', nargs='?')
    p.add_argument('decisions', nargs='?')
    a = p.parse_args()
    if a.action == 'packet': packet(a.label)
    elif a.action == 'seal': seal(a.label, a.decisions)
    else: select()
