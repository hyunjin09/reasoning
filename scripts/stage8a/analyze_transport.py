"""Apply sealed R/G rules and freeze eligible Value requests without S outcomes."""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

from visual_reasoning.stage8a.confirmation import frozen_predictions
from visual_reasoning.stage8a.transport import (CHEAP_KEYS, binary_metrics, cheap_matrix,
                                               transport_values, weak_transport)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def describe(records):
    families = Counter(r["family_id"] for r in records)
    return dict(events=len(records), families=len(families), family_event_counts=dict(families),
                labels=dict(Counter(r["label"] for r in records)),
                semantic_eligible=sum(r["semantic_eligible"] for r in records),
                source_roles=dict(Counter(r["source_role"] for r in records)),
                T_events=sum(r["label"] == "T" for r in records),
                locally_wrong=sum(not r["local_claim_correct"] for r in records))


def main():
    freeze_path = Path("outputs/stage8a/analysis/discovery_freeze_v1/freeze.json")
    rule = json.loads(freeze_path.read_text())
    assert rule["frozen"] and not rule["confirmation_used"]
    for section, keys in (("retrieval", ("models", "fit", "provenance")), ("cheap", ("models", "fit"))):
        for key in keys:
            assert digest(rule[section][key]) == rule[section][key+"_sha256"]
    rmodels = joblib.load(rule["retrieval"]["models"])
    cheap_models = joblib.load(rule["cheap"]["models"])
    fit = json.loads(Path(rule["retrieval"]["fit"]).read_text())
    provenance = json.loads(Path(rule["retrieval"]["provenance"]).read_text())
    tau_r = rule["retrieval"]["tau_R"]
    all_records, selections, summaries, raw_sha, parent_sha = [], [], {}, {}, {}
    cheap_reports = {}
    panels = {}
    for split in ("discovery", "confirmation"):
        config_path = Path(f"outputs/stage8a/config/measurement_{split}_v1.json")
        config = json.loads(config_path.read_text())
        parent = Path(config["requests"])
        assert digest(parent) == config["requests_sha256"]
        parent_sha[str(parent)] = digest(parent)
        requests = json.loads(parent.read_text())
        assert requests["split"] == split and not requests["preflight_only"]
        output = Path(config["output_dir"])
        assert json.loads((output/"wrapper.json").read_text())["completed"]
        raw = {}
        for path in sorted(output.glob("worker*/events/*.json")):
            e = json.loads(path.read_text())
            assert e["completed"] and e["capture_exact"] and e["self_noop_exact"]
            assert e["event_id"] not in raw and e["split"] == split
            raw[e["event_id"]] = e
            raw_sha[str(path)] = digest(path)
        assert set(raw) == {r["event_id"] for r in requests["requests"]}
        events = [raw[r["event_id"]] for r in requests["requests"]]
        if split == "discovery":
            assert [e["event_id"] for e in events] == provenance["event_order"]
            scores = fit["primary"]["oof"]
        else:
            assert config["discovery_freeze_sha256"] == digest(freeze_path)
            scores = frozen_predictions(events, rmodels, provenance["families"], rule["retrieval"]["primary_kind"])[rule["retrieval"]["primary_kind"]]["score"]
        records = []
        for request, event, score in zip(requests["requests"], events, scores):
            js, ce = transport_values(event)
            high = score > tau_r
            weak = weak_transport(event, rule["transport"])
            record = dict(event_id=event["event_id"], base_id=event["base_id"], family_id=event["family_id"],
                          split=split, label=event["label"], R=float(score), high_R=bool(high), low_G=weak,
                          highR_lowG=bool(high and weak), JS=js, CE=ce,
                          query_only_low_G=bool(js < rule["transport"]["tau_js"]),
                          source_role=request["source_role"], local_claim_correct=request["local_claim_correct"],
                          semantic_eligible=request["semantic_eligible"],
                          semantic_unavailable_reason=request["semantic_unavailable_reason"],
                          target_relative_vsd=event["target_relative_vsd"], roi_relative_vsd=event["roi_relative_vsd"])
            records.append(record)
            roles = []
            if event["event_id"] in requests["causal_confirmation_subset"]:
                roles.append("T_causal_confirmation")
            if high and weak:
                roles.append("highR_lowG")
            if roles and request["semantic_eligible"]:
                assert request["local_claim_correct"] and request["source_role"] == "demanded_source"
                selections.append(dict(request, analysis_roles=roles))
        all_records.extend(records)
        high_records = [r for r in records if r["high_R"]]
        weak_records = [r for r in records if r["highR_lowG"]]
        summaries[split] = dict(all=describe(records), high_R=describe(high_records),
                                highR_lowG=describe(weak_records),
                                highR_query_only_lowG=describe([r for r in high_records if r["query_only_low_G"]]),
                                fraction_of_high_R=len(weak_records)/len(high_records) if high_records else None)
        high_events = [e for e, r in zip(events, records) if r["high_R"]]
        y = np.array([weak_transport(e, rule["transport"]) for e in high_events], dtype=int)
        vals = np.array([transport_values(e) for e in high_events])
        combined_g = np.maximum(vals[:, 0]/rule["transport"]["tau_js"], np.abs(vals[:, 1])/rule["transport"]["tau_abs_ce"])
        cheap_reports[split] = {}
        for key in CHEAP_KEYS:
            x = cheap_matrix(high_events, key)
            correlations = {}
            for name, target in (("JS", vals[:,0]), ("CE", vals[:,1]), ("composite_G", combined_g)):
                correlations[name] = float(spearmanr(x[:,0], target).statistic) if np.ptp(x) and np.ptp(target) else None
            if key in cheap_models:
                model = cheap_models[key]
                score = model["model"].predict_proba(x)[:,1]
                cheap_reports[split][key] = dict(correlations=correlations,
                    metrics=binary_metrics(y, score, model["threshold"]), threshold=model["threshold"],
                    score=score.tolist(), event_order=[e["event_id"] for e in high_events],
                    scope="Held-out frozen" if split == "confirmation" else "In-sample fitted; use frozen cheap_fit.json for OOF selection metrics")
        panels[split] = records
    combined = [r for r in all_records if r["highR_lowG"]]
    gate2 = dict(events_at_least_24=len(combined) >= 24,
                 families_at_least_12=len({r["family_id"] for r in combined}) >= 12,
                 heldout_persistence=any(r["split"] == "confirmation" for r in combined))
    gate2["pass"] = all(gate2.values())
    out = Path("outputs/stage8a/analysis/transport_v1")
    assert not out.exists()
    out.mkdir(parents=True)
    report = dict(at=datetime.now(timezone.utc).isoformat(), discovery_freeze=str(freeze_path),
                  discovery_freeze_sha256=digest(freeze_path), splits=summaries,
                  combined_highR_lowG=describe(combined), gate2=gate2, events=all_records,
                  cheap=cheap_reports, preferred_cheap=rule["cheap"]["preferred"],
                  cheap_cancellation_scope="Exploratory; cannot become main online gate from discovery rank alone",
                  raw_sha256=raw_sha, source_sha256={str(Path(__file__)):digest(__file__),
                      "code/visual_reasoning/stage8a/transport.py":digest("code/visual_reasoning/stage8a/transport.py")})
    (out/"transport_analysis.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    selection = dict(at=report["at"], frozen_before_value_scores=True, discovery_freeze=str(freeze_path),
                     discovery_freeze_sha256=digest(freeze_path), parent_request_sha256=parent_sha,
                     state_analysis=str(out/"transport_analysis.json"), state_analysis_sha256=digest(out/"transport_analysis.json"),
                     requests=selections, highR_lowG_coverage=describe(combined),
                     missing_highR_lowG=[r for r in combined if not r["semantic_eligible"]],
                     rule="Union of first12 input-only eligibleT per split and every source/readout-eligible frozen highR/lowG event; no S outcomes used")
    request_path = Path("outputs/stage8a/value/requests_v1.json")
    assert not request_path.exists()
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(json.dumps(selection, indent=2, allow_nan=False)+"\n")
    fig, axes = plt.subplots(1,2,figsize=(12,5),layout="constrained")
    for ax, (split, records) in zip(axes, panels.items()):
        for label in ("T", "M", "nearby", "nonvisual"):
            selected = [r for r in records if r["label"] == label]
            g = [max(r["JS"]/rule["transport"]["tau_js"],abs(r["CE"])/rule["transport"]["tau_abs_ce"]) for r in selected]
            ax.scatter([r["R"] for r in selected], g, label=label, alpha=.7)
        ax.axvline(tau_r,color="black",ls="--"); ax.axhline(1,color="black",ls="--")
        ax.set_yscale("symlog",linthresh=.001)
        ax.set(xlabel="OOF R" if split=="discovery" else "Frozen held-out R",ylabel="max(JS / tauJS, |CE| / tauCE)",title=split+": weak transport below 1")
        ax.legend()
    for suffix in ("png","pdf","svg"):
        fig.savefig(out/f"routing_transport.{suffix}",dpi=180)
    plt.close(fig)
    print(json.dumps(dict(gate2=gate2,combined=describe(combined),value_requests=len(selections)),indent=2))


if __name__ == "__main__":
    main()
