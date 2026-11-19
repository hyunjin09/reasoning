"""Trajectory-equal descriptive census; no causal effects or significance search."""
import os,json
from collections import Counter
import numpy as np
import pandas as pd
from scripts.stage10b.common import ROOT,load,save,sha,now
from scripts.stage10b.protocol import trajectory_counts,decision,wilson

NEGATIVES=['NEW_DEMAND_NO_REACCESS','B_ALREADY_TEXTUALIZED','NO_TEXT_INTERVAL',
           'ATTENTION_ONLY','TARGET_AMBIGUOUS','TRACE_TOO_SHORT','ROUTING_DATA_MISSING']


def table(rows,path):
    # Explicit JSON strings retain heterogeneous evidence without implicit Arrow coercion.
    if not rows:
        pd.DataFrame(columns=['event_id','trajectory_id','record_kind','category']).to_parquet(path,index=False)
        return
    out=[]
    for r in rows:
        out.append({k:json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(list,dict,tuple)) else v for k,v in r.items()})
    pd.DataFrame(out).to_parquet(path,index=False)


def classify(e):
    if e['semantic_clean']:return 'CLEAN' if e['C5'] else e['classification']
    if e['prior_availability']=='SUFFICIENT':return 'B_ALREADY_TEXTUALIZED'
    if e['prior_availability'] in ('PARTIAL','AMBIGUOUS'):return 'TARGET_AMBIGUOUS'
    if not e['C1']:return 'NO_RESOLVED_VISUAL_A'
    if not e['C2']:return 'NO_TEXT_INTERVAL'
    if not e['C3']:return 'NO_NEW_REQUIRED_DEMAND'
    raise ValueError(e['event_id'])


def inference(ids,events):
    selected=[e for e in events if e['trajectory_id'] in set(ids)]
    result=trajectory_counts(ids,selected);primary=result.pop('primary')
    unresolved={e['trajectory_id'] for e in selected if e['semantic_clean'] and not e['C5']
                and e['classification'] in ('ROUTING_DATA_MISSING','TARGET_AMBIGUOUS')}-set(primary)
    observed={e['trajectory_id'] for e in selected if e['semantic_clean']}-unresolved
    lags=[e['lag'] for e in primary.values()]
    result.update(primary_event_ids=[e['event_id'] for e in primary.values()],
        unresolved_C5_trajectories=sorted(unresolved),
        missing_data_yield_bounds=[result['clean']/len(ids),(result['clean']+len(unresolved))/len(ids)] if ids else None,
        observed_C5_only=wilson(result['clean'],len(observed)),
        timing=dict(n=len(lags),median=float(np.median(lags)) if lags else None,
                    q25_q75=np.quantile(lags,[.25,.75]).tolist() if lags else None,
                    offsets=sorted(lags),histogram={str(i):lags.count(i) for i in range(32)}),
        taxonomy={k:sum(e['taxonomy']==k for e in primary.values()) for k in ('S1','S2','S3')},
        target_types=dict(Counter(e['target_type'] for e in primary.values())))
    return result


def main():
    assert os.environ.get('SLURM_JOB_ID')
    cp=ROOT/'stage10b_corpus_manifest.json';sp=ROOT/'audit/semantic_adjudication_frozen.json'
    rp=ROOT/'audit/reaccess_adjudicated.json';ap=ROOT/'stage10b_annotation_agreement.json'
    corpus=load(cp);semantic=load(sp);routing=load(rp);agree=load(ap)
    assert semantic['sealed'] and routing['sealed'] and routing['semantic_sha256']==sha(sp)
    rows=[r for r in corpus['rows'] if r['eligible']];by={r['trajectory_id']:r for r in rows}
    measured={r['event_id']:r for r in routing['rows']}
    assert set(measured)=={r['event_id'] for r in semantic['events']}
    events=[]
    for e in semantic['events']:
        r=measured[e['event_id']]
        assert r['trajectory_id']==e['trajectory_id']
        item=dict(e,**{k:v for k,v in r.items() if k not in e})
        item.update(C5=r['C5'],lag=r['lag'],dataset=by[e['trajectory_id']]['dataset'],
                    reasoning_tokens=by[e['trajectory_id']]['reasoning_tokens'])
        item['category']=classify(item);events.append(item)
    all_ids=list(by);pooled=inference(all_ids,events)
    dataset={d:inference([r['trajectory_id'] for r in rows if r['dataset']==d],events) for d in ('MathVision','MathVerse')}
    primary_ids=set(pooled['primary_event_ids']);primary=[e for e in events if e['event_id'] in primary_ids]
    primary_tids={e['trajectory_id'] for e in primary}
    for e in events:e['primary_for_trajectory']=e['event_id'] in primary_ids
    candidates=[e for e in events if e['category']=='CLEAN']
    most_complex={}
    for tid in primary_tids:
        labels={e['taxonomy'] for e in candidates if e['trajectory_id']==tid}
        most_complex[tid]=next(k for k in ('S2','S3','S1') if k in labels)
    negatives=[dict(e,record_kind='event') for e in events if e['category']!='CLEAN']
    frozen_trajs={r['trajectory_id']:r for r in semantic['trajectories']}
    for tid,r in by.items():
        if tid in primary_tids:continue
        own=[e for e in events if e['trajectory_id']==tid]
        new=[e for e in own if e['semantic_clean']]
        if new:
            priority=['ROUTING_DATA_MISSING','TARGET_AMBIGUOUS','ATTENTION_ONLY','NEW_DEMAND_NO_REACCESS']
            category=next(c for c in priority if any(e['category']==c for e in new))
        else:category=frozen_trajs[tid]['negative_category']
        negatives.append(dict(record_kind='trajectory',trajectory_id=tid,dataset=r['dataset'],category=category,
                              reason=frozen_trajs[tid]['reason'],events=[e['event_id'] for e in own]))
    negative_counts=Counter(r['category'] for r in negatives if r['record_kind']=='trajectory')
    for c in NEGATIVES:negative_counts.setdefault(c,0)
    assert sum(negative_counts.values())+pooled['clean']==len(rows)
    completion={label:inference([r['trajectory_id'] for r in rows if label==('capped' if r['at_length_cap'] else 'normal_eos' if r['normal_eos'] else 'other')],events)
                for label in ('normal_eos','capped','other')}
    boundaries=np.quantile([r['reasoning_tokens'] for r in rows],[.25,.5,.75])
    length={str(q+1):inference([r['trajectory_id'] for r in rows if int(np.searchsorted(boundaries,r['reasoning_tokens'],side='right'))==q],events) for q in range(4)}
    # Removing short intervals is a descriptive guardrail sensitivity, not a new primary rule.
    long_events=[dict(e,semantic_clean=e['semantic_clean'] and e['intervening_tokens']>=24) for e in events]
    sensitivity=inference(all_ids,long_events)
    result=dict(at=now(),independent_unit='one conservative problem/image trajectory',pooled=pooled,datasets=dataset,
                flow=dict(eligible=len(rows),any_C3=len({e['trajectory_id'] for e in events if e['C3']}),
                          any_C3_C4=len({e['trajectory_id'] for e in events if e['C3'] and e['C4']}),
                          C1_C4=pooled['new_demand'],C1_C5=pooled['clean']),
                primary_negative_categories=dict(negative_counts),completion=completion,
                secondary_taxonomy_any_clean_event=dict(Counter(most_complex.values())),
                secondary_taxonomy_note='One count per trajectory using strongest annotated topology among its clean events (S2 before S3 before S1). E5 primary taxonomy remains the earliest clean event.',
                length_quartile_cutpoints=boundaries.tolist(),length_quartiles=length,
                minimum24token_interval_sensitivity=sensitivity,
                event_count=len(events),clean_event_count=len(candidates),
                semantic_candidate_event_count=sum(e['semantic_clean'] for e in events),
                sources_sha256={str(p):sha(p) for p in (cp,sp,rp,ap)},
                interpretation='Operational explicit-demand candidate yield; passive association is not causal reopening.',
                missingness='Bounds count unresolved C5 at the trajectory level; not a confidence interval. Missing values never count as observed absence.',
                annotation_limit='Independent model-agent reviews with passage screening on long negatives; not exhaustive human token annotation.')
    save(ROOT/'stage10b_yield_inference.json',result)
    counts={d:v['clean'] for d,v in dataset.items()};status=decision(pooled['clean'],counts,counts,agree['acceptable_for_strong_go'])
    recommendations={
        'STRONG_GO':'Run a bounded causal reopening experiment on the frozen clean recurrent-demand cohort, testing whether visual necessity and source-specific causal dependence rise after the new B demand.',
        'LIMITED_GO':'Run only a small causal pilot on the cleanest frozen cases; do not promote recurrence to a headline claim yet.',
        'NO_GO':'Stop the recurrent-phase branch and finalize the paper around the established visual-dependent to text-sufficient transition plus dynamic source retargeting as a separate result.'}
    save(ROOT/'stage10b_go_nogo_decision.json',dict(at=now(),decision=status,clean_independent_trajectories=pooled['clean'],
        dataset_counts=counts,canonical_source_counts=counts,acceptable_agreement=agree['acceptable_for_strong_go'],
        maximum_source_share=max(counts.values())/pooled['clean'] if pooled['clean'] else None,
        recommendation=recommendations[status],recommendation_count=1,followup_launched=False,
        unresolved_C5_trajectories=pooled['unresolved_C5_trajectories'],
        inference_sha256=sha(ROOT/'stage10b_yield_inference.json'),
        interpretation_boundary='No causal reopening/complete recurrent phase-cycle claim. Failure to reach GO is not mechanism impossibility.'))
    independent=load(ROOT/'audit/semantic_independent_passes_frozen.json')
    annotations=[]
    for who,reviews in independent['reviews'].items():
        annotations.extend(dict(r,annotation_pass=who,record_kind='trajectory') for r in reviews.values())
    annotations.extend(dict(r,annotation_pass='adjudicated',record_kind='trajectory') for r in semantic['trajectories'])
    annotations.extend(dict(r,annotation_pass='adjudicated',record_kind='event') for r in semantic['events'])
    table(annotations,ROOT/'stage10b_semantic_annotations.parquet')
    table(routing['rows'],ROOT/'stage10b_reaccess_annotations.parquet')
    table(candidates,ROOT/'stage10b_candidate_events.parquet')
    table(negatives,ROOT/'stage10b_negative_cases.parquet')
    save(ROOT/'audit/analyzed_events.json',dict(at=now(),rows=events))
    print(status,pooled['clean'],'clean/',len(rows),'eligible;',pooled['new_demand'],'semantic;',len(pooled['unresolved_C5_trajectories']),'unresolved C5',flush=True)


if __name__=='__main__':main()
