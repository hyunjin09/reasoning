"""Evaluate the sealed discovery probes once on disjoint confirmation events."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import precision_recall_curve, roc_curve

from visual_reasoning.stage8a.confirmation import frozen_predictions
from visual_reasoning.stage8a.evaluation import metric_intervals, paired_auc_difference


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--discovery-freeze", required=True, type=Path)
    parser.add_argument("--measurement-config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rule = json.loads(args.discovery_freeze.read_text())
    assert rule["frozen"] and rule["confirmation_used"] is False
    retrieval = rule["retrieval"]
    for key in ("models", "fit", "provenance"):
        assert digest(retrieval[key]) == retrieval[key+"_sha256"]
    provenance = json.loads(Path(retrieval["provenance"]).read_text())
    fit = json.loads(Path(retrieval["fit"]).read_text())
    assert provenance["confirmation_used"] is False
    primary_kind = retrieval["primary_kind"]
    assert primary_kind == fit["primary"]["spec"]["kind"]
    # Only the hash-verified, project-generated discovery model bundle is loaded.
    models = joblib.load(retrieval["models"])
    assert models[primary_kind]["spec"] == fit["primary"]["spec"]
    assert models[primary_kind]["threshold"] == fit["primary"]["operating_point"]["threshold"]
    config = json.loads(args.measurement_config.read_text())
    assert config["discovery_freeze"] == str(args.discovery_freeze)
    assert config["discovery_freeze_sha256"] == digest(args.discovery_freeze)
    assert digest(config["requests"]) == config["requests_sha256"]
    frozen = json.loads(Path(config["requests"]).read_text())
    assert frozen["split"] == "confirmation" and not frozen["preflight_only"]
    directory = Path(config["output_dir"])
    assert json.loads((directory/"wrapper.json").read_text())["completed"]
    by_id, raw_sha = {}, {}
    for path in sorted(directory.glob("worker*/events/*.json")):
        event = json.loads(path.read_text())
        assert event["completed"] and event["capture_exact"] and event["self_noop_exact"]
        assert event["event_id"] not in by_id
        by_id[event["event_id"]] = event
        raw_sha[str(path)] = digest(path)
    assert set(by_id) == {r["event_id"] for r in frozen["requests"]}
    events = [by_id[r["event_id"]] for r in frozen["requests"]]
    result = frozen_predictions(events, models, provenance["families"], primary_kind)
    primary = result[primary_kind]
    primary["uncertainty"] = metric_intervals(events, primary["score"], primary["threshold"])
    comparisons = {kind: paired_auc_difference(events, primary["score"], result[kind]["score"])
                   for kind in ("lexical", "position")}
    gate = dict(auroc_at_least_080=primary["metrics"]["auroc"] >= .8,
                mention_fpr_at_most_020=primary["metrics"]["mention_fpr"] <= .2,
                beats_lexical=comparisons["lexical"]["positive_supported"],
                beats_position=comparisons["position"]["positive_supported"])
    gate["pass"] = all(gate.values())
    assert not args.output.exists()
    args.output.mkdir(parents=True)
    report = dict(at=datetime.now(timezone.utc).isoformat(), primary_kind=primary_kind,
                  event_order=[e["event_id"] for e in events], events=len(events),
                  families=len({e["family_id"] for e in events}), models=result,
                  paired_primary_minus_baseline=comparisons, gate1=gate,
                  scope="Held-out confirmation; frozen discovery normalization/features/thresholds; no refitting",
                  discovery_freeze=str(args.discovery_freeze), discovery_freeze_sha256=digest(args.discovery_freeze),
                  measurement_config=str(args.measurement_config), measurement_config_sha256=digest(args.measurement_config),
                  requests=config["requests"], requests_sha256=config["requests_sha256"], raw_sha256=raw_sha,
                  source_sha256={p:digest(p) for p in (str(Path(__file__)),
                    "code/visual_reasoning/stage8a/confirmation.py", "code/visual_reasoning/stage8a/evaluation.py",
                    "code/visual_reasoning/stage8a/probes.py")})
    (args.output/"retrieval_confirmation.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    y = np.array([e["label"] == "T" for e in events])
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), layout="constrained")
    for kind in (primary_kind, "attention", "qk", "lexical", "position"):
        prediction = result[kind]["score"]
        fpr, tpr, _ = roc_curve(y, prediction)
        precision, recall, _ = precision_recall_curve(y, prediction)
        axes[0, 0].plot(fpr, tpr, label=kind)
        axes[0, 1].plot(recall, precision, label=kind)
    axes[0, 0].plot([0, 1], [0, 1], "k--", lw=.5)
    axes[0, 0].set(xlabel="False-positive rate", ylabel="T recall", title="Frozen confirmation ROC")
    axes[0, 1].set(xlabel="T recall", ylabel="Precision", title="Frozen confirmation precision–recall")
    axes[0, 0].legend()
    scores = np.asarray(primary["score"])
    for label in ("T", "M", "nearby", "nonvisual"):
        selected = np.array([e["label"] == label for e in events])
        axes[1, 0].hist(scores[selected], bins=np.linspace(0, 1, 11), histtype="step", label=label)
    axes[1, 0].axvline(primary["threshold"], color="black", ls="--")
    axes[1, 0].set(xlabel="Frozen retrieval probability", ylabel="Events", title="Semantic labels and frozen threshold")
    axes[1, 0].legend()
    kinds = list(result)
    axes[1, 1].barh(kinds, [result[k]["metrics"]["auroc"] for k in kinds])
    axes[1, 1].axvline(.8, color="black", ls="--")
    axes[1, 1].set(xlim=(0, 1), xlabel="Held-out AUROC", title="Primary, ablations and controls")
    for suffix in ("png", "pdf", "svg"):
        fig.savefig(args.output/f"retrieval_confirmation.{suffix}", dpi=180)
    plt.close(fig)
    print(json.dumps(dict(gate1=gate, primary=primary["metrics"], events=len(events)), indent=2))


if __name__ == "__main__":
    main()
