#!/usr/bin/env python3
"""Independently audit Stage 3C.7 smoke or seven-base validation mechanics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c7"
CANDIDATES = ("original_candidate", "counterfactual_candidate")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--expected-bases", type=int, required=True)
    parser.add_argument("--output-prefix", default="")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def score_exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left[CANDIDATES[0]]["token_log_probabilities"] == right[CANDIDATES[0]]["token_log_probabilities"]
        and left[CANDIDATES[1]]["token_log_probabilities"] == right[CANDIDATES[1]]["token_log_probabilities"]
    )


def main() -> None:
    args = parse_args()
    paths = sorted(args.raw_dir.glob("**/examples/*/result.json"))
    rows = [read_json(path) for path in paths]
    config = read_json(OUT / "config/stage3c7_config.json")
    expected_ids = set(config[f"{'validation' if args.expected_bases <= 7 else 'primary'}_base_problem_ids"])
    actual_ids = {str(row["base_problem_id"]) for row in rows}
    if args.expected_bases == 1:
        expected_ids = {"141"}
    layout_rows, position_rows, delta_rows, selectivity_rows = [], [], [], []
    visual_rows, current_rows, residual_rows, order_rows, self_rows, repeat_rows = [], [], [], [], [], []
    finite_scores: list[bool] = []
    for row in rows:
        base = str(row["base_problem_id"])
        tensor_path = next(path for path in paths if str(read_json(path)["base_problem_id"]) == base).parent / row["state_tensor_artifact"]
        tensors = torch.load(tensor_path, map_location="cpu", weights_only=True)
        tensor_layout_ok = bool(tensors and all(
            tensor.ndim in {2, 4}
            and (tensor.ndim != 4 or tuple(tensor.shape[1:]) == (8, 1, 128))
            and torch.isfinite(tensor).all().item()
            for tensor in tensors.values()
        ))
        for target_id, target in row["target_results"].items():
            expected_downstream = config["residual_boundaries"][target_id]["downstream_cache_layers"]
            for condition, result in target["conditions"].items():
                native, suppressed, arms = result["native"], result["suppressed"], result["arms"]
                finite_scores.extend([native["finite"], suppressed["finite"]] + [arm["finite"] for arm in arms.values()] + [result["q_prompt_control"]["finite"]])
                layout_rows.append({
                    "base_problem_id": base, "target": target_id, "condition": condition,
                    "tpre_tensor_layout_ok": tensor_layout_ok,
                    "expected_native_kv_heads": 8, "expected_head_dimension": 128,
                    "capture_uses_post_rope_key": all(
                        audit.get("post_rope_key", False)
                        for state in ("native", "suppressed") for candidate in CANDIDATES
                        for audit in result["cache_capture_audits"][state][candidate]
                        if audit.get("layer_selected")
                    ),
                    "capture_uses_projected_value": all(
                        audit.get("value_projection", False)
                        for state in ("native", "suppressed") for candidate in CANDIDATES
                        for audit in result["cache_capture_audits"][state][candidate]
                        if audit.get("layer_selected")
                    ),
                })
                position_rows.append({
                    "base_problem_id": base, "target": target_id, "condition": condition,
                    "tpre_generated_index": int(target["tpre_generated_index"]),
                    "current_generated_index": int(target["current_generated_index"]),
                    "tpre_precedes_current_by_one": int(target["tpre_generated_index"]) + 1 == int(target["current_generated_index"]),
                    "tpre_absolute_position": int(native["tpre_absolute_position"]),
                    "same_absolute_position_native_suppressed": native["tpre_absolute_position"] == suppressed["tpre_absolute_position"],
                    "tpre_token_id": int(target["tpre_token_id"]), "tpre_token_text": target["tpre_token_text"],
                })
                for candidate, deltas in result["cache_deltas"].items():
                    for delta in deltas:
                        delta_rows.append({"base_problem_id": base, "target": target_id, "condition": condition, "candidate": candidate, **delta})
                for arm_name in ("C2_K", "C3_V", "C4_KV", "J3_downstream_KV", "J4_joint", "J5_full_KV_plus_residual"):
                    arm = arms[arm_name]
                    for candidate in CANDIDATES:
                        selected = [audit for audit in arm["cache_patch_audits"][candidate] if audit.get("layer_selected")]
                        selectivity_rows.append({
                            "base_problem_id": base, "target": target_id, "condition": condition,
                            "arm": arm_name, "candidate": candidate,
                            "expected_layer_count": len(arm["cache_layers"]), "observed_layer_count": len(selected),
                            "layers_exact": sorted(a["layer_index"] for a in selected) == arm["cache_layers"],
                            "only_tpre_replaced": all(a["positions_replaced"] == [native["tpre_absolute_position"]] and a["non_tpre_key_max_abs_delta"] == 0.0 and a["non_tpre_value_max_abs_delta"] == 0.0 for a in selected),
                            "component_isolated": all(a["unselected_component_key_max_abs_delta"] == 0.0 and a["unselected_component_value_max_abs_delta"] == 0.0 for a in selected),
                        })
                        visual_rows.append({
                            "base_problem_id": base, "target": target_id, "condition": condition,
                            "arm": arm_name, "candidate": candidate,
                            "visual_cache_invariant": not arm["visual_kv_donor_patched"] and all(a["visual_positions_replaced"] == [] for a in selected),
                        })
                        current_rows.append({
                            "base_problem_id": base, "target": target_id, "condition": condition,
                            "arm": arm_name, "candidate": candidate,
                            "current_query_kv_invariant": not arm["current_query_kv_donor_patched"] and all(not a["current_query_position_replaced"] for a in selected),
                            "query_vectors_unpatched": all(a["query_vectors_replaced"] == 0 and a["query_max_abs_delta"] == 0.0 for a in selected),
                            "non_tpre_past_cache_invariant": not arm["past_non_tpre_kv_donor_patched"],
                        })
                reproduction = result["stage3c6_reproduction"]
                residual_rows.append({"base_problem_id": base, "target": target_id, "condition": condition, **reproduction})
                expected_order = (
                    ["L33:h_post_attn", "L34:cache_attention", "L35:cache_attention"]
                    if target_id == "target_a" else ["L35:h_pre", "L35:cache_attention"]
                )
                for candidate in CANDIDATES:
                    residual_audit = arms["J4_joint"]["residual_patch_audits"][candidate][0]
                    expected_residual_events = ["patch", "mlp"] if target_id == "target_a" else ["patch", "attention", "mlp"]
                    order_rows.append({
                        "base_problem_id": base, "target": target_id, "condition": condition,
                        "candidate": candidate, "expected": expected_order,
                        "observed": arms["J4_joint"]["joint_event_order"][candidate],
                        "exact": arms["J4_joint"]["joint_event_order"][candidate] == expected_order,
                        "downstream_scope_exact": arms["J4_joint"]["cache_layers"] == expected_downstream,
                        "residual_audit_valid": arms["J4_joint"]["residual_patch_audits_valid"],
                        "actual_residual_event_order": residual_audit["event_order"],
                        "expected_residual_event_order": expected_residual_events,
                        "actual_residual_event_order_exact": residual_audit["event_order"] == expected_residual_events,
                    })
                controls = result.get("self_controls")
                if controls:
                    self_rows.append({
                        "base_problem_id": base, "target": target_id, "condition": condition,
                        "native_cache_exact": score_exact(controls["native_cache"], native),
                        "suppressed_cache_exact": score_exact(controls["suppressed_cache"], suppressed),
                        "native_residual_exact": score_exact(controls["native_residual"], native),
                        "suppressed_residual_exact": score_exact(controls["suppressed_residual"], suppressed),
                        "q_prompt_exact_suppressed": score_exact(result["q_prompt_control"], suppressed),
                    })
                if result["repeat"] is not None:
                    repeat_rows.append({"base_problem_id": base, "target": target_id, "condition": condition, **result["repeat"]})
    prefix = f"{args.output_prefix}_" if args.output_prefix else ""
    write_json(OUT / f"audit/{prefix}tpre_cache_layout.json", {"rows": layout_rows})
    write_json(OUT / f"audit/{prefix}cache_position_alignment.json", {"rows": position_rows})
    write_json(OUT / f"audit/{prefix}native_suppressed_cache_deltas.json", {"rows": delta_rows, "used_for_selection": False})
    write_json(OUT / f"audit/{prefix}cache_patch_selectivity.json", {"rows": selectivity_rows})
    write_json(OUT / f"audit/{prefix}visual_cache_invariance.json", {"rows": visual_rows})
    write_json(OUT / f"audit/{prefix}current_state_invariance.json", {"rows": current_rows})
    write_json(OUT / f"audit/{prefix}current_query_invariance.json", {"rows": current_rows})
    write_json(OUT / f"audit/{prefix}residual_reproduction.json", {"rows": residual_rows})
    write_json(OUT / f"audit/{prefix}joint_patch_order.json", {"rows": order_rows})
    write_json(OUT / f"audit/{prefix}self_patch_validation.json", {"rows": self_rows})
    write_json(OUT / f"audit/{prefix}reproducibility.json", {"rows": repeat_rows})
    checks = {
        "expected_base_count": len(rows) == args.expected_bases,
        "expected_base_ids": actual_ids == expected_ids,
        "layout": bool(layout_rows) and all(r["tpre_tensor_layout_ok"] and r["capture_uses_post_rope_key"] and r["capture_uses_projected_value"] for r in layout_rows),
        "position": bool(position_rows) and all(r["tpre_precedes_current_by_one"] and r["same_absolute_position_native_suppressed"] for r in position_rows),
        "selectivity": bool(selectivity_rows) and all(r["layers_exact"] and r["only_tpre_replaced"] and r["component_isolated"] for r in selectivity_rows),
        "visual_invariance": bool(visual_rows) and all(r["visual_cache_invariant"] for r in visual_rows),
        "current_invariance": bool(current_rows) and all(r["current_query_kv_invariant"] and r["query_vectors_unpatched"] and r["non_tpre_past_cache_invariant"] for r in current_rows),
        "stage3c6_reproduction": bool(residual_rows) and all(r["native_exact"] and r["suppressed_exact"] and r["residual_exact"] for r in residual_rows),
        "joint_order": bool(order_rows) and all(r["exact"] and r["downstream_scope_exact"] and r["residual_audit_valid"] and r["actual_residual_event_order_exact"] for r in order_rows),
        "self_controls": (
            bool(self_rows) and all(all(v for k, v in r.items() if k.endswith("_exact") or k.endswith("_suppressed")) for r in self_rows)
        ) if args.expected_bases <= 7 else True,
        "repeatability": (bool(repeat_rows) and all(r["exact"] for r in repeat_rows)) if args.expected_bases <= 7 else True,
        "finite": bool(finite_scores) and all(finite_scores),
    }
    summary = {"status": "PASS" if all(checks.values()) else "FAIL", "raw_dir": str(args.raw_dir), "base_count": len(rows), "checks": checks}
    write_json(OUT / f"audit/{prefix}mechanical_validation_summary.json", summary)
    print(json.dumps(summary, indent=2))
    if summary["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
