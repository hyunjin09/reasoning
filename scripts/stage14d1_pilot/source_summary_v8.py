"""Summarize frozen source reviews without loading solver answers or golds."""
from collections import Counter
from scripts.stage14d1_pilot.common import P, load, save, sha, now


def main():
    design = load(P/'manifests/resumption_v8_design.json')
    review = load(P/'annotations/query_review_complete.json')
    assert review['families'] == 72 and review['final_answers_hidden']
    for path, digest in review['files'].items():
        assert sha(path) == digest
    selected = {r['item_id'] for r in load(P/'protocol/offline_review_selection.json')['selected']}
    cases = []
    for item, path in sorted(design['source_states'].items(), key=lambda x: int(x[0])):
        s = load(path)
        q = load(P/'annotations/query_only'/f'{item}.json')
        a = load(P/'annotations/address_only'/f'{item}.json')
        cases.append(dict(item_id=item, family_id=s['family_id'], state_path=path,
            query_status=s['query']['status'], query_transport_valid=s['query_valid'],
            query_transport_reason=s['query_reason'], query_label=q['label'],
            relevance=q['task_relevance'], already_present=q['already_supplied_or_tentatively_present'],
            source_frame_adequate=q['source_frame_adequate'], guessed_value=q['guessed_requested_value'],
            address_transport_valid=s['address_valid'], address_label=a['label'],
            crop_count=len(s['views']['paths'])-1, read_aliases=s['read_aliases'],
            logical_continuations=s['logical_continuations'], fixed_readout_sample=item in selected))
    readouts=[]
    for item in sorted(selected, key=int):
        p=P/'annotations/readouts'/f'{item}.json'; r=load(p)
        assert r['original_image_inspected'] and r['final_answers_hidden']
        for record in r['records']:
            if record['generation_path']:
                assert sha(record['generation_path'])==record['generation_sha256']
            readouts.append(dict(item_id=item, family_id=r['family_id'], annotation=str(p), **record))
    by_arm={}
    for arm in ['G','Q','QI','QIA','QGL']:
        rs=[r for r in readouts if r['arm']==arm]
        assert len(rs)==24
        by_arm[arm]=dict(families=24,status_counts=dict(Counter(r['status'] for r in rs)),
            explicit_source_correct=sum(r['source_fact_correct'] is True for r in rs),
            explicit_source_wrong=sum(r['source_fact_correct'] is False for r in rs),
            source_correctness_unknown=sum(r['source_fact_correct'] is None for r in rs),
            demand_answered=sum(r['demand_answered'] is True for r in rs),
            new_correct_visual_information=sum(r['source_fact_correct'] is True and r['new_visual_information'] is True for r in rs),
            helper_aliases=sum(r['alias_of'] is not None for r in rs))
    out=dict(at=now(),families=72,source_only=True,solver_finals_opened=False,
        query_status_counts=dict(Counter(r['query_status'] for r in cases)),
        query_transport_valid=sum(r['query_transport_valid'] for r in cases),
        query_label_counts=dict(Counter(r['query_label'] for r in cases)),
        query_fully_relevant=sum(r['relevance']=='yes' for r in cases),
        query_relevance_counts=dict(Counter(r['relevance'] for r in cases)),
        address_label_counts=dict(Counter(r['address_label'] for r in cases)),
        address_transport_valid=sum(r['address_transport_valid'] for r in cases),
        local_views=sum(r['crop_count']>0 for r in cases),
        fixed_readout_sample_by_arm=by_arm,cases=cases,readouts=readouts,
        limitations=['Single AI reviewer; prior source exposure; no independent reliability estimate.',
            'Correct explicit text is not proof of fresh visual use; Q helper has no additional image, but Q solver remains image-conditioned.',
            'Absent/ambiguous/abstaining readouts are not classified as explicitly wrong facts.',
            'Fixed readout sample is source-stratified; additional flagged cases must remain a separate descriptive panel.',
            'Labels concern current query target, not automatically the historical source-selected E* opportunity.'])
    save(P/'analysis/source_review_summary_v8.json',out)
    print({k:v for k,v in out.items() if k not in ('cases','readouts')})

if __name__=='__main__': main()
