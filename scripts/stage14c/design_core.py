"""Prospective Stage14C CPU analysis core. No dataset/model loading or launches."""
from collections import Counter, defaultdict
import hashlib
import re
import numpy as np

ANALYSIS_SEED = 120220260929
STATUSES = ('CORRECT', 'WRONG', 'UNSCORABLE', 'TECHNICAL_MISSING')
VALUES = dict(CORRECT=1, WRONG=0, UNSCORABLE=None, TECHNICAL_MISSING=None)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def select_families(rows, main_n, reserve_n, seed):
    """Hamilton proportional quotas after family consolidation; no outcome fields."""
    ids = [r['family_id'] for r in rows]
    if len(set(ids)) != len(ids) or min(main_n, reserve_n) < 0:
        raise ValueError('Require unique consolidated families and nonnegative sizes')

    def pick(pool, n, purpose):
        n = min(n, len(pool))
        if not n:
            return []
        groups = defaultdict(list)
        for r in pool:
            groups[r['stratum']].append(r)
        quotas = {s: n * len(g) // len(pool) for s, g in groups.items()}
        order = sorted(groups, key=lambda s: (-(n * len(groups[s]) % len(pool)), s))
        for s in order[:n - sum(quotas.values())]:
            quotas[s] += 1
        selected = []
        for s in sorted(groups):
            rank = lambda r: (digest(f'{seed}|{purpose}|{r["family_id"]}'), r['family_id'])
            selected.extend(sorted(groups[s], key=rank)[:quotas[s]])
        return selected

    main = pick(rows, main_n, 'main')
    used = {r['family_id'] for r in main}
    reserve = pick([r for r in rows if r['family_id'] not in used], reserve_n, 'reserve')
    return dict(main=main, reserve=reserve)


def _canonical(answer, kind, options):
    if not isinstance(answer, str):
        return None
    text = answer.strip()
    if text.startswith('{') and text.endswith('}'):
        text = text[1:-1].strip()
    if kind in ('choice', 'letter'):
        if kind == 'choice' and not options:
            raise ValueError('Choice adapter requires source-defined option labels')
        return text.upper() if re.fullmatch(r'[A-Za-z]', text) and (kind == 'letter' or text.upper() in options) else None
    if kind == 'yes_no':
        return {'yes': True, 'true': True, 'no': False, 'false': False}.get(text.lower())
    if kind == 'integer':
        return int(text) if re.fullmatch(r'[+-]?\d+', text) else None
    if kind == 'ordered_pair':
        if text.startswith('(') and text.endswith(')'):
            text = text[1:-1]
        match = re.fullmatch(r'\s*([+-]?\d+)\s*,\s*([+-]?\d+)\s*', text)
        return tuple(map(int, match.groups())) if match else None
    raise ValueError('Unsupported source-defined answer type')


def score_final(answer, gold, kind, options=None):
    """Only adjudicated committed-final spans belong here, never full reasoning."""
    target = _canonical(gold, kind, options)
    if target is None:
        return 'SOURCE_REVIEW'
    if answer is None:
        return 'UNSCORABLE'
    value = _canonical(answer, kind, options)
    if value is None:
        return 'REVIEW'
    return 'CORRECT' if value == target else 'WRONG'


def ratio_draws(numerator, denominator, draws=10000, stream='default'):
    a, b = np.asarray(numerator, float), np.asarray(denominator, float)
    if a.shape != b.shape or a.ndim != 1 or np.any(b < 0) or draws <= 0:
        raise ValueError('Invalid family contribution arrays')
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError('Nonfinite family contribution')
    if len(a) == 0 or b.sum() == 0:
        return np.full(draws, np.nan)
    rng = np.random.default_rng(int(digest(f'{ANALYSIS_SEED}|{stream}')[:16], 16))
    output = np.full(draws, np.nan)
    for start in range(0, draws, 128):
        count = min(128, draws - start)
        ix = rng.integers(len(a), size=(count, len(a)))
        num, den = a[ix].sum(axis=1), b[ix].sum(axis=1)
        output[start:start + count] = np.divide(num * 100, den, out=np.full(count, np.nan), where=den > 0)
    return output


def interval(values):
    finite = values[np.isfinite(values)]
    return np.quantile(finite, [.025, .975]).tolist() if len(finite) else None


def marginal(rows, field, draws, stream):
    groups = defaultdict(list)
    for r in rows:
        groups[r['family_id']].append(VALUES[r[field]])
    good, wrong, lower, upper = [], [], [], []
    for family in sorted(groups):
        values = groups[family]
        scored = [v for v in values if v is not None]
        if scored:
            good.append(float(np.mean(scored)))
            wrong.append(1 - float(np.mean(scored)))
        nwrong = sum(v == 0 for v in values)
        missing = sum(v is None for v in values)
        lower.append(nwrong / len(values))
        upper.append((nwrong + missing) / len(values))
    return dict(accuracy_pp=float(np.mean(good) * 100) if good else None,
        residual_error_pp=float(np.mean(wrong) * 100) if wrong else None,
        residual_error_ci95_pp=interval(ratio_draws(wrong, [1] * len(wrong), draws, stream)),
        residual_error_bounds_pp=[float(np.mean(lower) * 100), float(np.mean(upper) * 100)] if groups else None)


def panel(rows, left, right, draws=10000, stream='default'):
    """Family-equal complete-pair effect; all source families retained for bounds."""
    groups, transitions = defaultdict(list), Counter()
    seen = set()
    for r in rows:
        key = (r['family_id'], r['item_id'])
        if key in seen or r[left] not in STATUSES or r[right] not in STATUSES:
            raise ValueError('Duplicate item or unsupported four-way outcome')
        seen.add(key)
        groups[r['family_id']].append((VALUES[r[left]], VALUES[r[right]]))
        transitions[r[left] + '__' + r[right]] += 1
    deltas, family_deltas, lows, highs, rescued, rescue_den = [], [], [], [], [], []
    paired_cells = {a + '__' + b: [] for a in ['CORRECT', 'WRONG'] for b in ['CORRECT', 'WRONG']}
    wrong_n = rescue_n = scored_wrong_n = 0
    weighted_wrong = weighted_unknown = weighted_rescue = 0.
    for family in sorted(groups):
        pairs = groups[family]
        complete = [(a, b) for a, b in pairs if a is not None and b is not None]
        ds = [b - a for a, b in complete]
        if ds:
            deltas.extend(ds)
            family_deltas.append(float(np.mean(ds)))
            for a in ['CORRECT', 'WRONG']:
                for b in ['CORRECT', 'WRONG']:
                    paired_cells[a + '__' + b].append(sum(x == VALUES[a] and y == VALUES[b] for x, y in complete) / len(complete))
        lows.append(float(np.mean([(0 if b is None else b) - (1 if a is None else a) for a, b in pairs])))
        highs.append(float(np.mean([(1 if b is None else b) - (0 if a is None else a) for a, b in pairs])))
        failures = [(a, b) for a, b in pairs if a == 0]
        n, s = len(failures), sum(b is not None for a, b in failures)
        good = sum(b == 1 for a, b in failures)
        wrong_n += n; scored_wrong_n += s; rescue_n += good
        rescued.append(good / len(pairs)); rescue_den.append(s / len(pairs))
        weighted_wrong += n / len(pairs)
        weighted_unknown += (n - s) / len(pairs)
        weighted_rescue += good / len(pairs)
    boot = ratio_draws(family_deltas, [1] * len(family_deltas), draws, stream + '|difference')
    rb = ratio_draws(rescued, rescue_den, draws, stream + '|rescue')
    denominator = sum(rescue_den)
    rescue = dict(numerator=rescue_n, scored_denominator=scored_wrong_n,
        native_wrong=wrong_n, unresolved_followups=wrong_n - scored_wrong_n,
        estimate_pp=100 * sum(rescued) / denominator if denominator else None,
        raw_fraction=rescue_n / scored_wrong_n if scored_wrong_n else None,
        bounds_pp=[100 * weighted_rescue / weighted_wrong, 100 * (weighted_rescue + weighted_unknown) / weighted_wrong] if weighted_wrong else None,
        ci95_pp=interval(rb), empty_draws=int(np.isnan(rb).sum()))
    return dict(n=len(rows), independent_units=len(groups), paired_n=len(deltas),
        paired_families=len(family_deltas), difference_pp=float(np.mean(family_deltas) * 100) if family_deltas else None,
        item_difference_pp=float(np.mean(deltas) * 100) if deltas else None,
        difference_bounds_pp=[float(np.mean(lows) * 100), float(np.mean(highs) * 100)] if groups else None,
        ci95_pp=interval(boot), rescue=rescue, transitions=dict(transitions),
        paired_transition_fraction_family_equal={k: float(np.mean(v)) if v else None for k, v in paired_cells.items()},
        marginal_left=marginal(rows, left, draws, stream + '|left_residual'),
        marginal_right=marginal(rows, right, draws, stream + '|right_residual'),
        counts_left={s: sum(r[left] == s for r in rows) for s in STATUSES},
        counts_right={s: sum(r[right] == s for r in rows) for s in STATUSES},
        _difference_draws=boot, _rescue_draws=rb, stream=stream)


def contrast(anchor, other, endpoint):
    if anchor['stream'] == other['stream']:
        raise ValueError('Independent tasks require independent bootstrap streams')
    if endpoint == 'difference':
        a, b = anchor['difference_pp'], other['difference_pp']
        bounds_a, bounds_b = anchor['difference_bounds_pp'], other['difference_bounds_pp']
    elif endpoint == 'rescue':
        a, b = anchor['rescue']['estimate_pp'], other['rescue']['estimate_pp']
        bounds_a, bounds_b = anchor['rescue']['bounds_pp'], other['rescue']['bounds_pp']
    else:
        raise ValueError('Unknown contrast endpoint')
    if a is None or b is None:
        return dict(estimate_pp=None, ci95_pp=None, bounds_pp=None, status='NOT_ESTIMABLE')
    samples = anchor[f'_{endpoint}_draws'] - other[f'_{endpoint}_draws']
    empty = int(np.isnan(samples).sum())
    return dict(estimate_pp=a - b, ci95_pp=interval(samples),
        bounds_pp=[bounds_a[0] - bounds_b[1], bounds_a[1] - bounds_b[0]],
        empty_draws=empty, status='UNSTABLE_BOOTSTRAP' if empty / len(samples) > .05 else 'ESTIMABLE',
        multiplicity='Unadjusted descriptive intervals; no adjusted-significance claim')
