"""Freeze input-only main families after the completed 2B Gate0 checks."""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage8a.cohort import freeze_cohort


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x") as f:
        f.write(json.dumps(obj, indent=2, ensure_ascii=False)+"\n")


def main():
    at = datetime.now(timezone.utc).isoformat()
    native = Path("outputs/stage8a/native/calibration_v2")
    mechanics = Path("outputs/stage8a/mechanics/v2")
    joint_path = Path("outputs/stage8a/localization/analysis_joint_v1/summary.json")
    joint = json.loads(joint_path.read_text())
    checks = [json.loads((mechanics/f"worker{r}/completed.json").read_text()) for r in range(2)]
    required = ("native_generation_repeat_exact", "native_streaming_128_logits_exact", "all_28_layer_capture_exact", "all_layer_cache_exact", "fixed_route_self_exact", "fixed_routing_exact", "cache_isolation_exact")
    assert all(all(c[k] for k in required) for c in checks)
    assert joint["native_normal_eos"] >= 10 and joint["visual_transfer_supported"] and joint["target_selectivity_supported"]
    evidence = [joint_path, native/"wrapper.json", mechanics/"wrapper.json"]
    evidence += [mechanics/f"worker{r}/completed.json" for r in range(2)]
    gate0 = dict(at=at, status="PASS", native_examples=joint["native_examples"], native_normal_eos=joint["native_normal_eos"], native_capped=joint["native_capped"],
                 calibration_events=joint["causal_events"], selected_layers=joint["selected_layers"], selected_heads=list(range(16)),
                 joint_semantic_minus_sham_family_median=joint["family_median_semantic_minus_sham"], joint_positive_family_fraction=joint["positive_family_fraction"],
                 target_vsd_family_median=joint["family_median_target_relative_vsd"], target_positive_fraction=joint["positive_vsd_fraction"],
                 evidence_sha256={str(p):digest(p) for p in evidence}, scope="Technical calibration only; Gates1–3 remain untested.")
    save("outputs/stage8a/audit/gate0_pass_v1.json", gate0)
    inventory_path = Path("outputs/stage8a/cohort/reusable_asset_inventory.json")
    inventory = json.loads(inventory_path.read_text())
    calibration_path = Path("outputs/stage8a/cohort/calibration_manifest.jsonl")
    calibration = [json.loads(line)["base_id"] for line in calibration_path.read_text().splitlines()]
    selected = freeze_cohort(inventory["candidates"], inventory["deduplicated_order"], calibration)
    for label, rows in (("main", selected["main"]), ("reserve", selected["reserve"])):
        with Path(f"outputs/stage8a/cohort/{label}_manifest_v1.jsonl").open("x") as f:
            for r in rows:
                assert digest(r["image"]) == r["image_sha256"]
                assert digest(r["asset_metadata"]) == r["asset_metadata_sha256"]
                f.write(json.dumps(r, ensure_ascii=False)+"\n")
    freeze = {k:v for k,v in selected.items() if k not in ("main", "reserve")}
    freeze.update(at=at, seed=1234, ordering="Previously frozen input-only inventory order, one representative per connected family; alternating discovery/confirmation, grouped for balanced two-rank launch.",
                  counts=dict(Counter(r["split"] for r in selected["main"])), reserve_counts=dict(Counter(r["split"] for r in selected["reserve"])),
                  prior_stage_counts=dict(Counter(r["prior_stage"] for r in selected["main"])),
                  source_sha256={str(p):digest(p) for p in (inventory_path, calibration_path, Path(__file__), Path("code/visual_reasoning/stage8a/cohort.py"))},
                  reserve_policy="Expand only for semantic event yield, in frozen within-split order; never for attention, causal effects, model accuracy or failed scientific gates.",
                  confirmation_policy="Native traces may be generated now. No confirmation features, outcomes, fitting or threshold evaluation until discovery rule is frozen.")
    save("outputs/stage8a/cohort/main_freeze_v1.json", freeze)
    config = json.loads(Path("outputs/stage8a/config/calibration_native_v2.json").read_text())
    for k in ("retry_of", "retry_reason"):
        config.pop(k, None)
    config.update(frozen_at=at, manifest="outputs/stage8a/cohort/main_manifest_v1.jsonl", output_dir="outputs/stage8a/native/main_v1",
                  gate0="outputs/stage8a/audit/gate0_pass_v1.json", cohort_freeze="outputs/stage8a/cohort/main_freeze_v1.json")
    config["manifest_sha256"] = digest(config["manifest"])
    config["gate0_sha256"] = digest(config["gate0"])
    config["cohort_freeze_sha256"] = digest(config["cohort_freeze"])
    for p,h in config["source_sha256"].items():
        assert digest(p) == h, p
        target = Path("outputs/stage8a/audit/source_snapshots/main_native_v1")/p
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as f:
            f.write(Path(p).read_bytes())
    save("outputs/stage8a/config/main_native_v1.json", config)
    print(json.dumps({"gate0":gate0,"counts":freeze["counts"],"reserve":freeze["reserve_counts"],"alias_excluded_bases":freeze["alias_excluded_bases"],"main_config_sha256":digest("outputs/stage8a/config/main_native_v1.json")},indent=2))


if __name__ == "__main__":
    main()
