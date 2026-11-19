"""Small family-separated discovery probes and frozen operating points."""
import re

import numpy as np
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ATTENTION = ["visual_mass"]
QK = ["qk_visual_nonvisual","qk_visual_reasoning"]
CONCENTRATION = ["visual_top4_mass","visual_max","visual_entropy","visual_effective_count"]
VISUAL_WORDS = re.compile(r"diagram|image|picture|figure|shown|label|\blook\b|\bsee\b|visual|图|看|标|长度|角|边",re.I)


def columns(spec):
    kind = spec["kind"]
    if kind == "attention":
        return ATTENTION
    if kind == "qk":
        return QK
    if kind == "joint":
        return ATTENTION+QK
    if kind == "extended":
        base = ATTENTION+QK+CONCENTRATION
        return base+["delta_"+k for k in base]
    if kind == "sink_secondary":
        if spec["base_kind"] not in {"joint", "extended"}:
            raise ValueError("Sink comparison must augment the selected primary")
        return columns(dict(kind=spec["base_kind"]))+["sink_mass","delta_sink_mass"]
    raise ValueError("No passive column definition")


def inputs(events,spec):
    kind = spec["kind"]
    if kind == "lexical":
        return [r["lexical_prefix_last32"] for r in events]
    if kind == "position":
        return np.array([[np.log1p(r["prefix_length"]),np.log1p(r["prefix_length"]+r["prompt_length"])] for r in events])
    if kind == "visual_word":
        return np.array([[float(bool(VISUAL_WORDS.search(r["lexical_prefix_last32"]))) ] for r in events])
    if kind == "shallow":
        return np.array([r["shallow_state"] for r in events],dtype=float)
    key = f"{spec['aggregation']}_k{spec['window']}"
    return np.array([[r["features"][key][k] for k in columns(spec)] for r in events],dtype=float)


def pipeline(spec):
    if spec["kind"] == "lexical":
        steps = [("tfidf",TfidfVectorizer(analyzer="char",ngram_range=(2,5),max_features=256,sublinear_tf=True))]
    else:
        steps = [("scale",StandardScaler())]
        if spec["kind"] == "shallow":
            steps.append(("pca",PCA(n_components=16,svd_solver="full")))
    steps.append(("logistic",LogisticRegression(C=spec["C"],class_weight="balanced",solver="liblinear",max_iter=3000,random_state=1234)))
    return Pipeline(steps)


def grouped_oof(events,spec,*,folds=5):
    if any(r["split"] != "discovery" for r in events):
        raise ValueError("Only discovery events may fit/choose probes")
    y = np.array([r["label"] == "T" for r in events],dtype=int)
    groups = np.array([r["family_id"] for r in events])
    if len(set(groups)) < folds or len(set(y)) != 2:
        raise ValueError("Insufficient class/family coverage")
    X = inputs(events,spec)
    splitter = StratifiedGroupKFold(n_splits=folds,shuffle=True,random_state=1234)
    prediction = np.full(len(events),np.nan)
    audit = []
    for train,test in splitter.split(np.zeros(len(events)),y,groups):
        assert not set(groups[train]) & set(groups[test])
        model = pipeline(spec)
        model.fit([X[i] for i in train] if isinstance(X,list) else X[train],y[train])
        prediction[test] = model.predict_proba([X[i] for i in test] if isinstance(X,list) else X[test])[:,1]
        audit.append(dict(train_families=sorted(set(groups[train])),test_families=sorted(set(groups[test])),
            scaler_mean=model.named_steps["scale"].mean_.tolist() if "scale" in model.named_steps else None))
    assert np.isfinite(prediction).all()
    return prediction,audit


def operating_point(y,labels,score):
    y,labels,score = np.asarray(y,dtype=bool),np.asarray(labels),np.asarray(score,dtype=float)
    if not np.isfinite(score).all() or not y.any() or not (labels=="M").any():
        raise ValueError("Operating point needs finite T and M scores")
    candidates = np.unique(np.r_[np.nextafter(score.min(),-np.inf),score])
    results = []
    for threshold in candidates:
        prediction = score > threshold
        recall = float(prediction[y].mean())
        fpr = float(prediction[labels=="M"].mean())
        if fpr <= .2+1e-12:
            results.append(dict(threshold=float(threshold),recall=recall,mention_fpr=fpr,target_met=recall>=.8-1e-12))
    return max(results,key=lambda r:(r["recall"],-r["threshold"]))


def metrics(events,score,threshold):
    y = np.array([r["label"] == "T" for r in events],dtype=int)
    labels = np.array([r["label"] for r in events])
    score = np.asarray(score,dtype=float)
    if len(set(y)) != 2:
        raise ValueError("Metrics need both semantic classes")
    prediction = score > threshold
    fpr,tpr,_ = roc_curve(y,score)
    tm = (labels=="T") | (labels=="M")
    calibration = 0.
    for i in range(5):
        keep = (score>=i/5)&((score<(i+1)/5) if i<4 else (score<=1))
        if keep.any():
            calibration += keep.mean()*abs(score[keep].mean()-y[keep].mean())
    return dict(auroc=float(roc_auc_score(y,score)),auprc=float(average_precision_score(y,score)),
        t_vs_m_auroc=float(roc_auc_score(y[tm],score[tm])) if len(set(y[tm]))==2 else None,
        t_vs_m_auprc=float(average_precision_score(y[tm],score[tm])) if len(set(y[tm]))==2 else None,
        recall=float(prediction[y==1].mean()),all_negative_fpr=float(prediction[y==0].mean()),
        mention_fpr=float(prediction[labels=="M"].mean()) if (labels=="M").any() else None,
        recall_at_fpr_10=float(tpr[fpr<=.1].max()),recall_at_fpr_20=float(tpr[fpr<=.2].max()),
        ece_5_equal_width=float(calibration),brier=float(np.mean((score-y)**2)))


def candidate_specs():
    specs = []
    for kind in ("attention","qk","joint","extended"):
        for aggregation in ("median","trimmed_mean","max"):
            for window in ((4,16,32) if kind=="extended" else (4,)):
                for c in (.01,.1,1.,10.):
                    specs.append(dict(kind=kind,aggregation=aggregation,window=window,C=c))
    for kind in ("lexical","position","visual_word","shallow"):
        for c in (.01,.1,1.,10.):
            specs.append(dict(kind=kind,C=c))
    return specs


def select_discovery(events):
    y = np.array([r["label"]=="T" for r in events],dtype=int)
    labels = np.array([r["label"] for r in events])
    results = []
    for spec in candidate_specs():
        prediction,folds = grouped_oof(events,spec)
        point = operating_point(y,labels,prediction)
        results.append(dict(spec=spec,oof=prediction.tolist(),folds=folds,operating_point=point,
                            metrics=metrics(events,prediction,point["threshold"])))
    def rank(r):
        return (r["operating_point"]["target_met"],r["metrics"]["auroc"],r["metrics"]["t_vs_m_auroc"],-r["spec"]["C"])
    best = {kind:max([r for r in results if r["spec"]["kind"]==kind],key=rank) for kind in sorted({r["spec"]["kind"] for r in results})}
    primary = max([best["joint"],best["extended"]],key=rank)
    # Secondary sink comparison cannot replace the primary deployable feature rule.
    secondary_spec = {**primary["spec"],"kind":"sink_secondary","base_kind":primary["spec"]["kind"]}
    secondary_prediction,secondary_folds = grouped_oof(events,secondary_spec)
    secondary_point = operating_point(y,labels,secondary_prediction)
    secondary = dict(spec=secondary_spec,oof=secondary_prediction.tolist(),folds=secondary_folds,
                     operating_point=secondary_point,metrics=metrics(events,secondary_prediction,secondary_point["threshold"]))
    return dict(primary=primary,best_by_kind=best,candidates=results,secondary_sink=secondary,
                selection_scope="Discovery OOF model selection; these selected OOF metrics are not unbiased held-out claims")
