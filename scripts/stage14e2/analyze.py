"""CPU-only closure of the frozen matched reader diagnostic; never launches work."""
from collections import Counter
import csv
import numpy as np
from scripts.stage14e2.common import P, load, save, sha, now
from scripts.stage14d1_pilot.statistics import bootstrap_indices, interval

ARMS = ('O_C', 'O_T', 'T_C', 'T_T', 'T_N')


def summarize(records, families):
    by = {(r['item_id'], r['condition']): r for r in records}
    assert len(by) == len(records)
    assert set(by) == {(f, a) for f in families for a in ARMS}
    strata = [by[f, 'T_C']['source_stratum'] for f in families]
    idx = bootstrap_indices(strata, 4000, 20261022)
    vectors, arms = {}, {}
    for a in ARMS:
        rs = [by[f, a] for f in families]
        v = np.array([r['label'] in ('U', 'R') for r in rs], dtype=int)
        vectors[a] = v
        arms[a] = dict(assigned=len(rs), attempted=sum(r['label'] != 'A' for r in rs),
            labels=dict(Counter(r['label'] for r in rs)), useful=int(v.sum()),
            rate=float(v.mean()), ci95=interval(v[idx].mean(1)),
            coverage=dict(Counter(r['coverage'] for r in rs)),
            parse_status=dict(Counter(r['status'] for r in rs)),
            useful_items=[r['item_id'] for r in rs if r['label'] in ('U', 'R')],
            interpretation='Textual source-correct response, not visual acquisition' if a == 'T_N'
                else 'Useful source reading including partial reinspection')
    pairs = {}
    for treatment, base in [('T_T', 'T_C'), ('O_T', 'O_C'), ('T_T', 'T_N')]:
        d = vectors[treatment] - vectors[base]
        pairs[treatment+'-'+base] = dict(difference=float(d.mean()), ci95=interval(d[idx].mean(1)),
            gains=[f for f, x in zip(families, d) if x == 1],
            losses=[f for f, x in zip(families, d) if x == -1])
    return dict(arms=arms, pairs=pairs, unit='conservative family', draws=4000,
        seed=20261022, strata=dict(Counter(strata)), zero_event_interval_is_degenerate=True)


def main():
    tasks = load(P/'inference/diagnostic_tasks_v1.json')
    packets = [p for file in sorted((P/'analysis').glob('source_packet_*_v1.json'))
               for p in load(file)['families']]
    assert len(packets) == 24 and {p['item_id'] for p in packets} == set(tasks['families'])
    labels = [r for file in sorted((P/'analysis').glob('source_reviews_*_v1.json'))
              for r in load(file)['rows']]
    by = {(r['item_id'], r['condition']): r for r in labels}
    assert len(by) == len(labels) == 120
    records = []
    for p in packets:
        assert sha(p['image']) == p['image_sha256']
        for o in p['outputs']:
            r = by[p['item_id'], o['condition']]
            assert r['label'] in ['U', 'R', 'K', 'W', '?', 'I', 'A', 'X']
            assert r['coverage'] in ['none', 'partial', 'full_task_source']
            assert r['notes'].strip()
            if o['status'] == 'ABSENT_ORIGINAL_TARGET':
                assert r['label'] == 'A'
            elif o['status'] != 'VALID':
                assert r['label'] == 'X'
            else:
                assert r['label'] not in ['A', 'X']
            if o['generation_path']:
                assert sha(o['generation_path']) == o['generation_sha256']
            quote = r.get('exact_quote', '')
            if quote:
                assert quote in o.get('final_body', ''), (p['item_id'], o['condition'], quote)
            records.append(dict(r, **{k: p[k] for k in ['family_id', 'image', 'image_sha256',
                'source_stratum', 'source_reference', 'prefix_sha256']}, **o,
                reviewer='Single AI reviewer; condition visible; source-referenced development diagnostic'))
    assert len({r['family_id'] for r in records}) == 24
    save(P/'analysis/source_review_complete_v1.json', dict(at=now(), rows=records))
    result = summarize(records, tasks['families'])
    save(P/'analysis/diagnostic_results_v1.json', dict(at=now(), **result,
        source_reviews_sha256=sha(P/'analysis/source_review_complete_v1.json'),
        final_answer_accuracy_measured=False, follow_on_authorized_now=False))
    with (P/'analysis/source_review_index_v1.csv').open('x', newline='') as out:
        fields = ['item_id', 'family_id', 'condition', 'label', 'coverage', 'status',
                  'source_stratum', 'notes', 'generation_path', 'generation_sha256', 'image']
        writer = csv.DictWriter(out, fieldnames=fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(records)
    print(result)


if __name__ == '__main__':
    main()
