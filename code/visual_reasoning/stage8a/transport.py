"""Frozen, query-and-span transport weakness and discovery-only cheap gates."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


CHEAP_KEYS = ("alphaV_ratio", "postWO_ratio", "residual_ratio",
              "head_cancellation_ratio", "head_cosine_disagreement")


def transport_values(event):
    return float(event["first_query_js"]["visual_off"]), float(event["ce_effect"]["visual_off"])


def weak_transport(event, rule):
    js, ce = transport_values(event)
    if not np.isfinite([js, ce]).all() or js < 0:
        raise ValueError("Transport observations must be finite with nonnegative JS")
    return bool(js < rule["tau_js"] and abs(ce) < rule["tau_abs_ce"])


def cheap_matrix(events, key):
    if key not in CHEAP_KEYS:
        raise ValueError("Unregistered cheap transport feature")
    values = np.array([np.median([layer["transport"][key][0]
                                 for layer in e["passive_current"].values()]) for e in events])
    if not np.isfinite(values).all():
        raise ValueError("Missing transport features are not zero")
    if key != "head_cosine_disagreement":
        if (values < 0).any():
            raise ValueError("Norm ratios cannot be negative")
        values = np.log10(np.maximum(values, 1e-16))
    return values[:, None]


def binary_metrics(y, score, threshold):
    y, score = np.asarray(y, dtype=int), np.asarray(score)
    pred = score > threshold
    two_classes = len(set(y)) == 2
    return dict(n=len(y), positives=int(y.sum()),
                auroc=float(roc_auc_score(y, score)) if two_classes else None,
                auprc=float(average_precision_score(y, score)) if y.any() else None,
                recall=float(pred[y == 1].mean()) if y.any() else None,
                fpr=float(pred[y == 0].mean()) if (y == 0).any() else None,
                balanced_accuracy=float(balanced_accuracy_score(y, pred)) if two_classes else None)


def operating_point(y, score):
    choices = []
    for threshold in np.unique(score):
        m = binary_metrics(y, score, threshold)
        if m["fpr"] <= .2:
            choices.append((m["recall"], -m["fpr"], float(threshold)))
    return max(choices)[2]


def fit_cheap_gates(events, rule):
    if any(e["split"] != "discovery" for e in events):
        raise ValueError("Cheap gate fitting is discovery-only")
    y = np.array([weak_transport(e, rule) for e in events], dtype=int)
    groups = np.array([e["family_id"] for e in events])
    if len(set(y)) < 2:
        return {}, {"unavailable": "Only one causal transport class in discovery high-R events"}
    n_splits = min(5, *(len(set(groups[y == value])) for value in (0, 1)))
    if n_splits < 2:
        return {}, {"unavailable": "Fewer than two families in a transport class"}
    folds = list(StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=1234).split(y, y, groups))
    models, report = {}, {}
    for key in CHEAP_KEYS:
        x = cheap_matrix(events, key)
        candidates = []
        for c in (.01, .1, 1., 10.):
            score = np.empty(len(y))
            for train, valid in folds:
                if len(set(y[train])) < 2:
                    raise ValueError("Grouped training fold lacks one transport class")
                model = make_pipeline(StandardScaler(), LogisticRegression(
                    C=c, class_weight="balanced", solver="liblinear", random_state=1234))
                model.fit(x[train], y[train])
                score[valid] = model.predict_proba(x[valid])[:, 1]
            tau = operating_point(y, score)
            candidates.append(dict(C=c, oof=score.tolist(), threshold=tau, metrics=binary_metrics(y, score, tau)))
        best = max(candidates, key=lambda a: (a["metrics"]["auroc"], -a["C"]))
        model = make_pipeline(StandardScaler(), LogisticRegression(
            C=best["C"], class_weight="balanced", solver="liblinear", random_state=1234))
        model.fit(x, y)
        models[key] = dict(model=model, threshold=best["threshold"])
        report[key] = best
    best_auc = max(r["metrics"]["auroc"] for r in report.values())
    # Prefer simpler norm measures when their discovery AUROC is within .02.
    preferred = next(k for k in CHEAP_KEYS if report[k]["metrics"]["auroc"] >= best_auc - .02)
    return models, dict(candidates=report, preferred=preferred, folds=n_splits,
                        event_order=[e["event_id"] for e in events], labels=y.tolist(),
                        family_ids=groups.tolist(), confirmation_used=False)
