#!/usr/bin/env python3
"""Validate gated within-block rescue against the frozen broad scan."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c6"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def result_map(root: Path) -> dict[str, dict[str, Any]]:
    return {str(row["base_problem_id"]): row for path in sorted(root.glob("shard_*/examples/*/result.json")) for row in [read_json(path)]}


def exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left["original_candidate"]["token_log_probabilities"] == right["original_candidate"]["token_log_probabilities"]
        and left["counterfactual_candidate"]["token_log_probabilities"] == right["counterfactual_candidate"]["token_log_probabilities"]
    )


def main() -> None:
    config = read_json(OUT / "config/stage3c6_config.json")
    freeze = read_json(OUT / "phase_a_hpre_scan/candidate_region_freeze.json")
    rows = result_map(OUT / "raw/phase_b_validation")
    phase_a = result_map(OUT / "raw/phase_a_validation")
    expected = set(config["validation_base_problem_ids"])
    if set(rows) != expected or set(phase_a) != expected:
        raise RuntimeError("Phase-B validation requires the exact seven validation bases")
    active = {target: value["candidate_region"]["layers"] for target, value in freeze["targets"].items() if value["run_phase_b"]}
    checks = {
        "exact_seven_validation_bases": len(rows) == 7,
        "only_gated_targets_run": True,
        "native_and_suppressed_reproduce_phase_a": True,
        "hpre_rescue_reproduces_phase_a": True,
        "all_frozen_layer_boundary_cells_present": True,
        "current_position_only": True,
        "past_and_visual_kv_never_donor_patched": True,
        "all_self_native_exact": True,
        "all_self_suppressed_exact": True,
        "post_block_next_pre_score_equivalence": True,
        "all_scores_finite": True,
    }
    equivalence_count = 0
    scan_count = 0
    for base, row in rows.items():
        checks["only_gated_targets_run"] &= set(row["target_results"]) == set(active)
        checks["past_and_visual_kv_never_donor_patched"] &= not row["past_token_kv_donor_patched"] and not row["visual_kv_donor_patched"]
        for target_id, region in active.items():
            for condition, source in row["target_results"][target_id]["conditions"].items():
                old = phase_a[base]["target_results"][target_id]["conditions"][condition]
                checks["native_and_suppressed_reproduce_phase_a"] &= exact(source["native"], old["native"]) and exact(source["suppressed"], old["suppressed"])
                expected_keys = {f"L{layer}_{boundary}" for layer in region for boundary in ("h_pre", "h_post_attn", "h_post_block")}
                checks["all_frozen_layer_boundary_cells_present"] &= set(source["scans"]) == expected_keys
                for key, scan in source["scans"].items():
                    scan_count += 1
                    rescue = scan["rescue"]
                    checks["all_self_native_exact"] &= bool(scan["self_native_exact"])
                    checks["all_self_suppressed_exact"] &= bool(scan["self_suppressed_exact"])
                    checks["current_position_only"] &= bool(rescue["current_position_only"] and rescue["boundary_patch_audits_valid"])
                    checks["past_and_visual_kv_never_donor_patched"] &= not rescue["past_token_kv_donor_patched"] and not rescue["visual_kv_donor_patched"]
                    checks["all_scores_finite"] &= bool(rescue["finite"])
                    for audit in rescue["boundary_patch_audits"].values():
                        checks["current_position_only"] &= len(audit) == 1 and int(audit[0]["noncurrent_positions_changed"]) == 0
                    if scan["boundary"] == "h_pre":
                        checks["hpre_rescue_reproduces_phase_a"] &= exact(rescue, old["rescue_by_layer"][str(scan["layer"])]["rescue"])
                for layer in region:
                    if layer + 1 in region:
                        equivalence_count += 1
                        checks["post_block_next_pre_score_equivalence"] &= exact(
                            source["scans"][f"L{layer}_h_post_block"]["rescue"],
                            source["scans"][f"L{layer + 1}_h_pre"]["rescue"],
                        )
    result = {
        "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
        "checks_passed": sum(checks.values()), "checks_total": len(checks),
        "active_targets": active, "scan_cell_count": scan_count,
        "post_block_next_pre_comparison_count": equivalence_count,
    }
    write_json(OUT / "audit/phase_b_validation_summary.json", result)
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
