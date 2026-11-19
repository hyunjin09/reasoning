"""Freeze source-only evidence and evaluate necessary discovery conditions."""
from collections import Counter
from copy import deepcopy
import pandas as pd
from scripts.stage11b.common import ROOT, load, save, sha, now
from scripts.stage11b.protocol import CANDIDATES, in_stratum
from scripts.stage11b.source_gate import source_possible
from scripts.stage11b.summarize_sufficiency import accepted, agreement, FIELDS


def read_reviews(packet_path, stem):
    packet = {r['item_id']: r for r in load(packet_path)['rows']}
    reviews = {}
    for who in ['a', 'b']:
        x = load(ROOT/'annotations'/f'{stem}_{who}.json')
        assert x['sealed'] and x['model_outcomes_opened'] is False
        assert x['proposal_sha256'] == sha(packet_path)
        rr = {r['item_id']: r for r in x['rows']}
        assert len(rr) == len(x['rows']) and set(rr) == set(packet)
        for i, r in rr.items():
            assert r['family_id'] == packet[i]['family_id'] and r['image_inspected']
            assert r['sufficiency'] in ['SUFFICIENT', 'INSUFFICIENT', 'AMBIGUOUS']
            assert all(isinstance(r[k], bool) for k in FIELDS[1:])
        reviews[who] = rr
    return packet, reviews


def main():
    packet, raw = read_reviews(ROOT/'packets/discovery_sufficiency.json', 'discovery_sufficiency')
    repairs, revised = read_reviews(ROOT/'packets/discovery_sufficiency_repair_v1.json', 'discovery_sufficiency_repair')
    construction = {r['item_id']: r for r in load(ROOT/'audit/discovery_construction_key.json')['rows']}
    rows = []
    for i, original in packet.items():
        r = deepcopy(construction[i])
        proposal = repairs.get(i, original)
        reviews = revised if i in repairs else raw
        passed = bool(proposal['facts']) and all(accepted(reviews[w][i]) for w in ['a', 'b'])
        r['facts'] = proposal['facts']
        r['eligible'] = passed
        r['raw_eligibility'] = r['eligibility']
        if passed:
            r['eligibility'] = 'E_STAR_ELIGIBLE'
        elif proposal['facts'] or r['eligibility'] == 'E_STAR_ELIGIBLE':
            r['eligibility'] = 'EXCLUDED_REVIEW_UNRESOLVED'
        elif any(reviews[w][i]['sufficiency'] == 'AMBIGUOUS' for w in ['a', 'b']):
            r['eligibility'] = 'AMBIGUOUS'
        r['final_sufficiency'] = 'SUFFICIENT' if passed else None
        r['review_version'] = 'repair_v1' if i in repairs else 'original'
        r['final_review_a'] = reviews['a'][i]
        r['final_review_b'] = reviews['b'][i]
        r['subject'] = original['subject']
        r['level'] = original['level']
        r['fact_count'] = len(r['facts'])
        assert not passed or 1 <= len(r['facts']) <= 4
        rows.append(r)
    assert len(rows) == len({r['family_id'] for r in rows}) == 128
    evidence_path = ROOT/'annotations/discovery_evidence_final.json'
    save(evidence_path, dict(at=now(), sealed=True, model_outcomes_opened=False, rows=rows,
        rule='Nonempty one-to-four-fact proposal passes both independent semantic quality reviews; unresolved cases excluded',
        repair_passes=1, raw_reviews_preserved=True))
    flat = [dict(item_id=r['item_id'], family_id=r['family_id'], subject=r['subject'], level=r['level'],
        eligibility=r['eligibility'], eligible=r['eligible'], fact_count=r['fact_count'],
        reasoning_depth_bin=r['reasoning_depth_bin'], facts=r['facts'], review_version=r['review_version']) for r in rows]
    path = ROOT/'stage11b_discovery_e_star_eligibility.parquet'
    assert not path.exists()
    pd.DataFrame(flat).to_parquet(path, index=False)
    strata = []
    for rule in CANDIDATES:
        rr = [r for r in rows if in_stratum(r, rule)]
        ee = [r for r in rr if r['eligible']]
        types = Counter(r['facts'][0]['evidence_type'] for r in ee)
        subjects = Counter(r['subject'] for r in ee)
        depth = sum(r['reasoning_depth_bin'] in ['2-3', '4+'] for r in ee)
        diversity = dict(two_evidence_types=sum(v >= 3 for v in types.values()) >= 2,
            no_subject_dominates=bool(ee) and max(subjects.values())/len(ee) <= .6,
            nontrivial_depth=bool(ee) and depth/len(ee) >= .5)
        strata.append(dict(rule=rule, n=len(rr), eligible=len(ee), eligibility_rate=len(ee)/len(rr),
            **source_possible(len(rr), len(ee), all(diversity.values())), diversity=diversity,
            evidence_types=dict(types), subject_counts=dict(subjects), depth_ge2=depth,
            model_accuracy=None, forward_discordance=None, model_outcomes_opened=False))
    save(ROOT/'audit/source_only_necessary_gate.json', dict(at=now(), strata=strata,
        any_source_feasible=any(r['possible'] for r in strata), evidence_sha256=sha(evidence_path),
        proof='Forward discordance <= Thinking correct <= .75 * eligible; 12 forward therefore requires at least16 eligible. This is necessary, never sufficient, for the original GO gate.',
        model_outcomes_opened=False))
    repair_agreement = {k: agreement([revised['a'][i][k] for i in repairs], [revised['b'][i][k] for i in repairs]) for k in FIELDS}
    save(ROOT/'stage11b_e_star_sufficiency_review.json', dict(at=now(), status='COMPLETE_DISCOVERY_ONLY',
        raw_summary=load(ROOT/'audit/raw_sufficiency_summary.json'), repair_agreement=repair_agreement,
        final_eligible=sum(r['eligible'] for r in rows), final_categories=dict(Counter(r['eligibility'] for r in rows)),
        unresolved_cases=[r['item_id'] for r in rows if r['eligibility']=='EXCLUDED_REVIEW_UNRESOLVED'],
        heldout_review_status='NOT_RUN', model_outcomes_opened=False,
        caveat='Two model-agent reviews with own prior construction exposure; not human reliability. Raw nonempty sufficiency kappa is prevalence-sensitive and reported separately; repair does not replace raw agreement.'))
    print('SEALED', sum(r['eligible'] for r in rows), 'eligible of128')
    for r in strata:
        print(r['rule']['id'], r['eligible'], '/', r['n'], 'SOURCE_POSSIBLE', r['possible'])


if __name__ == '__main__':
    main()
