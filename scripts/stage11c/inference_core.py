"""Prospective family-paired P1–P3 calculations; no automatic interpretation or launch."""
import math
import numpy as np
from scripts.stage11c.common import SEED

ENDPOINTS = ('P1_native_gap', 'P2_oracle_gap', 'P3_gap_closure')


def discordance(thinking, direct):
    forward = int(np.sum(thinking & ~direct))
    reverse = int(np.sum(direct & ~thinking))
    n = forward+reverse
    tail = sum(math.comb(n, k) for k in range(min(forward, reverse)+1))/2**n if n else .5
    return dict(thinking_only=forward, direct_only=reverse,
        both_correct=int(np.sum(thinking & direct)), both_wrong=int(np.sum(~thinking & ~direct)),
        mcnemar_exact_descriptive_p=min(1., 2*tail))


def paired_estimates(rows):
    """One complete record per conservative family, equal weighting,4000 draws."""
    assert rows and len({r['family_id'] for r in rows}) == len(rows)
    fields = ('native_thinking', 'native_direct', 'oracle_thinking', 'oracle_direct')
    assert all(isinstance(r[k], (bool, np.bool_)) for r in rows for k in fields), 'No missing-outcome imputation'
    y = np.array([[r[k] for k in fields] for r in rows], dtype=bool)
    v = y.astype(np.float64)
    x = np.column_stack([v[:, 0]-v[:, 1], v[:, 2]-v[:, 3],
                         v[:, 0]-v[:, 1]-v[:, 2]+v[:, 3]])
    draws = np.random.default_rng(SEED).integers(0, len(rows), (4000, len(rows)))
    boot = x[draws].mean(axis=1)
    result = {}
    for j, name in enumerate(ENDPOINTS):
        result[name] = dict(estimate=float(x[:, j].mean()),
            ci95=np.percentile(boot[:, j], [2.5, 97.5]).tolist(),
            ci_bonferroni_3=np.percentile(boot[:, j], [100*.05/6, 100*(1-.05/6)]).tolist())
    p1, p3 = result['P1_native_gap'], result['P3_gap_closure']
    return dict(n_families=len(rows), weighting='equal_family_paired', seed=SEED, bootstrap_draws=4000,
        endpoints=result, accuracy=dict(zip(fields, v.mean(axis=0).tolist())),
        discordance=dict(native=discordance(y[:, 0], y[:, 1]), oracle=discordance(y[:, 2], y[:, 3])),
        closure_fraction=p3['estimate']/p1['estimate'] if p1['estimate'] >= .10 and p1['ci95'][0] > 0 else None)
