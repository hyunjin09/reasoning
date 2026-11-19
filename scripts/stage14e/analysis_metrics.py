"""Family-level estimands; missingness and alias execution remain explicit."""
import numpy as np
from collections import Counter
from scripts.stage14d1_pilot.statistics import bootstrap_indices, interval, paired_summary


def acquisition(records, family_ids, strata, arms):
    by = {(r['family_id'], r['condition']): r for r in records}
    assert len(by) == len(records)
    assert set(by) == {(f, a) for f in family_ids for a in arms}
    assert len(strata) == len(family_ids)
    indices = bootstrap_indices(strata, 4000, 20261022)
    output = {'families': len(family_ids), 'arms': {}, 'pairs': {}}
    vectors = {}
    for arm in arms:
        rs = [by[f, arm] for f in family_ids]
        assert all(r['label'] in ['U', 'R', 'K', 'W', '?', 'I', 'A', 'X'] for r in rs)
        values = np.array([int(r['label'] in ['U', 'R']) for r in rs])
        vectors[arm] = values
        attempted = sum(r['label'] != 'A' for r in rs)
        output['arms'][arm] = dict(assigned=len(family_ids), attempted=attempted,
            label_counts=dict(Counter(r['label'] for r in rs)), useful_correct=int(values.sum()),
            useful_correct_fraction=float(values.mean()), bootstrap95=interval(values[indices].mean(1)),
            useful_correct_per_attempt=float(values.sum()/attempted) if attempted else None,
            interpretation='Source-correctness under no-image conditions is not visual acquisition.'
                if 'noimage' in arm else 'New or validly reinspected source facts, including partial coverage.')
    for i, base in enumerate(arms):
        for treatment in arms[i+1:]:
            delta = vectors[treatment] - vectors[base]
            output['pairs'][treatment + '-' + base] = dict(difference=float(delta.mean()),
                bootstrap95=interval(delta[indices].mean(1)), paired_gains=int((delta == 1).sum()),
                paired_losses=int((delta == -1).sum()))
    return output


def accuracy(records, family_ids, arms=('N', 'S', 'M')):
    by = {(r['family_id'], r['arm']): r for r in records}
    assert len(by) == len(records), 'Duplicate logical family/arm'
    assert set(by) == {(f, a) for f in family_ids for a in arms}, 'Incomplete assignment table'
    indices = bootstrap_indices([by[f, arms[0]]['stratum'] for f in family_ids], 4000, 20261022)
    vectors = {a: np.array([np.nan if by[f, a]['correct'] is None else float(by[f, a]['correct'])
                            for f in family_ids]) for a in arms}
    output = {'families': len(family_ids), 'arms': {}, 'pairs': {}}
    for a, values in vectors.items():
        valid = np.isfinite(values)
        correct = int((values == 1).sum())
        unknown = int((~valid).sum())
        samples = values[indices]
        n = np.isfinite(samples).sum(1)
        means = np.divide(np.nansum(samples, axis=1), n, out=np.full(len(n), np.nan), where=n > 0)
        output['arms'][a] = dict(correct=correct, wrong=int((values == 0).sum()),
            unscorable=unknown, missing=sum(by[f, a].get('missing', False) for f in family_ids),
            assigned=len(family_ids), known_correct_fraction=correct/len(family_ids),
            scorable_accuracy=float(values[valid].mean()) if valid.any() else None,
            scorable_bootstrap95=interval(means),
            accuracy_missingness_bounds=[correct/len(family_ids), (correct+unknown)/len(family_ids)])
    for base, treatment in [('N', 'S'), ('N', 'M'), ('S', 'M')]:
        if base not in vectors or treatment not in vectors:
            continue
        result = paired_summary(vectors[base], vectors[treatment], indices)
        result['rescue_items'] = [by[f, base]['item_id'] for j, f in enumerate(family_ids)
                                 if vectors[base][j] == 0 and vectors[treatment][j] == 1]
        result['regression_items'] = [by[f, base]['item_id'] for j, f in enumerate(family_ids)
                                     if vectors[base][j] == 1 and vectors[treatment][j] == 0]
        output['pairs'][treatment + '-' + base] = result
    return output
