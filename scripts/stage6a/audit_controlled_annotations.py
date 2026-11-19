"""Check reviewed prefixes, native quotes and genuine intervening-source refreshes."""
import json
from collections import Counter,defaultdict
from scripts.stage6a.inventory import OUT
from scripts.stage6a.source_annotations import validate_prefix_membership
from visual_reasoning.stage6a.semantic import reviewed_visual_correctness


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    annotations=load(OUT/'traces/controlled_demand_annotations.jsonl')
    raw={r['event_id']:r['raw_decoded_response'] for r in load(OUT/'traces/controlled_native_index.jsonl')}
    reviews=load(OUT/'traces/controlled_manual_reviews.jsonl')
    native=defaultdict(list)
    for r in load(OUT/'traces/controlled_reasoning_spans.jsonl'):
        if r['section']=='reasoning':native[r['event_id']].append(r)
    manual=load(OUT/'traces/c1_manual_semantic_prefix.jsonl');by_base=defaultdict(list)
    for row in manual:by_base[row['base_id']].append(row)
    original=set(json.loads((OUT/'config/c1_secondary_sources.json').read_text()))
    remaining=json.loads((OUT/'config/c1_secondary_remaining_annotation_scope.json').read_text())
    validate_prefix_membership(by_base,original,remaining['base_ids'],complete=remaining['status']=='COMPLETE')
    for base,rows in by_base.items():
        expected=native[rows[0]['event_id']][:20]
        assert [r['span_id'] for r in rows]==[r['span_id'] for r in expected]
        for actual,source in zip(rows,expected):assert actual['text']==source['text']
    baseline_checks=0
    for review in load(OUT/'c1_diagram_stress/intact_local_claim_review.jsonl'):
        if review['membership_status']!='eligible':continue
        matches=[r for r in by_base.get(review['base_id'],[])
            if r['char_start']<review['char_end']<=r['char_end']]
        if not matches:continue
        baseline_checks+=1
        expected_truth=reviewed_visual_correctness([review])
        assert any(c['source_id']=='T' and reviewed_visual_correctness([c])==expected_truth
            for c in matches[0]['source_claims']),('Prefix erased reviewed baseline T claim',review['base_id'],matches[0]['span_id'])
    (OUT/'audit/c1_prefix_baseline_claim_consistency.json').write_text(json.dumps(dict(
        status='PASS',checked_baseline_claims=baseline_checks,issues=[],
        normalization='INCORRECT and scoped INCORRECT_* role labels agree; literal truth remains separate.'),indent=2)+'\n')
    groups=defaultdict(list)
    for r in annotations:groups[r['event_id']].append(r)
    refresh_sources=0;claims=0;cross_span=0;observed=set()
    for eid,rows in groups.items():
        assert len(rows)==len(native[eid])
        for i,row in enumerate(rows):
            assert row['text']==native[eid][i]['text']
            if row['demand_changed'] is not None:
                assert i>0 and not row['unresolved'] and not rows[i-1]['unresolved']
                assert row['demand_changed']==(row['demanded_sources']!=rows[i-1]['demanded_sources'])
            for source,prior in row['prior_explicit_access'].items():
                if prior is True:
                    evidence=row['prior_explicit_evidence'][source]
                    assert any(r['span_id']==evidence['span_id'] and r['text']==evidence['text'] and source in r['explicit_visual_claim_sources'] for r in rows[:i])
            for source,role in row['source_temporal_roles'].items():
                if role!='REFRESH':continue
                refresh_sources+=1;assert row['prior_explicit_access'][source] is True
                previous=[j for j,r in enumerate(rows[:i]) if not r['unresolved'] and source in r['demanded_sources']]
                start=max(previous) if previous else -1
                assert any(not r['unresolved'] and r['demanded_sources'] and source not in r['demanded_sources'] for r in rows[start+1:i]),(eid,row['span_id'],source)
            for claim in row.get('source_claims',[]):
                if 'span_assignment' in claim:
                    assert raw[eid][claim['char_start']:claim['char_end']]==claim['quote']
                    assert row['char_start']<claim['char_end']<=row['char_end']
                    key=(eid,claim['source_id'],claim['char_start'],claim['char_end'])
                    assert key not in observed,'Each reviewed claim must appear exactly once'
                    observed.add(key);cross_span+=claim['claim_crosses_span_boundary']
                else:assert claim['quote'] in row['text']
                claims+=1
    expected={(r['event_id'],c['source_id'],c['char_start'],c['char_end']) for r in reviews if r['event_id'] in groups for c in r['source_claims']}
    assert observed==expected,('Missing or duplicated reviewed claims',expected-observed,observed-expected)
    report=dict(status='PASS',events=len(groups),reasoning_spans=len(annotations),
        complete_manual_prefix_bases=len(by_base),manual_prefix_spans=len(manual),
        baseline_claims_preserved_in_prefix=baseline_checks,
        exact_native_source_claims=claims,validated_source_refreshes=refresh_sources,
        all_controlled_review_claims_assigned_once=len(observed),cross_span_reviewed_claims=cross_span,
        temporal_roles=dict(Counter(r['first_reuse_refresh'] for r in annotations)),
        limitations=['Manual prefix scope covers localized numeric facts, not every geometric property or the whole trajectory.',
            'Outside reviewed claims, conservative rule coverage and unresolved states are reported explicitly.',
            'Prior explicit access means a prior source-linked utterance; it is not evidence of causal visual use.'])
    (OUT/'audit/controlled_annotation_integrity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
