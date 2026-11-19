"""Versioned reporting repair for sealed, possibly unresolvable extractions.

No scorer, dose ordering or scientific gate changes. Unresolved outcomes receive
no accuracy credit and remain unresolved in paired transitions. The caller must
validate the extraction seal before setting extraction_review_closed.
"""
from visual_reasoning.stage8c.analysis_fp32 import summarize, transitions


def development_decision(arms, metadata, *, extraction_review_closed=False):
    if set(arms)!={1.,1.25,1.5,2.} or any(len(a)!=128 for a in arms.values()):
        raise ValueError('Four complete frozen128-item arms required')
    if any(set(rows) != set(metadata) for rows in arms.values()):
        raise ValueError('Frozen paired metadata membership required')
    summaries={gain:summarize(rows) for gain,rows in arms.items()}
    if not extraction_review_closed:
        return dict(status='awaiting_blind_extraction',dose=None,
                    reason='Resolve/declare unresolvable extraction before final dose gates; no automatic test launch')
    base=summaries[1.];candidates=[];details={}
    for gain in (1.25,1.5,2.):
        s=summaries[gain];tr=transitions(arms[1.],arms[gain]);change=s['accuracy']-base['accuracy']
        strata={}
        for subject in sorted({r['subject'] for r in metadata.values()}):
            ids=[i for i,r in metadata.items() if r['subject']==subject]
            diff=sum(int(arms[gain][i]['correct'] is True)-int(arms[1.][i]['correct'] is True) for i in ids)/len(ids)
            strata[subject]=dict(n=len(ids),delta=diff,severe_harm=len(ids)>=15 and diff<-.10)
        severe=sum(v['severe_harm'] for v in strata.values())
        major=[v for v in strata.values() if v['n']>=15]
        positive=[v for v in strata.values() if v['delta']>0]
        other_major=[v for v in major if not positive or v is not positive[0]]
        narrow=len(positive)==1 and len(other_major)>=2 and all(v['delta']<0 for v in other_major)
        reasons=[]
        if change<=0:reasons.append('no_positive_accuracy')
        if tr['CtoW']>=tr['WtoC']:reasons.append('no_positive_rescue_balance')
        if s['cap_rate']-base['cap_rate']>.10:reasons.append('cap_increase_gt10pp')
        if s['median_reasoning_tokens']>1.5*base['median_reasoning_tokens'] and change<.02:
            reasons.append('length_increase_gt50pct_without_2pp_gain')
        if narrow:reasons.append('narrow_benefit_with_major_subtype_degradation')
        details[gain]=dict(summary=s,transitions=tr,delta=change,subtypes=strata,no_go_reasons=reasons)
        if not reasons:
            candidates.append(((-s['accuracy'],-(tr['WtoC']-tr['CtoW']),
                 s['cap_rate']-base['cap_rate'],s['median_reasoning_tokens']-base['median_reasoning_tokens'],gain),gain))
    chosen=min(candidates)[1] if candidates else None
    return dict(status='pass' if chosen else 'stop_dev_no_go',dose=chosen,details=details,
                baseline=base,test_launch_authorized=bool(chosen))
