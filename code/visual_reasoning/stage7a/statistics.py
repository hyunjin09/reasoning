"""Bounded base-family bootstrap and directional sign-randomization tests."""
from collections import defaultdict
import numpy as np


def collapse_groups(rows, value_key='value'):
    # Average nested events within a base first, then average near-image bases
    # within their common independent family. Large event counts add no weight.
    base = defaultdict(list)
    group_for_base = {}
    for row in rows:
        value = row[value_key]
        if value is None or not np.isfinite(value):
            continue
        base[row['base_id']].append(float(value))
        group_for_base[row['base_id']] = row['group_id']
    grouped = defaultdict(list)
    for key, values in base.items():
        grouped[group_for_base[key]].append(float(np.mean(values)))
    return {key: float(np.mean(values)) for key, values in sorted(grouped.items())}


def directional_summary(rows, *, seed=1234, bootstrap_samples=2000, randomization_samples=10000):
    groups = collapse_groups(rows)
    values = np.array(list(groups.values()), dtype=float)
    result = dict(independent_unit='image/question family; equal base weights within near-image group',
                  groups=groups, n_groups=len(values), n_bases=len({r['base_id'] for r in rows}),
                  nested_events=len(rows), inference_scope='preselected semantic cohort; never selected by causal state/effect')
    if not len(values):
        return {**result, 'status': 'UNAVAILABLE', 'p_one_sided': None}
    result.update(mean=float(values.mean()), median=float(np.median(values)),
                  positive_group_fraction=float(np.mean(values > 0)))
    if len(values) < 2:
        return {**result, 'status': 'CASE_ONLY', 'p_one_sided': None, 'mean_ci95': None}
    rng = np.random.default_rng(seed)
    boot = rng.choice(values, (bootstrap_samples, len(values)), replace=True).mean(axis=1)
    result['mean_ci95'] = np.quantile(boot, [.025, .975]).tolist()
    if len(values) <= 16:
        indices = np.arange(2**len(values), dtype=np.uint32)
        signs = 2*((indices[:, None] >> np.arange(len(values))) & 1).astype(float)-1
        p = float(np.mean((signs*values).mean(axis=1) >= values.mean()-1e-12))
        method = 'exact sign randomization of independent family means'
    else:
        signs = rng.choice([-1., 1.], (randomization_samples, len(values)))
        p = float((1+np.sum((signs*values).mean(axis=1) >= values.mean()-1e-12))/(randomization_samples+1))
        method = 'seeded sign randomization of independent family means, 10000 draws'
    result.update(status='ESTIMATED', p_one_sided=p, p_method=method, seed=seed,
                  bootstrap_samples=bootstrap_samples)
    return result


def holm_within_family(tests):
    result = {key: dict(value) for key, value in tests.items()}
    eligible = sorted(((r['p_one_sided'], key) for key, r in result.items()
                       if r.get('p_one_sided') is not None))
    previous = 0.
    for index, (p, key) in enumerate(eligible):
        corrected = min(1., max(previous, p*(len(eligible)-index)))
        previous = corrected
        r = result[key]
        r['holm_p'] = corrected
        r['directionally_robust'] = bool(r['median'] > 0 and r['mean_ci95'][0] > 0 and
                                         r['positive_group_fraction'] >= .75 and corrected < .05)
    for r in result.values():
        r.setdefault('holm_p', None)
        r.setdefault('directionally_robust', False)
    return result
