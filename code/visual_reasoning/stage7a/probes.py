"""Fixed L2 logistic feasibility probe; no hyperparameter or feature search."""
from collections import Counter
import warnings
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler


def group_weights(rows, balance_classes=False):
    counts = Counter((r['group_id'], r['label']) if balance_classes else r['group_id'] for r in rows)
    weights = np.array([1./counts[(r['group_id'], r['label']) if balance_classes else r['group_id']] for r in rows])
    if balance_classes:
        labels = np.array([r['label'] for r in rows])
        for label in (0, 1):
            selected = labels == label
            weights[selected] *= len(rows)/(2*weights[selected].sum())
    return weights


def score_predictions(rows, probability):
    y = np.array([r['label'] for r in rows])
    p = np.asarray(probability)
    assert len(rows) == len(p) and set(y) == {0, 1} and np.isfinite(p).all()
    w = group_weights(rows)
    pred = (p >= .5).astype(int)
    bins = []
    bin_id = np.minimum((p*10).astype(int), 9)
    for b in range(10):
        selected = bin_id == b
        bins.append(dict(bin=b, lower=b/10, upper=(b+1)/10, events=int(selected.sum()),
                         families=len({r['group_id'] for r, use in zip(rows, selected) if use}),
                         mean_probability=float(np.average(p[selected], weights=w[selected])) if selected.any() else None,
                         positive_fraction=float(np.average(y[selected], weights=w[selected])) if selected.any() else None))
    return dict(balanced_accuracy=float(balanced_accuracy_score(y, pred, sample_weight=w)),
                macro_F1=float(f1_score(y, pred, average='macro', sample_weight=w, zero_division=0)),
                AUROC=float(roc_auc_score(y, p, sample_weight=w)),
                Brier=float(np.average((p-y)**2, weights=w)), calibration=bins,
                events=len(rows), independent_families=len({r['group_id'] for r in rows}))


def fit_probe(train, test, family, *, minimum_groups=2):
    group_counts = {split: {str(label): len({r['group_id'] for r in rows if r['label'] == label})
                           for label in (0, 1)} for split, rows in [('train', train), ('test', test)]}
    if any(n < minimum_groups for counts in group_counts.values() for n in counts.values()):
        return dict(status='UNAVAILABLE', reason='Fewer than two independent families per class on a split side',
                    groups_per_class=group_counts)
    assert not {r['group_id'] for r in train} & {r['group_id'] for r in test}
    vectorizer = DictVectorizer(sparse=False, dtype=np.float64)
    x_train = vectorizer.fit_transform([r['features'][family] for r in train])
    x_test = vectorizer.transform([r['features'][family] for r in test])
    if x_train.shape[1] == 0:
        return dict(status='UNAVAILABLE', reason='No observed training features in this family', groups_per_class=group_counts)
    assert np.isfinite(x_train).all() and np.isfinite(x_test).all()
    weights = group_weights(train, balance_classes=True)
    scaler = StandardScaler().fit(x_train, sample_weight=weights)
    x_train, x_test = scaler.transform(x_train), scaler.transform(x_test)
    model = LogisticRegression(C=1., penalty='l2', solver='liblinear', max_iter=2000, random_state=1234)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model.fit(x_train, [r['label'] for r in train], sample_weight=weights)
    probability = model.predict_proba(x_test)[:, list(model.classes_).index(1)]
    return dict(status='ESTIMATED_FEASIBILITY_ONLY', groups_per_class=group_counts,
                feature_count=x_train.shape[1], feature_names=vectorizer.get_feature_names_out().tolist(),
                metrics=score_predictions(test, probability),
                predictions=[dict(id=r['id'], group_id=r['group_id'], label=r['label'], probability=float(p))
                             for r, p in zip(test, probability)],
                warnings=[str(w.message) for w in caught], iterations=model.n_iter_.tolist(),
                estimator=dict(family='L2 logistic', C=1., solver='liblinear', max_iter=2000, seed=1234),
                preprocessing='Vocabulary, weighted centering and scaling fit on training data only; missing source features are zero with explicit availability indicators')


def accuracy_bootstrap(predictions, *, paired_reference=None, samples=2000, seed=1234):
    """Hold the fitted model fixed and resample independent test families."""
    groups = sorted({r['group_id'] for r in predictions})
    if len(groups) < 2:
        return dict(status='UNAVAILABLE', reason='Fewer than two independent test families')
    y = np.array([r['label'] for r in predictions])
    pred = np.array([r['probability'] >= .5 for r in predictions])
    group_index = np.array([groups.index(r['group_id']) for r in predictions])
    weights = group_weights(predictions)
    other = None
    if paired_reference is not None:
        lookup = {r['id']: r for r in paired_reference}
        assert set(lookup) == {r['id'] for r in predictions}
        assert all(lookup[r['id']]['label'] == r['label'] and lookup[r['id']]['group_id'] == r['group_id'] for r in predictions)
        other = np.array([lookup[r['id']]['probability'] >= .5 for r in predictions])
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(samples):
        multiplicity = np.bincount(rng.integers(0, len(groups), len(groups)), minlength=len(groups))
        w = weights*multiplicity[group_index]
        if any(w[y == label].sum() == 0 for label in (0, 1)):
            continue
        def accuracy(p):
            return .5*sum(np.average(p[y == label] == label, weights=w[y == label]) for label in (0, 1))
        value = accuracy(pred)
        if other is not None: value -= accuracy(other)
        values.append(value)
    return dict(status='ESTIMATED', interval95=np.quantile(values, [.025, .975]).tolist() if values else None,
                valid_samples=len(values), requested_samples=samples, independent_families=len(groups), seed=seed,
                estimand='paired balanced-accuracy difference' if other is not None else 'balanced accuracy',
                limitation='Conditional on fitted model; resamples lacking either class are undefined and omitted. Low family counts remain pilot evidence.')
