"""Family-unit estimators with frozen support and bootstrap thresholds."""
import numpy as np

SEED=920260924
B=4000


def mean_interval(values,confidence=.95):
    x=np.asarray([v for v in values if v is not None and np.isfinite(v)],dtype=float)
    out=dict(n_families=len(x),mean=float(x.mean()) if len(x) else None,confidence=confidence,ci=None,
             bootstrap_replicates=B,valid_replicates=0,inference='insufficient_support')
    if not len(x):return out
    rng=np.random.default_rng(SEED)
    means=x[rng.integers(0,len(x),(B,len(x)))].mean(-1)
    out['valid_replicates']=int(np.isfinite(means).sum())
    if len(x)>=20 and out['valid_replicates']>=.95*B:
        q=(1-confidence)/2;out.update(ci=np.quantile(means,[q,1-q]).tolist(),inference='family_bootstrap')
    return out


def paired(rows,key,left='thinking',right='instruct_cot',scope='primary',confidence=.9875,allowed=None):
    by={}
    for r in rows:
        if allowed is not None and r['family_id'] not in allowed:continue
        by.setdefault(r['family_id'],{})[r['arm']]=r[scope].get(key)
    pairs=[(family,arms[left],arms[right]) for family,arms in by.items()
           if arms.get(left) is not None and arms.get(right) is not None
           and np.isfinite(arms[left]) and np.isfinite(arms[right])]
    out=mean_interval([a-b for _,a,b in pairs],confidence)
    out.update(left=left,right=right,scope=scope,metric=key,total_families=len(by),
               paired_families=[f for f,_,_ in pairs],left_mean=float(np.mean([a for _,a,_ in pairs])) if pairs else None,
               right_mean=float(np.mean([b for _,_,b in pairs])) if pairs else None)
    return out


def adjusted(rows,key,confidence=.9875):
    valid=[r for r in rows if r['primary'].get(key) is not None and np.isfinite(r['primary'][key]) and r['primary']['reasoning_tokens']>0]
    families=sorted({r['family_id'] for r in valid})
    categories={k:sorted({str(r[k]) for r in valid}) for k in ('subject','completion','answer_format')}
    columns=['intercept','thinking_vs_cot','direct_vs_cot','log_length','difficulty','question_length']
    columns += [f'{k}={v}' for k,values in categories.items() for v in values[1:]]
    X=[]
    for r in valid:
        X.append([1.,float(r['arm']=='thinking'),float(r['arm']=='instruct_direct'),np.log(r['primary']['reasoning_tokens']),float(r['difficulty']),float(r['question_length'])]
                 +[float(str(r[k])==v) for k,values in categories.items() for v in values[1:]])
    X=np.asarray(X);y=np.array([r['primary'][key] for r in valid]);family_index=np.array([families.index(r['family_id']) for r in valid])
    # Scale continuous covariates for numerical conditioning, preserving arm coefficients.
    for j in (3,4,5):X[:,j]=(X[:,j]-X[:,j].mean())/max(X[:,j].std(),1.)
    def fit(weights):
        root=np.sqrt(weights);design=X*root[:,None];target=y*root
        coef,_,rank,_=np.linalg.lstsq(design,target,rcond=1e-10)
        # Rank loss from absent resampled categories need not make the arm contrast unidentified.
        unit=np.zeros(X.shape[1]);unit[1]=1
        estimable=np.linalg.norm(unit-np.linalg.pinv(design,rcond=1e-10)@design@unit)<1e-7
        return (float(coef[1]) if estimable else np.nan),int(rank)
    estimate,rank=fit(np.ones(len(valid)));rng=np.random.default_rng(SEED);samples=[];ranks=[]
    for _ in range(B):
        counts=np.bincount(rng.integers(0,len(families),len(families)),minlength=len(families))
        effect,r=fit(counts[family_index]);samples.append(effect);ranks.append(r)
    samples=np.asarray(samples);ok=np.isfinite(samples)
    out=dict(metric=key,coefficient=estimate if np.isfinite(estimate) else None,ci=None,confidence=confidence,
        n_families=len(families),n_trajectories=len(valid),columns=columns,rank=rank,design_columns=X.shape[1],
        rank_deficient=rank<X.shape[1],bootstrap_rank_deficient=int(sum(r<X.shape[1] for r in ranks)),
        valid_replicates=int(ok.sum()),bootstrap_replicates=B,inference='insufficient_support',
        meaning='Adjusted association; generation length/completion are post-checkpoint quantities, not randomized controls')
    if len(families)>=20 and ok.sum()>=.95*B and np.isfinite(estimate):
        q=(1-confidence)/2;out.update(ci=np.quantile(samples[ok],[q,1-q]).tolist(),inference='family_cluster_bootstrap_OLS')
    return out
