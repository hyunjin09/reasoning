"""Apply the frozen calibration rule; do not select from confirmation data."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from visual_reasoning.stage8a.localization import joint_window_gate, select_late_window


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    config_path = Path(args.config)
    config = json.loads(config_path.read_text())
    out = Path(args.output)
    assert not out.exists()
    raw = Path(config["output_dir"])
    assert json.loads((raw/"wrapper.json").read_text())["completed"]
    assert digest(config["requests"]) == config["requests_sha256"]
    frozen = json.loads(Path(config["requests"]).read_text())
    expected = {r["event_id"] for r in frozen["requests"]}
    paths = sorted(raw.glob("worker*/events/*.json"))
    records = [json.loads(p.read_text()) for p in paths]
    assert len(records) == len(expected) and {r["event_id"] for r in records} == expected
    assert all(r["completed"] and all(a["self_noop_exact"] and a["selected_routing_fixed"] for a in r["results"]) for r in records)
    for rank in range(2):
        env = json.loads((raw/f"worker{rank}/environment.json").read_text())
        assert env["config_sha256"] == digest(config_path)
        assert json.loads((raw/f"worker{rank}/completed.json").read_text())["completed"]
    algorithm = "code/visual_reasoning/stage8a/localization.py"
    assert digest(algorithm) == config["source_sha256"][algorithm]
    if config["phase"] == "calibration_profile":
        result = select_late_window(records)
    elif config["phase"] == "calibration_joint":
        assert len(config["layer_sets"]) == 1
        assert digest(config["selection"]) == config["selection_sha256"]
        layers = json.loads(Path(config["selection"]).read_text())["selected_layers"]
        result = joint_window_gate(records, layers)
    else:
        raise ValueError("Unknown calibration analysis")
    native_root = Path(config["native_wrapper"]).parent
    native_workers = [json.loads((native_root/f"worker{rank}/completed.json").read_text()) for rank in range(2)]
    result.update(at=datetime.now(timezone.utc).isoformat(), config=str(config_path), config_sha256=digest(config_path),
                  source_sha256=digest(algorithm), raw_sha256={str(p):digest(p) for p in paths},
                  native_examples=sum(w["examples"] for w in native_workers),
                  native_normal_eos=sum(w["normal_eos"] for w in native_workers),
                  native_capped=sum(r["truncated"] for w in native_workers for r in w["results"]),
                  causal_events=len(records), gpu_device_hours=sum(r["runtime_seconds"] for r in records)/3600,
                  inference_scope="Calibration only; no held-out Stage8A gate is established")
    out.mkdir(parents=True)
    summary = out/"summary.json"
    summary.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    if config["phase"] == "calibration_profile":
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
        rng = np.random.default_rng(1234)
        indices = rng.integers(0,len(records),size=(4000,len(records)))
        fig, axes = plt.subplots(3,1,figsize=(10,9),sharex=True)
        fields = [("semantic_minus_sham", "Full visual Values: semantic − sham"),
                  ("roi_semantic_minus_sham", "ROI Values: semantic − sham"),
                  ("target_relative_vsd", "Target removal CE effect − irrelevant removal")]
        statistics = {}
        for axis,(field,label) in zip(axes,fields):
            matrix = np.asarray([[next(a[field] for a in r["results"] if a["layers"] == [l]) for l in range(28)] for r in records])
            med = np.median(matrix,axis=0)
            low,high = np.quantile(np.median(matrix[indices],axis=1),[.025,.975],axis=0)
            for row in matrix:
                axis.plot(range(28),row,color="0.65",alpha=.3,linewidth=.7)
            axis.plot(range(28),med,color="#176B87",linewidth=2,label="Family median")
            axis.fill_between(range(28),low,high,color="#176B87",alpha=.15,label="Pointwise family bootstrap95% interval")
            axis.axhline(0,color="0.3",linewidth=.7,linestyle="--")
            selected = result["selected_layers"]
            axis.axvspan(selected[0]-.5,selected[-1]+.5,color="#E3A008",alpha=.15)
            axis.set_ylabel("nats")
            axis.set_title(label,loc="left",fontsize=11)
            statistics[field] = dict(median=med.tolist(),low=low.tolist(),high=high.tolist())
        axes[0].legend(loc="best",fontsize=8)
        axes[-1].set_xlabel("Language layer (zero-based)")
        axes[-1].set_xticks(range(0,28,2))
        fig.suptitle("2B calibration: descriptive layer profiles; shaded window selected for joint validation",fontsize=11)
        fig.tight_layout()
        for extension in ["png","pdf","svg"]:
            fig.savefig(out/f"layer_profiles.{extension}",dpi=180)
        plt.close(fig)
        (out/"plot_statistics.json").write_text(json.dumps(dict(seed=1234,bootstrap_replicates=4000,
             interval_scope="Pointwise descriptive calibration intervals; selection data, not a confirmatory test",statistics=statistics),indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ["raw_sha256","ranked_windows"]},indent=2))


if __name__ == "__main__":
    main()
