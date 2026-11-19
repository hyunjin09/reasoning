"""Predeclared item/family paired inference and development dose guards."""
from collections import Counter
import numpy as np
from scipy.stats import binomtest


def transitions(baseline, arm):
    if set(baseline) != set(arm):
        raise ValueError('Paired complete item membership required')
    counts = Counter()
    for item in baseline:
        a,b = baseline[item]['correct'], arm[item]['correct']
        counts['unresolved' if a is None or b is None else
               ('C' if a else 'W')+'to'+('C' if b else 'W')] += 1
    return {k:counts[k] for k in ('WtoC','CtoW','CtoC','WtoW','unresolved')}


def summarize(rows):
    rows=list(rows.values())
    n=len(rows)
    return dict(n=n,correct=sum(r['correct'] is True for r in rows),
        unresolved=sum(r['correct'] is None for r in rows),
        accuracy=sum(r['correct'] is True for r in rows)/n,
        eos_rate=np.mean([r['normal_eos'] for r in rows]).item(),
        cap_rate=np.mean([r['at_length_cap'] for r in rows]).item(),
        mean_reasoning_tokens=np.mean([r['reasoning_tokens'] for r in rows]).item(),
        median_reasoning_tokens=np.median([r['reasoning_tokens'] for r in rows]).item(),
        mean_generated_tokens=np.mean([r['tokens'] for r in rows]).item(),
        interventions=sum(r['actual_interventions'] for r in rows),
        elapsed_seconds=sum(r['elapsed_seconds'] for r in rows))


def paired_inference(baseline, arm, families, draws=20000):
    ids=sorted(baseline)
    if set(ids)!=set(arm) or set(ids)!=set(families):
        raise ValueError('Exactly paired items and family IDs required')
    delta=np.array([int(arm[i]['correct'] is True)-int(baseline[i]['correct'] is True) for i in ids])
    rng=np.random.default_rng(820260921)
    item_means=[];family_means=[]
    fids=sorted(set(families.values()))
    sums=np.array([sum(delta[k] for k,i in enumerate(ids) if families[i]==f) for f in fids])
    sizes=np.array([sum(families[i]==f for i in ids) for f in fids])
    for offset in range(0,draws,1000):
        n=min(1000,draws-offset)
        item_means.extend(delta[rng.integers(0,len(ids),size=(n,len(ids)))].mean(1))
        sampled=rng.integers(0,len(fids),size=(n,len(fids)))
        family_means.extend(sums[sampled].sum(1)/sizes[sampled].sum(1))
    tr=transitions(baseline,arm);disc=tr['WtoC']+tr['CtoW']
    return dict(delta_accuracy=float(delta.mean()),item_ci95=np.quantile(item_means,[.025,.975]).tolist(),
        family_ci95=np.quantile(family_means,[.025,.975]).tolist(),items=len(ids),families=len(fids),
        transitions=tr,mcnemar_two_sided_p=binomtest(tr['WtoC'],disc,.5).pvalue if disc else 1.,
        bootstrap_draws=draws,seed=820260921,unresolved_correct_credit=False)


def development_decision(arms, metadata):
    if set(arms)!={1.,1.25,1.5,2.} or any(len(a)!=128 for a in arms.values()):
        raise ValueError('Four complete frozen128-item arms required')
    summaries={gain:summarize(rows) for gain,rows in arms.items()}
    if any(s['unresolved'] for s in summaries.values()):
        return dict(status='awaiting_blind_extraction',dose=None,
                    reason='Resolve/declare unresolvable extraction before final dose gates; no automatic test launch')
    base=summaries[1.];candidates=[];details={}
    for gain in (1.25,1.5,2.):
        s=summaries[gain];tr=transitions(arms[1.],arms[gain]);change=s['accuracy']-base['accuracy']
        strata={}
        for subject in sorted({r['subject'] for r in metadata.values()}):
            ids=[i for i,r in metadata.items() if r['subject']==subject]
            diff=sum(int(arms[gain][i]['correct'])-int(arms[1.][i]['correct']) for i in ids)/len(ids)
            strata[subject]=dict(n=len(ids),delta=diff,severe_harm=len(ids)>=15 and diff<-.10)
        severe=sum(v['severe_harm'] for v in strata.values())
        major=[v for v in strata.values() if v['n']>=15]
        positive=[v for v in strata.values() if v['delta']>0]
        other_major=[v for v in major if not positive or v is not positive[0]]
        narrow=len(positive)==1 and bool(other_major) and all(v['delta']<0 for v in other_major)
        reasons=[]
        if change<=0:reasons.append('no_positive_accuracy')
        if tr['CtoW']>=tr['WtoC']:reasons.append('no_positive_rescue_balance')
        if s['cap_rate']-base['cap_rate']>.10:reasons.append('cap_increase_gt10pp')
        if s['median_reasoning_tokens']>1.5*base['median_reasoning_tokens'] and change<.02:
            reasons.append('length_increase_gt50pct_without_2pp_gain')
        if severe>=2:reasons.append('multiple_major_subtypes_severely_harmed')
        if narrow:reasons.append('narrow_benefit_with_major_subtype_degradation')
        details[gain]=dict(summary=s,transitions=tr,delta=change,subtypes=strata,no_go_reasons=reasons)
        if not reasons:
            candidates.append(((-s['accuracy'],-(tr['WtoC']-tr['CtoW']),severe,
                 s['cap_rate']-base['cap_rate'],s['median_reasoning_tokens']-base['median_reasoning_tokens'],gain),gain))
    chosen=min(candidates)[1] if candidates else None
    return dict(status='pass' if chosen else 'stop_dev_no_go',dose=chosen,details=details,
                baseline=base,test_launch_authorized=bool(chosen))
