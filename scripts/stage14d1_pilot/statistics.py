"""Family-paired, source-stratified estimates with explicit missingness."""
import numpy as np

def bootstrap_indices(strata,draws=4000,seed=20261019):
    rng=np.random.default_rng(seed)
    groups=[np.flatnonzero(np.asarray(strata)==s) for s in sorted(set(strata))]
    return np.concatenate([rng.choice(g,size=(draws,len(g)),replace=True) for g in groups],axis=1)

def interval(values):
    values=np.asarray(values);values=values[np.isfinite(values)]
    return np.quantile(values,[.025,.975]).tolist() if len(values) else None

def paired_summary(baseline,treatment,indices):
    baseline=np.asarray(baseline,dtype=float);treatment=np.asarray(treatment,dtype=float)
    valid=np.isfinite(baseline)&np.isfinite(treatment)
    delta=treatment-baseline
    sampled=delta[indices];count=np.isfinite(sampled).sum(axis=1)
    means=np.divide(np.nansum(sampled,axis=1),count,out=np.full(len(indices),np.nan),where=count>0)
    bx=np.nan_to_num(baseline,nan=0);ty=np.nan_to_num(treatment,nan=0)
    return dict(paired_scorable=int(valid.sum()),rescue=int(((baseline==0)&(treatment==1)).sum()),
        regression=int(((baseline==1)&(treatment==0)).sum()),
        baseline_correct_paired=int((baseline[valid]==1).sum()),treatment_correct_paired=int((treatment[valid]==1).sum()),
        paired_accuracy_difference=float(delta[valid].mean()) if valid.any() else None,
        paired_bootstrap_95ci=interval(means),
        known_correct_difference_all_assigned=float((ty-bx).mean()),
        known_correct_bootstrap_95ci=interval((ty-bx)[indices].mean(axis=1)),
        missingness_difference_bounds=[float((ty-(bx+np.isnan(baseline))).mean()),float(((ty+np.isnan(treatment))-bx).mean())])
