"""Summarize frozen Value-semantic assays with family-clustered uncertainty."""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from visual_reasoning.stage8a.evaluation import semantic_gate


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    proof = json.loads(Path("outputs/stage8a/audit/gpu_work_complete_v1.json").read_text())
    assert proof["required_gpu_work_complete"]
    selected = json.loads(Path("outputs/stage8a/value/requests_v1.json").read_text())
    state = json.loads(Path(selected["state_analysis"]).read_text())
    assert digest(selected["state_analysis"]) == selected["state_analysis_sha256"]
    state_by_id = {r["event_id"]:r for r in state["events"]}
    values = []
    for path, sha in proof["value_artifact_sha256"].items():
        assert digest(path) == sha
        e = json.loads(Path(path).read_text())
        r = e["results"][0]
        values.append(dict(event_id=e["event_id"], base_id=e["base_id"], family_id=e["family_id"],
                           split=e["split"], label=e["label"], roles=e["analysis_roles"],
                           semantic_minus_sham=r["semantic_minus_sham"],
                           roi_semantic_minus_sham=r["roi_semantic_minus_sham"],
                           semantic_margin_shift=r["margin_shifts"]["semantic"],
                           sham_margin_shift=r["margin_shifts"]["sham"],
                           target_relative_vsd=r["target_relative_vsd"],
                           R=state_by_id[e["event_id"]]["R"],
                           JS=state_by_id[e["event_id"]]["JS"], CE=state_by_id[e["event_id"]]["CE"],
                           runtime_seconds=e["runtime_seconds"], peak_gpu_allocated_bytes=e["peak_gpu_allocated_bytes"]))
    low = [e for e in values if "highR_lowG" in e["roles"]]
    confirmation = [e for e in values if "T_causal_confirmation" in e["roles"]]
    by_split = {split:semantic_gate([e for e in low if e["split"] == split]) for split in ("discovery","confirmation")}
    gate3 = semantic_gate(low)
    total_state = state["combined_highR_lowG"]["events"]
    report = dict(at=datetime.now(timezone.utc).isoformat(), value_events=len(values), gate3=gate3,
                  highR_lowG_by_split=by_split,
                  highR_lowG_T_only=semantic_gate([e for e in low if e["label"] == "T"]),
                  prespecified_T_confirmation=semantic_gate(confirmation),
                  prespecified_T_by_split={split:semantic_gate([e for e in confirmation if e["split"]==split]) for split in ("discovery","confirmation")},
                  coverage=dict(all_frozen_state_events=total_state,evaluable=len(low),
                      fraction=len(low)/total_state if total_state else None,
                      exclusions=selected["missing_highR_lowG"],
                      exclusion_reasons=dict(Counter(e["semantic_unavailable_reason"] for e in selected["missing_highR_lowG"]))),
                  assay_worker_gpu_hours=sum(e["runtime_seconds"] for e in values)/3600,
                  peak_gpu_allocated_bytes=max(e["peak_gpu_allocated_bytes"] for e in values),
                  events=values, request_sha256=digest("outputs/stage8a/value/requests_v1.json"),
                  source_sha256={str(Path(__file__)):digest(__file__),"code/visual_reasoning/stage8a/evaluation.py":digest("code/visual_reasoning/stage8a/evaluation.py")})
    out=Path("outputs/stage8a/analysis/value_v1")
    assert not out.exists()
    out.mkdir(parents=True)
    (out/"value_summary.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout="constrained")
    for split,color in (("discovery","tab:blue"),("confirmation","tab:orange")):
        ev=sorted([e for e in low if e["split"]==split],key=lambda e:e["semantic_minus_sham"])
        axes[0].scatter(range(len(ev)),[e["semantic_minus_sham"] for e in ev],label=split,color=color)
        axes[1].scatter([e["sham_margin_shift"] for e in ev],[e["semantic_margin_shift"] for e in ev],label=split,color=color)
    axes[0].axhline(0,color="black",lw=.7)
    axes[0].set(xlabel="Event order within split (sorted for display)",ylabel="Semantic minus sham (nats)",title=f"Frozen high-R / low-G: {len(low)} evaluable / {total_state}")
    if low:
        limits=[min(min(e["sham_margin_shift"],e["semantic_margin_shift"]) for e in low),max(max(e["sham_margin_shift"],e["semantic_margin_shift"]) for e in low)]
        axes[1].plot(limits,limits,"k--",lw=.7)
    axes[1].set(xlabel="Sham margin shift",ylabel="Semantic margin shift",title="Fixed-routing full-visual Value controls")
    for ax in axes:ax.legend()
    for suffix in ("png","pdf","svg"):fig.savefig(out/f"value_semantics.{suffix}",dpi=180)
    plt.close(fig)
    print(json.dumps(dict(gate3=gate3,T_confirmation=report["prespecified_T_confirmation"],coverage=report["coverage"],gpu_hours=report["assay_worker_gpu_hours"]),indent=2))


if __name__ == "__main__":
    main()
