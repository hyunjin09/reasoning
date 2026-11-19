"""Family-clustered confirmation uncertainty and semantic gate arithmetic."""
from collections import defaultdict

import numpy as np
from sklearn.metrics import roc_auc_score

from .probes import metrics


def family_resamples(families,*,repetitions=4000,seed=1234):
    members=defaultdict(list)
    for i,f in enumerate(families):
        members[f].append(i)
    keys=sorted(members)
    if len(keys)<2:
        raise ValueError("At least two families are needed to estimate clustered uncertainty")
    rng=np.random.default_rng(seed)
    for _ in range(repetitions):
        draw=rng.choice(len(keys),len(keys),replace=True)
        yield np.array([i for k in draw for i in members[keys[k]]],dtype=int)


def metric_intervals(events,score,threshold,*,repetitions=4000):
    score=np.asarray(score)
    samples=defaultdict(list)
    valid=0
    for index in family_resamples([e["family_id"] for e in events],repetitions=repetitions):
        subset=[events[i] for i in index]
        if len({e["label"]=="T" for e in subset})<2:
            continue
        result=metrics(subset,score[index],threshold)
        for k,v in result.items():
            if v is not None:
                samples[k].append(v)
        valid+=1
    return dict(ci95={k:np.quantile(v,[.025,.975]).tolist() for k,v in samples.items()},
                valid_resamples=valid,requested_resamples=repetitions,seed=1234)


def paired_auc_difference(events,primary,baseline,*,repetitions=4000):
    y=np.array([e["label"]=="T" for e in events],dtype=int)
    primary,baseline=np.asarray(primary),np.asarray(baseline)
    differences=[]
    for index in family_resamples([e["family_id"] for e in events],repetitions=repetitions):
        if len(set(y[index]))<2:
            continue
        differences.append(roc_auc_score(y[index],primary[index])-roc_auc_score(y[index],baseline[index]))
    interval=np.quantile(differences,[.025,.975]).tolist()
    return dict(delta=float(roc_auc_score(y,primary)-roc_auc_score(y,baseline)),ci95=interval,
                positive_supported=interval[0]>0,valid_resamples=len(differences))


def semantic_gate(events,*,repetitions=4000):
    if len({e["event_id"] for e in events})!=len(events):
        raise ValueError("Duplicate semantic events")
    grouped=defaultdict(list)
    for e in events:
        value=float(e["semantic_minus_sham"])
        if not np.isfinite(value):
            raise ValueError("Nonfinite semantic result is unavailable, not zero")
        grouped[e["family_id"]].append(value)
    if not events:
        return {"events":0,"families":0,"positive_event_fraction":None,"family_median_effect":None,"family_ci95":None,"pass":None}
    medians=np.array([np.median(grouped[f]) for f in sorted(grouped)])
    fraction=float(np.mean([e["semantic_minus_sham"]>0 for e in events]))
    median=float(np.median(medians))
    interval=None
    passed=None
    if len(medians)>=2:
        rng=np.random.default_rng(1234)
        bootstrap=np.median(rng.choice(medians,(repetitions,len(medians)),replace=True),axis=1)
        interval=np.quantile(bootstrap,[.025,.975]).tolist()
        passed=bool(fraction>=.7 and median>0 and interval[0]>0)
    return {"events":len(events),"families":len(grouped),"positive_event_fraction":fraction,
            "family_median_effect":median,"family_ci95":interval,"pass":passed,
            "family_event_counts":{f:len(v) for f,v in grouped.items()},
            "family_effect_medians":{f:float(np.median(v)) for f,v in grouped.items()},
            "scope":"Conditional on evaluable matched controls; report missing-state coverage separately"}
