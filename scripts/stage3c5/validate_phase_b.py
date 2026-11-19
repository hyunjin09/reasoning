#!/usr/bin/env python3
"""Validate disjoint Stage 3C.5 carrier-patch mechanics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c5"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def result_map(root: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row["base_problem_id"]): row
        for path in sorted(root.glob("shard_*/examples/*/result.json"))
        for row in [read_json(path)]
    }


def stage3b0_map() -> dict[str, dict[str, Any]]:
    return {
        str(row["base_problem_id"]): row
        for path in sorted((ROOT / "outputs/stage3b0/raw/shards").glob("cohort_*/examples/*/result.json"))
        for row in [read_json(path)]
    }


def main() -> None:
    config = read_json(OUT / "config/stage3c5_config.json")
    gate = read_json(OUT / "analysis/phase_b_gate.json")
    scopes = read_json(OUT / "config/tpre_layer_scopes.json")["scopes"]
    selected = scopes[gate["selected_layer_scope"]["scope_id"]]
    rows = result_map(OUT / "raw/phase_b_validation")
    prior_q = stage3b0_map()
    if set(rows) != set(config["validation_base_problem_ids"]):
        raise RuntimeError("Phase-B validation cohort mismatch")
    position_rows = []
    patch_rows = []
    self_rows = []
    repeat_rows = []
    capture_rows = []
    state_rows = []
    for base, row in rows.items():
        tensor_path = next((OUT / "raw/phase_b_validation").glob(f"shard_*/examples/{base}/hpre_states.pt"))
        hpre = torch.load(tensor_path, weights_only=True)
        state_rows.append({
            "base_problem_id": base, "tensor_count": len(hpre),
            "all_float32": all(value.dtype == torch.float32 for value in hpre.values()),
            "all_finite": all(bool(torch.isfinite(value).all().item()) for value in hpre.values()),
        })
        q_expected = prior_q[base]["layout"]["groups"]["Q"]
        for target_id, target in row["target_results"].items():
            current = int(target["t_star_absolute_position"])
            visual = set(row["token_groups"]["V"])
            position_rows.append({
                "base_problem_id": base, "target_id": target_id,
                "tpre_exact": int(target["t_pre_generated_index"]) == int(target["t_star_generated_index"]) - 1,
                "Q_stage3b0_exact": target["Q_positions"] == q_expected,
                "Q_nonvisual": not bool(set(target["Q_positions"]) & visual),
                "R_last1_exact": target["R_positions"]["R_last1"] == [current - 1],
                "R_last2_exact": target["R_positions"]["R_last2"] == [current - 2, current - 1],
                "R_last4_exact": target["R_positions"]["R_last4"] == list(range(current - 4, current)),
                "R_nonvisual": not bool(set(target["R_positions"]["R_last4"]) & visual),
                "capture_union_exact": target["capture_positions"] == sorted(set(target["Q_positions"]) | set(target["R_positions"]["R_last4"])),
                "selected_layers_exact": target["selected_layers"] == selected,
            })
            for condition, audits in target["capture_audits"].items():
                for candidate, details in audits.items():
                    calls = details["kv_capture_audit"]
                    selected_calls = [call for call in calls if call["layer_selected"]]
                    capture_rows.append({
                        "base_problem_id": base, "target_id": target_id,
                        "condition": condition, "candidate": candidate,
                        "all_layers_visited": len(calls) == 36 and sorted(call["layer_index"] for call in calls) == list(range(36)),
                        "selected_layers_exact": [call["layer_index"] for call in selected_calls] == selected,
                        "post_rope_and_value": all(call["post_rope_key"] and call["value_projection"] for call in selected_calls),
                        "capture_positions_exact": all(call["positions"] == target["capture_positions"] for call in selected_calls),
                    })
            for carrier, carrier_row in target["carriers"].items():
                if carrier != "h_pre":
                    expected_positions = target["Q_positions"] if carrier == "Q" else target["R_positions"][carrier]
                    if carrier_row["source_positions"] != expected_positions:
                        raise RuntimeError("Carrier source-position drift")
                if carrier_row["repeat_audit"] is not None:
                    repeat_rows.append(carrier_row["repeat_audit"])
                for pair_name, pair in carrier_row["pairs"].items():
                    score = pair["score"]
                    if pair_name in {"self_O", "self_C"}:
                        recipient = pair["recipient"]
                        native = target["native"][recipient]
                        self_rows.append({
                            "base_problem_id": base, "target_id": target_id, "carrier": carrier,
                            "pair": pair_name, "D_exact": float(score["D"]) == float(native["D"]),
                            "original_tokens_exact": score["original_candidate"]["token_log_probabilities"] == native["original_candidate"]["token_log_probabilities"],
                            "counterfactual_tokens_exact": score["counterfactual_candidate"]["token_log_probabilities"] == native["counterfactual_candidate"]["token_log_probabilities"],
                        })
                    for candidate, audits in score["patch_audits"].items():
                        if carrier == "h_pre":
                            valid = bool(
                                len(audits) == 1
                                and audits[0]["positions_replaced"] == [current]
                                and int(audits[0]["noncurrent_positions_changed"]) == 0
                                and bool(audits[0]["current_position_exact_source_match"])
                                and bool(audits[0]["downstream_recompute_verified"])
                            )
                        else:
                            selected_calls = [call for call in audits if call["layer_selected"]]
                            valid = bool(
                                len(audits) == 36
                                and [call["layer_index"] for call in selected_calls] == selected
                                and all(call["positions_replaced"] == carrier_row["source_positions"] for call in selected_calls)
                                and all(int(call["visual_kv_entries_replaced"]) == 0 for call in selected_calls)
                                and all(not bool(call["current_query_kv_replaced"]) for call in selected_calls)
                                and all(float(call["nonselected_key_max_abs_delta"]) == 0.0 for call in selected_calls)
                                and all(float(call["nonselected_value_max_abs_delta"]) == 0.0 for call in selected_calls)
                                and all(int(call["queries_before_threshold_modified"]) == 0 for call in selected_calls)
                                and all(int(call["query_vectors_replaced"]) == 0 for call in selected_calls)
                            )
                        patch_rows.append({
                            "base_problem_id": base, "target_id": target_id, "carrier": carrier,
                            "pair": pair_name, "candidate": candidate, "valid": valid,
                            "finite": bool(score["finite"]),
                        })
    checks = [
        ("exact_seven_validation_bases", len(rows) == 7),
        ("phase_b_gate_was_passed", bool(gate["pass"])),
        ("cache_positions_exact", all(all(value for key, value in row.items() if key not in {"base_problem_id", "target_id"}) for row in position_rows)),
        ("capture_layout_exact", all(all(value for key, value in row.items() if key not in {"base_problem_id", "target_id", "condition", "candidate"}) for row in capture_rows)),
        ("patch_mechanics_exact", all(row["valid"] for row in patch_rows)),
        ("all_scores_finite", all(row["finite"] for row in patch_rows)),
        ("self_patches_transparent", all(row["D_exact"] and row["original_tokens_exact"] and row["counterfactual_tokens_exact"] for row in self_rows)),
        ("deterministic_repeats_exact", bool(repeat_rows) and all(row["exact"] and row["D_max_abs_delta"] == 0 for row in repeat_rows)),
        ("raw_hpre_states_finite", all(row["tensor_count"] == 16 and row["all_float32"] and row["all_finite"] for row in state_rows)),
        ("no_visual_kv_patch", all(not row["visual_kv_donor_patch"] for row in rows.values())),
    ]
    summary = {
        "status": "PASS" if all(value for _, value in checks) else "FAIL",
        "checks": [{"id": index + 1, "name": name, "pass": value} for index, (name, value) in enumerate(checks)],
        "counts": {"bases": len(rows), "position_rows": len(position_rows), "capture_rows": len(capture_rows), "patch_rows": len(patch_rows), "self_rows": len(self_rows), "repeat_rows": len(repeat_rows)},
    }
    write_json(OUT / "audit/cache_position_audit.json", {"rows": position_rows, "all_pass": checks[2][1]})
    write_json(OUT / "audit/state_patch_alignment.json", {"capture_rows": capture_rows, "patch_rows": patch_rows, "self_rows": self_rows, "summary": summary})
    write_json(OUT / "audit/reproducibility.json", {"repeat_rows": repeat_rows, "all_exact": checks[7][1]})
    write_json(OUT / "audit/phase_b_validation_summary.json", summary)
    print(json.dumps(summary, indent=2))
    if summary["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
