"""Pure census definitions, independent of observed routing outcomes."""
import re
import math
from collections import Counter


def paragraphs(text):
    rows=[]
    for m in re.finditer(r'\S.*?(?=\n[ \t]*\n|\Z)',text,re.S):
        value=m.group().rstrip()
        rows.append(dict(start=m.start(),end=m.start()+len(value),text=value))
    assert ' '.join(r['text'] for r in rows).split()==text.split()
    return rows


def wilson(successes,total):
    assert 0<=successes<=total
    if not total:return dict(n=0,successes=0,point=None,ci95=None)
    z=1.959963984540054;p=successes/total;denom=1+z*z/total
    center=(p+z*z/(2*total))/denom
    radius=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/denom
    return dict(n=total,successes=successes,point=p,ci95=[0. if successes==0 else max(0.,center-radius),1. if successes==total else min(1.,center+radius)])


def agreement(a,b):
    assert len(a)==len(b)
    if not a:return dict(n=0,raw=None,kappa=None)
    n=len(a);raw=sum(x==y for x,y in zip(a,b))/n;ca,cb=Counter(a),Counter(b)
    chance=sum(ca[k]*cb[k] for k in set(a)|set(b))/(n*n)
    return dict(n=n,raw=raw,kappa=(raw-chance)/(1-chance) if chance<1 else None,
                annotator_a_counts=dict(ca),annotator_b_counts=dict(cb),chance_agreement=chance)


def decision(clean,datasets,source_types,acceptable_agreement):
    assert clean==sum(datasets.values())==sum(source_types.values())
    if clean<12:return 'NO_GO'
    if clean<24:return 'LIMITED_GO'
    if len([n for n in datasets.values() if n>=8])<2:return 'LIMITED_GO'
    if max(datasets.values())/clean>.75 or max(source_types.values())/clean>.75:return 'LIMITED_GO'
    return 'STRONG_GO' if acceptable_agreement else 'LIMITED_GO'


def qualifying_runs(indices,flags):
    assert len(indices)==len(flags)
    return [int(indices[i]) for i in range(len(indices)-1)
            if flags[i] and flags[i+1] and indices[i+1]==indices[i]+1
            and not(i>0 and flags[i-1] and indices[i]==indices[i-1]+1)]


def trajectory_counts(ids,events):
    assert len(ids)==len(set(ids));eligible=set(ids)
    assert all(e['trajectory_id'] in eligible for e in events)
    semantic={e['trajectory_id'] for e in events if e['semantic_clean']}
    primary={}
    for e in sorted(events,key=lambda e:e['onset']):
        if e['semantic_clean'] and e['C5']:primary.setdefault(e['trajectory_id'],e)
    return dict(eligible=len(ids),new_demand=len(semantic),clean=len(primary),primary=primary,
                E1=wilson(len(primary),len(ids)),E2=wilson(len(semantic),len(ids)),E3=wilson(len(primary),len(semantic)))
