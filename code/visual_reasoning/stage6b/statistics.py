"""Base-level paired effects with source-group-aware inference."""
import math
from collections import defaultdict
import numpy as np
from scipy.stats import wilcoxon


def holm(pvalues):
    values = np.asarray(pvalues, dtype=float)
    if not np.isfinite(values).all() or (values < 0).any() or (values > 1).any():
        raise ValueError('Finite p-values in [0,1] required')
    order = np.argsort(values, kind='stable')
    adjusted = np.empty(len(values))
    maximum = 0.
    for index, position in enumerate(order):
        maximum = max(maximum, float(values[position])*(len(values)-index))
        adjusted[position] = min(1., maximum)
    return adjusted.tolist()


def paired_effect(values, groups=None, *, seed=1234):
    values = np.asarray(values, dtype=float)
    if not values.size or not np.isfinite(values).all():
        raise ValueError('Nonempty finite paired effects required')
    if groups is None:
        groups = list(range(len(values)))
    if len(groups) != len(values):
        raise ValueError('Group count differs from base count')
    clusters = defaultdict(list)
    for group, value in zip(groups, values):
        clusters[group].append(float(value))
    sums = np.asarray([sum(v) for v in clusters.values()])
    counts = np.asarray([len(v) for v in clusters.values()])
    means = sums/counts
    sample = np.random.default_rng(seed).integers(0, len(means), size=(10000,len(means)))
    bootstrap = sums[sample].sum(1)/counts[sample].sum(1)
    ci = np.quantile(bootstrap, [.025,.975]).tolist()
    p = 1. if not np.any(means) or len(means)<2 else float(wilcoxon(means, alternative='two-sided', method='auto').pvalue)
    if not math.isfinite(p):
        raise RuntimeError('Nonfinite Wilcoxon p-value')
    return {'bases':len(values),'independent_groups':len(means),
        'mean':float(values.mean()),'median':float(np.median(values)),
        'positive_fraction':float((values>0).mean()),'zero_fraction':float((values==0).mean()),
        'bootstrap_mean_ci95':ci,'p_raw':p,'bootstrap_resamples':10000,'seed':seed,
        'inference':'Two-sided paired Wilcoxon on source-group means; source-group bootstrap preserving equal base weighting. Conditions/events are aggregated within base first.'}


def robustness(result, corrected_p):
    return bool(result['independent_groups']>=2 and result['median']>0
        and result['bootstrap_mean_ci95'][0]>0
        and result['positive_fraction']>=.75 and corrected_p<.05)
