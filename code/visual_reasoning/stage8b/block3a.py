"""Frozen native-only taxonomy, independent-family selection and replication gate."""
from collections import defaultdict
import numpy as np
from scipy.stats import binomtest, wilcoxon


def routing_subtype(local, routing):
    shares = routing.get('candidate_visual_shares', {})
    margin = routing.get('qk_T_X')
    if local not in ('L+', 'L-') or not {'T','X'} <= shares.keys() or margin is None:
        return 'R4'
    if not np.isfinite(margin) or not all(np.isfinite(v) for v in shares.values()):
        return 'R4'
    ordered = sorted(shares, key=lambda k: -shares[k])
    if abs(shares[ordered[0]]-shares[ordered[1]]) <= 1e-8:
        return 'R4'
    if ordered[0] == 'X':
        return 'R2'
    if ordered[0] != 'T':
        return 'R4'
    if margin <= 1.0:
        return 'R1'
    return 'R3' if local == 'L-' else 'SELECTIVE_LPLUS'


def select_anchors(rows, n=32):
    chosen, used = [], set()
    failures = sorted((r for r in rows if r['local']=='L-'), key=lambda r:r['review_order'])
    controls = sorted((r for r in rows if r['local']=='L+'), key=lambda r:(r['qk_T_X'],r['review_order']))
    for row in failures+controls:
        if row['family_id'] not in used:
            chosen.append(row); used.add(row['family_id'])
        if len(chosen)==n:
            break
    if len(chosen)!=n:
        raise ValueError(f'Only {len(chosen)} eligible independent families for requested {n}')
    return chosen


def pair_reads(rows):
    grouped=defaultdict(list)
    for row in rows:
        if row['seed'] in (1235,1236,1237,1238) and row['local'] in ('L+','L-'):
            grouped[(str(row['item_id']),row['subgoal'])].append(row)
    result=[]
    for key,group in sorted(grouped.items()):
        assert len({r['seed'] for r in group})==len(group), 'Multiple reads for one seed/subgoal'
        plus=sorted((r for r in group if r['local']=='L+'),key=lambda r:r['seed'])
        minus=sorted((r for r in group if r['local']=='L-'),key=lambda r:r['seed'])
        for a,b in zip(plus,minus):
            assert a['family_id']==b['family_id'] and a['category']==b['category']
            result.append(dict(item_id=key[0],subgoal=key[1],family_id=a['family_id'],category=a['category'],success=a['event_id'],failure=b['event_id']))
    return result


def replication(pairs):
    families=sorted({p['family_id'] for p in pairs})
    summary=dict(pairs=len(pairs),families=len(families),yield_pass=len(pairs)>=20 and len(families)>=16,metrics={})
    rng=np.random.default_rng(1234)
    for metric in ('qk_T_X','share_T_X'):
        values={f:np.median([p[metric] for p in pairs if p['family_id']==f]) for f in families}
        x=np.asarray(list(values.values()),dtype=float)
        if not len(x) or not np.all(np.isfinite(x)):
            summary['metrics'][metric]=dict(pass_gate=False,reason='Missing/nonfinite paired measurements'); continue
        boot=np.median(x[rng.integers(0,len(x),size=(10000,len(x)))],axis=1)
        lo,hi=np.quantile(boot,[.025,.975]); median=float(np.median(x))
        strata={}
        for category in sorted({p['category'] for p in pairs}):
            ids={p['family_id'] for p in pairs if p['category']==category}
            strata[category]=dict(families=len(ids),median=float(np.median([values[f] for f in ids])))
        breadth=sum(s['families']>=2 and s['median']>0 for s in strata.values())>=2
        nonzero=x[x!=0]
        sign_p=binomtest(int((nonzero>0).sum()),len(nonzero),.5).pvalue if len(nonzero) else 1.
        summary['metrics'][metric]=dict(median=median,ci95=[float(lo),float(hi)],sign_p=sign_p,
            wilcoxon_p=float(wilcoxon(x).pvalue) if len(nonzero) else 1.,
            paired_standardized_mean=float(x.mean()/x.std(ddof=1)) if len(x)>1 and x.std(ddof=1)>0 else None,
            categories=strata,breadth_pass=breadth,pass_gate=bool(median>0 and lo>0 and breadth))
    tests=sorted((v['sign_p'],k) for k,v in summary['metrics'].items() if 'sign_p' in v)
    previous=0.
    for i,(p,key) in enumerate(tests):
        previous=max(previous,min(1.,(len(tests)-i)*p));summary['metrics'][key]['sign_p_holm']=previous
    summary['pass']=bool(summary['yield_pass'] and any(v['pass_gate'] for v in summary['metrics'].values()))
    return summary
