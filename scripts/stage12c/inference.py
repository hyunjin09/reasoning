"""Family-equal rescue estimation, retaining technical missingness."""
from collections import Counter
import numpy as np
from scripts.stage12bs.inference import proportion
from scripts.stage12c.protocol import transition


def rate(rows, arm):
    values = [r[arm] for r in rows if r[arm] is not None]
    return sum(values) / len(values) if values else None


def endpoint(rows, arm):
    values = [r[arm] for r in rows if r[arm] is not None]
    k, n, total = sum(values), len(values), len(rows)
    return dict(proportion(k, n), frozen_total=total, missing=total-n,
                observed_rescues_over_frozen_total=k/total if total else None,
                missingness_identification_bounds=[k/total, (k+total-n)/total] if total else None)


def paired(rows, first, second):
    rr = [r for r in rows if r[first] is not None and r[second] is not None]
    counts = Counter(transition(r[first], r[second]) for r in rr)
    return dict(total=len(rows), jointly_scoreable=len(rr), missing_pairs=len(rows)-len(rr),
                both_fail=counts['BOTH_FAIL'], first_only=counts['C_ONLY'],
                second_only=counts['T_ONLY'], both_succeed=counts['BOTH_SUCCEED'],
                second_minus_first=(counts['T_ONLY']-counts['C_ONLY'])/len(rr) if rr else None)


def infer(rows, draws=4000, seed=120220260929):
    assert len({r['family_id'] for r in rows}) == len(rows)
    strata = {b: [r for r in rows if r['bottleneck']==b] for b in ['B1','B2','B3','B4']}
    primary = {f'P{i}': dict(endpoint(strata[b], arm), arm=arm.upper(), stratum=b)
               for i, (arm, b) in enumerate([('c','B1'),('t','B1'),('c','B4'),('t','B4')], 1)}
    rng = np.random.default_rng(seed)
    samples = {k: [] for k in ['delta_c','delta_t','t_minus_c_B1','t_minus_c_B4','overall_t_minus_c','overall_c_minus_n']}
    def contrasts(ss, overall):
        values = {}
        for a in ['c','t']:
            x, y = rate(ss['B1'], a), rate(ss['B4'], a)
            values['delta_'+a] = x-y if x is not None and y is not None else None
        for b in ['B1','B4']:
            values['t_minus_c_'+b] = paired(ss[b], 'c', 't')['second_minus_first']
        values['overall_t_minus_c'] = paired(overall, 'c', 't')['second_minus_first']
        values['overall_c_minus_n'] = paired(overall, 'n', 'c')['second_minus_first']
        return values
    def resample(rr):
        return [rr[i] for i in rng.integers(len(rr), size=len(rr))] if rr else []
    for _ in range(draws):
        ss = {b: resample(strata[b]) for b in ['B1','B4']}
        for key, value in contrasts(ss, resample(rows)).items():
            if value is not None: samples[key].append(value)
    contrast_results = {k: dict(estimate=v, percentile95=np.percentile(samples[k],[2.5,97.5]).tolist() if samples[k] else None,
                               draws=draws, defined_draws=len(samples[k]))
                        for k,v in contrasts(strata,rows).items()}
    return dict(primary=primary, contrasts=contrast_results, bootstrap_seed=seed, bootstrap_draws=draws,
                bootstrap_unit='One equally weighted independent family; C/T kept paired, missingness retained; B1/B4 resampled separately for selectivity.',
                by_stratum={b: dict(frozen_total=len(rr), c=endpoint(rr,'c'), t=endpoint(rr,'t'),
                                   paired=paired(rr,'c','t'), inferential=b in ['B1','B4']) for b,rr in strata.items()},
                overall_accuracy={a.upper(): endpoint(rows,a) for a in ['n','c','t']},
                overall_paired={f'{a.upper()}_{b.upper()}': paired(rows,a,b) for a,b in [('n','c'),('n','t'),('c','t')]},
                b1_subtypes={name: dict(c=endpoint(rr,'c'),t=endpoint(rr,'t'),paired=paired(rr,'c','t'))
                    for name,rr in [(name,[r for r in strata['B1'] if bool(r['e_has_incorrect_atom'])==explicit])
                        for name,explicit in [('B1_EXPLICIT_WRONG',True),('B1_UNRESOLVED_ONLY',False)]]})
