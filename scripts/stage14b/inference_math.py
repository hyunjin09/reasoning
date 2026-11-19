"""Frozen paired estimands with explicit missingness and alias sensitivity."""
from collections import defaultdict
import numpy as np
from scipy.stats import binomtest

SEED=120220260929
DRAWS=10000

def ratio_bootstrap(numerators,denominators,draws=DRAWS,scale=100):
    a=np.asarray(numerators,dtype=float);b=np.asarray(denominators,dtype=float)
    assert len(a)==len(b) and np.all(b>=0)
    if not len(a) or not b.sum():return dict(estimate_pp=None,ci95_pp=None,units=len(a),empty_draws=draws)
    rng=np.random.default_rng(SEED);boot=[];empty=0
    # Bounded batches avoid a large draws×families allocation.
    for start in range(0,draws,128):
        ix=rng.integers(len(a),size=(min(128,draws-start),len(a)))
        numerator=a[ix].sum(axis=1);denominator=b[ix].sum(axis=1)
        keep=denominator>0;empty+=int((~keep).sum());boot.extend((numerator[keep]/denominator[keep]).tolist())
    return dict(estimate_pp=float(a.sum()/b.sum()*scale),ci95_pp=(np.quantile(boot,[.025,.975])*scale).tolist() if boot else None,
        units=len(a),empty_draws=empty,draws=draws,seed=SEED)

def summarize(values,n=None):
    if n is None:n=len(values)
    assert n==len(values) and all(v is None or type(v) is bool for v in values)
    c=values.count(True);w=values.count(False);m=values.count(None)
    return dict(n=n,correct=c,wrong=w,missing_or_unscorable=m,resolved_accuracy=c/(c+w) if c+w else None,
        coverage_lower_accuracy=c/n if n else None,accuracy_bounds=[c/n,(c+m)/n] if n else None)

def paired(rows,draws=DRAWS):
    n=len(rows);ii=[r['I'] for r in rows];tt=[r['T'] for r in rows]
    complete=[r for r in rows if r['I'] is not None and r['T'] is not None]
    delta=[int(r['T'])-int(r['I']) for r in complete];groups=defaultdict(list)
    for r,d in zip(complete,delta):groups[r['family_id']].append(d)
    item=ratio_bootstrap(delta,np.ones(len(delta)),draws)
    cluster=ratio_bootstrap([sum(v) for v in groups.values()],[len(v) for v in groups.values()],draws)
    cluster['families']=len(groups)
    family=ratio_bootstrap([np.mean(v) for v in groups.values()],np.ones(len(groups)),draws)
    missing_bounds=[(tt.count(True)-ii.count(True)-ii.count(None))/n*100,
        (tt.count(True)+tt.count(None)-ii.count(True))/n*100] if n else [None,None]
    t_only=sum(r['T'] and not r['I'] for r in complete);i_only=sum(r['I'] and not r['T'] for r in complete)
    marginal={}
    for model,values in [('I',ii),('T',tt)]:
        groups_acc=defaultdict(lambda:[0,0])
        for r,value in zip(rows,values):
            groups_acc[r['family_id']][0]+=value is True
            groups_acc[r['family_id']][1]+=value is not None
        marginal[model]=ratio_bootstrap([v[0] for v in groups_acc.values()],[v[1] for v in groups_acc.values()],draws)
    return dict(marginal_accuracy_clusters=marginal,n=n,paired_n=len(complete),paired_difference_pp=item['estimate_pp'],item=item,cluster=cluster,family_equal=family,
        I=summarize(ii),T=summarize(tt),missingness_bounds_pp=missing_bounds,
        paired_transitions=dict(both_correct=sum(r['I'] and r['T'] for r in complete),thinking_only=t_only,instruct_only=i_only,
            both_wrong=sum(not r['I'] and not r['T'] for r in complete),incomplete=n-len(complete)),
        mcnemar_exact_two_sided_p=float(binomtest(t_only,t_only+i_only,.5).pvalue) if t_only+i_only else 1.,
        robust_positive=bool(cluster['ci95_pp'] and cluster['ci95_pp'][0]>0 and missing_bounds[0]>0))

def rescue(rows,draws=DRAWS):
    failures=[r for r in rows if r['native'] is False]
    success=sum(r['equal'] is True for r in failures);resolved=sum(r['equal'] is not None for r in failures);missing=len(failures)-resolved
    groups=defaultdict(lambda:[0,0])
    for r in rows:
        g=groups[r['family_id']]
        g[0]+=int(r['native'] is False and r['equal'] is True)
        g[1]+=int(r['native'] is False and r['equal'] is not None)
    bootstrap=ratio_bootstrap([v[0] for v in groups.values()],[v[1] for v in groups.values()],draws)
    def label(v):return 'correct' if v is True else 'wrong' if v is False else 'unresolved'
    transitions={a+'__'+b:0 for a in ['correct','wrong','unresolved'] for b in ['correct','wrong','unresolved']}
    for r in rows:transitions[label(r['native'])+'__'+label(r['equal'])]+=1
    return dict(n=len(rows),native_wrong=len(failures),rescued=success,resolved_followups=resolved,unresolved_followups=missing,
        rescue_fraction_resolved=success/resolved if resolved else None,
        all_native_wrong_bounds=[success/len(failures),(success+missing)/len(failures)] if failures else [None,None],
        bootstrap=bootstrap,transitions=transitions,
        substantial_by_frozen_rule=bool(resolved and success/resolved>=.2 and bootstrap['ci95_pp'] and bootstrap['ci95_pp'][0]>=10))
