"""Source-only review packets and strict dual-review eligibility; no model outputs."""
import argparse
from collections import Counter
from scripts.stage11c.common import ROOT, SEED, load, save, sha, now
from scripts.stage11c.protocol import stratified

LABELS = {'SUFFICIENT', 'INSUFFICIENT', 'AMBIGUOUS'}
QUALITY = ('facts_true', 'atomic_and_minimal', 'no_answer_leak', 'question_requires_image')


def review_pass(row):
    assert row['sufficiency'] in LABELS
    assert all(type(row[k]) is bool for k in QUALITY)
    return row['sufficiency'] == 'SUFFICIENT' and all(row[k] for k in QUALITY)


def agreement(a, b):
    assert len(a) == len(b)
    n = len(a)
    if not n:
        return dict(n=0, agreement=None, kappa=None)
    observed = sum(x == y for x, y in zip(a, b))/n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[k]*cb[k] for k in set(ca)|set(cb))/n**2
    return dict(n=n, agreement=observed, kappa=(observed-expected)/(1-expected)
                if expected < 1 else None, prevalence_a=dict(ca), prevalence_b=dict(cb))


def proposal(round_id):
    sources = {r['item_id']: r for r in load(ROOT/'packets/evidence_source.json')['rows']}
    rows, hashes = [], {}
    for reviewer in ['a', 'b']:
        path = ROOT/'annotations'/f'construction_round{round_id}_{reviewer}.json'
        packet = ROOT/'packets'/f'construction_round{round_id}_{reviewer}.json'
        construction = load(path)
        assert construction['sealed'] and construction['model_outcomes_opened'] is False
        assigned = load(packet)['rows']
        assert {r['item_id'] for r in construction['rows']} == {r['item_id'] for r in assigned}
        assert len(construction['rows']) == len(assigned)
        for c in construction['rows']:
            assert c['image_inspected'] and 0 <= len(c['facts']) <= 4
            assert all(isinstance(f, str) and f.strip() for f in c['facts'])
            s = sources[c['item_id']]
            assert c['source_order'] == s['source_order']
            rows.append(dict(s, facts=c['facts'], evidence_type=c['evidence_type'],
                             downstream_depth=c['downstream_depth']))
        hashes[reviewer] = sha(path)
    rows.sort(key=lambda r: r['source_order'])
    assert len({r['item_id'] for r in rows}) == len(rows)
    dest = ROOT/'packets'/f'review_round{round_id}.json'
    save(dest, dict(at=now(), frozen=True, round_id=round_id, model_outcomes_opened=False,
                   construction_sha256=hashes, rows=rows,
                   note='Identical proposals for two separate reviews. Constructor judgments/reasons omitted.'))
    print('REVIEW_PACKET', dest, len(rows), sha(dest))


def aggregate(round_id):
    packet = ROOT/'packets'/f'review_round{round_id}.json'
    proposals = load(packet)['rows']
    reviews, hashes = {}, {}
    for reviewer in ['a', 'b']:
        path = ROOT/'annotations'/f'review_round{round_id}_{reviewer}.json'
        review = load(path)
        assert review['sealed'] and review['model_outcomes_opened'] is False
        assert review['proposal_sha256'] == sha(packet)
        assert len(review['rows']) == len(proposals)
        reviews[reviewer] = {r['item_id']: r for r in review['rows']}
        assert set(reviews[reviewer]) == {r['item_id'] for r in proposals}
        hashes[reviewer] = sha(path)
    excluded = set()
    for path in (ROOT/'audit').glob('source_alias_exclusions_v*.json'):
        excluded.update(r['item_id'] for r in load(path)['exclusions'])
    rows = []
    for p in proposals:
        a, b = [reviews[k][p['item_id']] for k in ['a', 'b']]
        assert a['image_inspected'] and b['image_inspected']
        assert a['family_id'] == b['family_id'] == p['family_id']
        pa, pb = review_pass(a), review_pass(b)
        rows.append(dict(p, eligible=bool(p['facts']) and pa and pb and p['item_id'] not in excluded,
                         source_alias_excluded=p['item_id'] in excluded,
                         review_a=a, review_b=b, quality_a=pa, quality_b=pb))
    reliability = {}
    for subset, selected in [('all', rows), ('nonempty', [r for r in rows if r['facts']])]:
        reliability[subset] = dict(
            sufficiency=agreement([r['review_a']['sufficiency'] for r in selected],
                                  [r['review_b']['sufficiency'] for r in selected]),
            quality=agreement([str(r['quality_a']) for r in selected],
                              [str(r['quality_b']) for r in selected]))
    dest = ROOT/'audit'/f'evidence_round{round_id}.json'
    save(dest, dict(at=now(), frozen=True, model_outcomes_opened=False, n=len(rows),
                   eligible=sum(r['eligible'] for r in rows), proposal_sha256=sha(packet),
                   reviews_sha256=hashes, reliability=reliability, rows=rows))
    print('ROUND', round_id, 'ELIGIBLE', sum(r['eligible'] for r in rows), '/', len(rows))
    print(reliability)


def next_round():
    rounds = sorted((ROOT/'audit').glob('evidence_round*.json'))
    assert rounds
    allrows = [r for path in rounds for r in load(path)['rows']]
    assert len({r['item_id'] for r in allrows}) == len(allrows)
    n, eligible = len(allrows), sum(r['eligible'] for r in allrows)
    assert n < 300 and eligible < 120
    assert sorted(r['source_order'] for r in allrows) == list(range(n))
    count = min(120, 120-eligible, 300-n)
    sources = load(ROOT/'packets/evidence_source.json')['rows']
    selected = sources[n:n+count]
    assert [r['source_order'] for r in selected] == list(range(n, n+count))
    round_id = len(rounds)+1
    for reviewer, subset in [('a', selected[:(count+1)//2]), ('b', selected[(count+1)//2:])]:
        save(ROOT/'packets'/f'construction_round{round_id}_{reviewer}.json',
             dict(at=now(), frozen=True, round_id=round_id, reviewer=reviewer,
                  model_outcomes_opened=False, previous_reviewed=n, previous_eligible=eligible,
                  prior_round_sha256={str(p): sha(p) for p in rounds}, rows=subset))
    print('ROUND', round_id, 'N', count, 'PREVIOUS_ELIGIBLE', eligible)


def freeze(review_decision):
    """Seal only after the source stop boundary and explicit reliability assessment."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    assert not list(ROOT.glob('native*/results/*/generation.json'))
    assert not list(ROOT.glob('oracle*/results/*/generation.json'))
    rounds = sorted((ROOT/'audit').glob('evidence_round*.json'))
    rows = [r for path in rounds for r in load(path)['rows']]
    assert len({r['item_id'] for r in rows}) == len(rows)
    assert sorted(r['source_order'] for r in rows) == list(range(len(rows)))
    eligible = [r for r in rows if r['eligible']]
    excluded = {r['item_id'] for p in (ROOT/'audit').glob('source_alias_exclusions_v*.json')
                for r in load(p)['exclusions']}
    assert not excluded.intersection(r['item_id'] for r in eligible), 'Apply every alias repair before sealing'
    assert len(eligible) == 120 or len(rows) == 300, 'Source annotation stop boundary not reached'
    decision = load(review_decision)
    assert decision['model_outcomes_opened'] is False
    assert decision['round_sha256'] == {str(p): sha(p) for p in rounds}
    assert decision['reliability_acceptable'], 'Resolve meaningful low agreement before sealing'
    reliability = {}
    for name, subset in [('all', rows), ('nonempty', [r for r in rows if r['facts']])]:
        reliability[name] = dict(
            sufficiency=agreement([r['review_a']['sufficiency'] for r in subset],
                                  [r['review_b']['sufficiency'] for r in subset]),
            quality=agreement([str(r['quality_a']) for r in subset],
                              [str(r['quality_b']) for r in subset]))
    save(ROOT/'stage11c_e_star_sufficiency_review.json', dict(at=now(), frozen=True,
        model_outcomes_opened=False, reviewed=len(rows), eligible=len(eligible),
        round_sha256={str(p): sha(p) for p in rounds}, original_reliability=reliability,
        reliability_decision_sha256=sha(review_decision),
        reviewer_limitation='Two independent model-agent semantic reviews, not human reliability. Each reviewer constructed one half before reviewing the identical whole proposal.',
        rows=rows))
    gold_path = ROOT/'stage11c_e_star_gold.parquet'
    assert not gold_path.exists()
    gold = [{k: r[k] for k in ['item_id', 'family_id', 'source_order', 'question', 'answer',
             'image', 'image_sha256', 'level', 'subject', 'major_subject', 'facts',
             'evidence_type', 'downstream_depth', 'eligible', 'source_alias_excluded']} for r in rows]
    pq.write_table(pa.Table.from_pylist(gold), gold_path)
    if len(eligible) < 64:
        primary, reserve = [], []
    else:
        primary = stratified(eligible, min(80, len(eligible)), SEED, 'primary',
                             ['major_subject', 'evidence_type'])
        ids = {r['item_id'] for r in primary}
        reserve = [r for r in eligible if r['item_id'] not in ids]
        assert len(reserve) <= 40
        if reserve:
            reserve = stratified(reserve, len(reserve), SEED, 'reserve', ['major_subject', 'evidence_type'])
    subsets = {name: [r['item_id'] for r in stratified(primary, n, SEED, name,
                ['major_subject', 'evidence_type'])] if primary else []
               for name, n in [('neutral', 24), ('cot', 48), ('secondary_native', 32)]}
    save(ROOT/'stage11c_primary_split.json', dict(at=now(), frozen=True, seed=SEED,
        status='READY' if primary else 'STOP_INSUFFICIENT_EVIDENCE', model_outcomes_opened=False,
        reviewed=len(rows), eligible=len(eligible), primary_n=len(primary), reserve_n=len(reserve),
        primary=primary, reserve=reserve, subsets=subsets,
        e_star_sha256=sha(gold_path), review_sha256=sha(ROOT/'stage11c_e_star_sufficiency_review.json'),
        original_source_manifest_sha256=sha(ROOT/'stage11c_heldout_source_manifest.json'),
        source_exclusion_sha256={str(p): sha(p) for p in (ROOT/'audit').glob('source_alias_exclusions_v*.json')}))
    print('SEALED', len(rows), 'REVIEWED', len(eligible), 'ELIGIBLE', len(primary), 'PRIMARY', len(reserve), 'RESERVE')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['proposal', 'aggregate', 'next', 'freeze'])
    p.add_argument('--round', type=int)
    p.add_argument('--review-decision')
    a = p.parse_args()
    if a.action == 'proposal':
        proposal(a.round)
    elif a.action == 'aggregate':
        aggregate(a.round)
    elif a.action == 'next':
        next_round()
    else:
        freeze(a.review_decision)
