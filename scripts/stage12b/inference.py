"""One row per independent family; explicit undefined/excluded denominators."""
import math
import numpy as np
from scripts.stage12b.protocol import profile


def proportion(k, n):
    if n == 0:
        return dict(numerator=k, denominator=n, estimate=None, wilson95=None)
    p = k/n
    z = 1.959963984540054
    d = 1+z*z/n
    center = (p+z*z/(2*n))/d
    radius = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return dict(numerator=k, denominator=n, estimate=p,
                wilson95=[max(0, center-radius), min(1, center+radius)])


def contrast(rows):
    pos = [r for r in rows if r['e'] and not r['n']]
    neg = [r for r in rows if not r['e'] and not r['n']]
    recovery = (sum(r['o'] for r in pos)/len(pos)-sum(r['o'] for r in neg)/len(neg)) if pos and neg else None
    delta = sum(int(r['o'])-int(r['n']) for r in rows)/len(rows) if rows else None
    return recovery, delta


def infer(rows, draws=4000, seed=120220260929):
    assert len({r['family_id'] for r in rows}) == len(rows)
    native = [r for r in rows if r['n'] is not None]
    paired = [r for r in rows if all(r[k] is not None for k in ['e','n','o'])]
    failures = [r for r in paired if not r['n']]
    labels = [profile(r['e'], r['n'], r['o']) for r in failures]
    counts = {b: labels.count(b) for b in ['B1','B2','B3','B4']}
    assert sum(counts.values()) == len(failures)
    endpoints = dict(P1=proportion(sum(not r['n'] for r in native),len(native)),
                     P2=proportion(sum(r['o'] for r in failures),len(failures)))
    for i, b in enumerate(counts, 3): endpoints[f'P{i}'] = proportion(counts[b],len(failures))
    rng = np.random.default_rng(seed)
    samples = [[], []]
    for _ in range(draws):
        selected = [paired[i] for i in rng.integers(len(paired), size=len(paired))] if paired else []
        for dest, value in zip(samples, contrast(selected)):
            if value is not None: dest.append(value)
    contrasts = {}
    for name, value, sample in zip(['rescue_Eplus_minus_Eminus','paired_oracle_minus_native'],contrast(paired),samples):
        contrasts[name] = dict(estimate=value, percentile95=np.percentile(sample,[2.5,97.5]).tolist() if sample else None,
                               defined_draws=len(sample), draws=draws)
    informative = len(failures)>=20 and (sum(counts[b]>=5 for b in ['B1','B2','B3'])>=2 or max(counts[b] for b in ['B1','B2','B3'])>=10)
    return dict(endpoints=endpoints,classes=counts,contrasts=contrasts,bootstrap_seed=seed,
                independent_unit='family',native_denominator=len(native),paired_denominator=len(paired),
                technical_excluded_from_paired=[r['family_id'] for r in rows if r not in paired],
                secondary_rescue={str(e):proportion(sum(r['o'] for r in failures if r['e']==e),sum(r['e']==e for r in failures)) for e in [True,False]},
                decision='PROFILE_INFORMATIVE' if informative else 'PROFILE_SPARSE')
