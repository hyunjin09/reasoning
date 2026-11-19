#!/usr/bin/env python3
"""Independently validate the eight-base Stage 3C8 intervention mechanics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"
CANDIDATES = ("original_candidate", "counterfactual_candidate")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-a-root", type=Path, required=True)
    parser.add_argument("--phase-b-root", type=Path, required=True)
    parser.add_argument("--phase-c-root", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def results(root: Path) -> dict[str, dict[str, Any]]:
    return {str(row["base_problem_id"]): row for path in sorted(root.glob("**/examples/*/result.json")) for row in [read_json(path)]}


def finite_scores(value: Any) -> list[bool]:
    values: list[bool] = []
    if isinstance(value, dict):
        if "finite" in value and isinstance(value["finite"], bool):
            values.append(value["finite"])
        for item in value.values():
            values.extend(finite_scores(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(finite_scores(item))
    return values


def scores_exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left["original_candidate"]["token_log_probabilities"] == right["original_candidate"]["token_log_probabilities"]
        and left["counterfactual_candidate"]["token_log_probabilities"] == right["counterfactual_candidate"]["token_log_probabilities"]
    )


def main() -> None:
    args = parse_args()
    expected = {str(row["base_problem_id"]) for line in (OUT / "cohort/validation_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip() for row in [json.loads(line)]}
    phase_a, phase_b, phase_c = results(args.phase_a_root), results(args.phase_b_root), results(args.phase_c_root)
    if not (set(phase_a) == set(phase_b) == set(phase_c) == expected and len(expected) == 8):
        raise RuntimeError("Mechanical validation roots do not contain the frozen eight bases")
    cache_layout, position_selectivity, group_selectivity = [], [], []
    visual_invariance, t16_rows, cutoff_rows, self_rows, repeat_rows = [], [], [], [], []
    all_finite = []
    for base in sorted(expected, key=int):
        a = phase_a[base]
        all_finite.extend(finite_scores(a))
        for coordinate, target in a["coordinates"].items():
            for condition, condition_row in target["conditions"].items():
                for state_name, candidates in condition_row["capture_audits"].items():
                    for candidate, audits in candidates.items():
                        selected = [row for row in audits if row.get("layer_selected")]
                        cache_layout.append({
                            "base_problem_id": base,
                            "phase": "A",
                            "coordinate": coordinate,
                            "condition": condition,
                            "state": state_name,
                            "candidate": candidate,
                            "layer_count": len(selected),
                            "native_gqa_layout": bool(selected) and all(row["key_shape"][1:] == [8, 1, 128] and row["value_shape"][1:] == [8, 1, 128] and row["post_rope_key"] and row["value_projection"] for row in selected),
                        })
                for mode, arm in condition_row["arms"].items():
                    for candidate in CANDIDATES:
                        selected = [row for row in arm["cache_patch_audits"][candidate] if row.get("layer_selected")]
                        position_selectivity.append({
                            "base_problem_id": base,
                            "phase": "A",
                            "coordinate": coordinate,
                            "condition": condition,
                            "mode": mode,
                            "candidate": candidate,
                            "layers_exact": len(selected) == 20 and sorted(row["layer_index"] for row in selected) == list(range(16, 36)),
                            "position_exact": bool(selected) and all(row["positions_replaced"] == [arm["tpre_absolute_position"]] for row in selected),
                            "nonselected_exact": bool(selected) and all(row["non_tpre_key_max_abs_delta"] == 0 and row["non_tpre_value_max_abs_delta"] == 0 for row in selected),
                            "component_exact": bool(selected) and all(row["unselected_component_key_max_abs_delta"] == 0 and row["unselected_component_value_max_abs_delta"] == 0 for row in selected),
                        })
                        visual_invariance.append({
                            "base_problem_id": base,
                            "phase": "A",
                            "valid": not arm["visual_kv_donor_patched"] and not arm["current_query_kv_donor_patched"] and all(not row["visual_positions_replaced"] and not row["current_query_position_replaced"] for row in selected),
                        })
                controls = condition_row["self_controls"]
                self_rows.append({
                    "base_problem_id": base,
                    "phase": "A",
                    "coordinate": coordinate,
                    "condition": condition,
                    "native_exact": scores_exact(controls["native_self_KV"], condition_row["native"]),
                    "suppressed_exact": scores_exact(controls["suppressed_self_KV"], condition_row["suppressed"]),
                })
                if condition_row["repeat"] is not None:
                    repeat_rows.append({"base_problem_id": base, "phase": "A", **condition_row["repeat"]})

        b = phase_b[base]
        all_finite.extend(finite_scores(b))
        for coordinate, target in b["coordinates"].items():
            expected_window = target["window_generated_indices"]
            expected_absolute = None
            for condition, condition_row in target["conditions"].items():
                for candidate in CANDIDATES:
                    capture = [row for row in condition_row["capture_audits"]["native"][candidate]["cache"] if row.get("layer_selected")]
                    cache_layout.append({
                        "base_problem_id": base,
                        "phase": "B",
                        "coordinate": coordinate,
                        "condition": condition,
                        "candidate": candidate,
                        "layer_count": len(capture),
                        "native_gqa_layout": bool(capture) and all(row["key_shape"][1:] == [8, 16, 128] and row["value_shape"][1:] == [8, 16, 128] for row in capture),
                    })
                    suppressions = condition_row["capture_audits"]["suppressed"][candidate]["suppression"]
                    expected_absolute = condition_row["suppressed"]["absolute_query_positions"]
                    t16_rows.append({
                        "base_problem_id": base,
                        "coordinate": coordinate,
                        "condition": condition,
                        "candidate": candidate,
                        "generated_window_exact": len(expected_window) == 17 and expected_window == list(range(expected_window[-1] - 16, expected_window[-1] + 1)),
                        "layer_count_exact": len(suppressions) == 36,
                        "query_positions_exact": bool(suppressions) and all(row["query_positions"] == expected_absolute for row in suppressions),
                        "gain_zero": bool(suppressions) and all(row["gain"] == 0 for row in suppressions),
                    })
                all_recent = condition_row["all_recent"]
                for candidate in CANDIDATES:
                    selected = [row for row in all_recent["cache_patch_audits"][candidate] if row.get("layer_selected")]
                    group_selectivity.append({
                        "base_problem_id": base,
                        "phase": "B",
                        "arm": "all_recent",
                        "coordinate": coordinate,
                        "condition": condition,
                        "candidate": candidate,
                        "position_count_exact": bool(selected) and all(row["position_count"] == 16 for row in selected),
                        "layers_exact": len(selected) == 36,
                        "nonselected_exact": bool(selected) and all(row["nonselected_key_max_abs_delta"] == 0 and row["nonselected_value_max_abs_delta"] == 0 for row in selected),
                    })
                    visual_invariance.append({
                        "base_problem_id": base,
                        "phase": "B",
                        "valid": not all_recent["visual_kv_donor_patched"] and not all_recent["current_query_kv_donor_patched"] and all(not row["visual_positions_replaced"] and not row["current_query_position_replaced"] for row in selected),
                    })
                for group, arm in condition_row["type_group_rescue"].items():
                    for candidate in CANDIDATES:
                        selected = [row for row in arm["cache_patch_audits"][candidate] if row.get("layer_selected")]
                        group_selectivity.append({
                            "base_problem_id": base,
                            "phase": "B",
                            "arm": group,
                            "coordinate": coordinate,
                            "condition": condition,
                            "candidate": candidate,
                            "position_count_exact": bool(selected) and all(row["positions_replaced"] == arm["selected_absolute_positions"] for row in selected),
                            "layers_exact": len(selected) == 36,
                            "nonselected_exact": bool(selected) and all(row["nonselected_key_max_abs_delta"] == 0 and row["nonselected_value_max_abs_delta"] == 0 for row in selected),
                        })
                controls = condition_row["self_controls"]
                self_rows.append({
                    "base_problem_id": base,
                    "phase": "B",
                    "coordinate": coordinate,
                    "condition": condition,
                    "native_exact": bool(controls["native_self_exact"]),
                    "suppressed_exact": bool(controls["suppressed_self_exact"]),
                })
                if condition_row["repeat"] is not None:
                    repeat_rows.append({"base_problem_id": base, "phase": "B", **condition_row["repeat"]})

        c = phase_c[base]
        all_finite.extend(finite_scores(c))
        for condition, baseline in c["baselines"].items():
            for candidate in CANDIDATES:
                audit = baseline[candidate]["cutoff_audit"]
                cutoff_rows.append({
                    "base_problem_id": base,
                    "condition": condition,
                    "candidate": candidate,
                    "enabled": audit["enabled"],
                    "all_layers": sorted(set(audit["layers_modified"])) == list(range(36)),
                    "starts_at_generation": min(audit["absolute_query_indices"]) == c["prompt_token_count"],
                    "prefill_native": not audit["prefill_modified"],
                })
        for pair, full_q in c["full_q"].items():
            audit = full_q["patch_audit"]
            group_selectivity.append({
                "base_problem_id": base,
                "phase": "C",
                "arm": f"full_q:{pair}",
                "position_count_exact": audit["positions"] == c["question_positions"],
                "layers_exact": len(audit["layers_patched"]) == 36,
                "nonselected_exact": audit["nonselected_key_max_abs_delta"] == 0 and audit["nonselected_value_max_abs_delta"] == 0,
            })
            visual_invariance.append({
                "base_problem_id": base,
                "phase": "C",
                "valid": not audit["forbidden_positions_replaced"],
            })
        for condition, control in c["self_controls"].items():
            self_rows.append({"base_problem_id": base, "phase": "C", "condition": condition, "native_exact": control["exact"], "suppressed_exact": True})
        if c["repeat"] is not None:
            repeat_rows.append({"base_problem_id": base, "phase": "C", **c["repeat"]})

    write_json(OUT / "audit/cache_layout.json", {"rows": cache_layout})
    write_json(OUT / "audit/position_patch_selectivity.json", {"rows": position_selectivity})
    write_json(OUT / "audit/group_patch_selectivity.json", {"rows": group_selectivity})
    write_json(OUT / "audit/visual_cache_invariance.json", {"rows": visual_invariance})
    write_json(OUT / "audit/phase_b_t16_validation.json", {"rows": t16_rows})
    write_json(OUT / "audit/phase_c_cutoff_validation.json", {"rows": cutoff_rows})
    write_json(OUT / "audit/self_patch_validation.json", {"rows": self_rows})
    write_json(OUT / "audit/reproducibility.json", {"rows": repeat_rows})
    tokenizer = read_json(OUT / "audit/tokenizer_span_audit.json")
    checks = {
        "eight_bases": len(expected) == 8,
        "tokenizer_span": tokenizer["status"] == "PASS",
        "cache_layout": bool(cache_layout) and all(row["native_gqa_layout"] and row["layer_count"] in {20, 36} for row in cache_layout),
        "single_position_selectivity": bool(position_selectivity) and all(row["layers_exact"] and row["position_exact"] and row["nonselected_exact"] and row["component_exact"] for row in position_selectivity),
        "group_position_selectivity": bool(group_selectivity) and all(row["position_count_exact"] and row["layers_exact"] and row["nonselected_exact"] for row in group_selectivity),
        "visual_current_invariance": bool(visual_invariance) and all(row["valid"] for row in visual_invariance),
        "phase_b_t16": bool(t16_rows) and all(row["generated_window_exact"] and row["layer_count_exact"] and row["query_positions_exact"] and row["gain_zero"] for row in t16_rows),
        "phase_c_cutoff": bool(cutoff_rows) and all(row["enabled"] and row["all_layers"] and row["starts_at_generation"] and row["prefill_native"] for row in cutoff_rows),
        "self_patches": bool(self_rows) and all(row["native_exact"] and row["suppressed_exact"] for row in self_rows),
        "repeatability": (
            {str(row["phase"]) for row in repeat_rows} == {"A", "B", "C"}
            and all(row["exact"] for row in repeat_rows)
        ),
        "finite": bool(all_finite) and all(all_finite),
    }
    summary = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "base_problem_ids": sorted(expected, key=int)}
    write_json(OUT / "audit/mechanical_validation.json", summary)
    print(json.dumps(summary, indent=2))
    if summary["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
