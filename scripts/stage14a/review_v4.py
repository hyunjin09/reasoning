"""QC-aware replacement counting; preserves v3 and every primary/source reread receipt."""
import argparse
import json
from scripts.stage14a.common import ROOT, load, save, sha, now
from scripts.stage14a.review import rendering
from scripts.stage14a.review_v2 import validate


def canonical_map(families, supplements):
    parent = {f: f for f in families}

    def find(f):
        while parent[f] != f:
            f = parent[f]
        return f

    for s in supplements:
        roots = {find(f) for f in s['frozen_family_ids']}
        target = min(roots)
        for f in roots:
            parent[f] = target
    return {f: find(f) for f in parent}


def accepted_families(rows, canonical, qc_rows=()):
    rejected = {r['item_id'] for r in qc_rows if r['eligibility'] == 'FAIL'}
    assert all(r['eligibility'] in ['PASS','FAIL'] and r['resolved_for_final_seal'] for r in qc_rows)
    return {canonical[r['family_id']] for r in rows if r['decision'] == 'ACCEPT' and r['item_id'] not in rejected}


def advance(seen, family, decision, target=1000):
    assert len(seen) < target, 'Stop immediately at target independent families.'
    result = set(seen)
    if decision == 'ACCEPT':
        result.add(family)
    return result


def commit(path):
    order = load(ROOT/'stage14a_mathvision_candidate_order.json')['rows']
    by = {r['item_id']: r for r in load(ROOT/'audit/mathvision_census_source_snapshot.json')['rows']}
    supplements = sorted((ROOT/'audit').glob('source_alias_supplement_*_v1.json'))
    canonical = canonical_map({r['family_id'] for r in by.values()}, [load(p) for p in supplements])
    previous = [load(p) for p in sorted((ROOT/'audit/reviews/mathvision_v2').glob('*.json'))]
    qc_rows = [load(p) for p in sorted((ROOT/'audit/reviews/mathvision_qc250').glob('*.json'))]
    seen = accepted_families(previous, canonical, qc_rows)
    rows = load(path)
    prepared = []
    for i, row in enumerate(rows, len(previous)):
        assert row['item_id'] == order[i]['item_id']
        validate(by[row['item_id']], row)
        family = canonical[order[i]['family_id']]
        next_seen = advance(seen, family, row['decision'])
        r = dict(row, rank=i+1, family_id=order[i]['family_id'], at=now(),
                 reviewer='main agent', model_outcomes_used=False, receipt_version=2,
                 writer_version=4, canonical_family_id_at_review=family,
                 increments_independent_family_count=len(next_seen) > len(seen),
                 original_receipt_sha256=sha(path),
                 alias_supplements_sha256={str(p): sha(p) for p in supplements},
                 amendment='audit/atom_count_user_amendment_v2.json')
        if r['decision'] == 'ACCEPT':
            r['equal_evidence_rendering'] = rendering(by[r['item_id']], r['e_star_atoms'])
        prepared.append(r)
        seen = next_seen
    for r in prepared:
        save(ROOT/'audit/reviews/mathvision_v2'/f'{r["rank"]:04d}_{r["item_id"]}.json', r)
        with (ROOT/'audit/eligibility_log_v2.jsonl').open('a') as f:
            f.write(json.dumps(r, ensure_ascii=False)+'\n')
    print('SCREENED', len(previous)+len(rows), 'INDEPENDENT_ACCEPTED', len(seen),
          'ACCEPTED_SOURCE_RECEIPTS', sum(r['decision']=='ACCEPT' for r in previous+prepared))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True)
    commit(parser.parse_args().path)
