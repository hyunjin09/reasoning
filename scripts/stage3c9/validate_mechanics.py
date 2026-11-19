#!/usr/bin/env python3
"""Independently validate the 16 Stage 3C.9 intervention mechanics."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"
CANDIDATES = ("original_candidate", "counterfactual_candidate")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--route-root", type=Path, required=True)
    return parser.parse_args()


def results(root: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row["base_problem_id"]): row
        for path in sorted(root.glob("**/examples/*/result.json"))
        for row in [read_json(path)]
    }


def finite_flags(value: Any) -> list[bool]:
    flags = []
    if isinstance(value, dict):
        if "finite" in value and isinstance(value["finite"], bool):
            flags.append(value["finite"])
        for item in value.values():
            flags.extend(finite_flags(item))
    elif isinstance(value, list):
        for item in value:
            flags.extend(finite_flags(item))
    elif isinstance(value, float):
        flags.append(math.isfinite(value))
    return flags


def selected_layers(audits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in audits if row.get("layer_selected")]


def main() -> None:
    args = parse_args()
    manifest = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "cohort/validation_manifest.jsonl")}
    analyzed_source = {
        (str(row["base_problem_id"]), int(row["event_id"]), row["window"]): row
        for row in read_jsonl(OUT / "audit/validation_source_sensitivity.jsonl")
    }
    source, checkpoint, routes = results(args.source_root), results(args.checkpoint_root), results(args.route_root)
    if len(manifest) != 8 or set(source) != set(manifest) or set(checkpoint) != set(manifest):
        raise RuntimeError("Source/checkpoint validation outputs must exactly cover eight frozen validation bases")
    if len(routes) != 3 or not set(routes).issubset(set(manifest)):
        raise RuntimeError("Route validation must cover three frozen validation bases")
    event_index, readout_index, suppression, cache_layout = [], [], [], []
    span_selectivity, neighbor_selectivity, route_order, self_patch, replay = [], [], [], [], []
    finite = []
    sign_alignment = []
    streaming_parity = []
    for base, item in manifest.items():
        expected_events = {int(row["event_id"]): row for row in item["events"]}
        source_events = {int(row["event_id"]): row for row in source[base]["events"]}
        checkpoint_events = {int(row["event_id"]): row for row in checkpoint[base]["events"]}
        event_exact = set(source_events) == set(checkpoint_events) == set(expected_events)
        for event_id, expected in expected_events.items():
            raw_source = source_events[event_id]
            raw_checkpoint = checkpoint_events[event_id]
            event_index.append({
                "base_problem_id": base,
                "event_id": event_id,
                "exact": event_exact
                and int(raw_source["span_start_token"]) == int(expected["span_start_token"])
                and int(raw_source["span_end_token"]) == int(expected["span_end_token"])
                and int(raw_checkpoint["span_start_token"]) == int(expected["span_start_token"])
                and int(raw_checkpoint["span_end_token"]) == int(expected["span_end_token"]),
            })
            for condition in ("O", "O_sham", "C", "C_sham"):
                for readout in ("local_use", "final_use"):
                    observed = raw_source["conditions"][condition][readout]
                    if observed.get("streaming_full_prefix_parity") is not None:
                        streaming_parity.append({
                            "phase": "streaming_full_prefix_parity",
                            "base_problem_id": base,
                            **observed["streaming_full_prefix_parity"],
                        })
                    expected_readout = expected["local_use_readout"] if readout == "local_use" else item["final_use_readout"]
                    readout_index.append({
                        "base_problem_id": base,
                        "event_id": event_id,
                        "condition": condition,
                        "readout": readout,
                        "index_exact": int(observed["readout_generated_index"]) == int(expected_readout["token_index"]),
                        "prefix_hash_exact": bool(observed["prefix_hash_exact"] and observed["prefix_sha256"] == expected_readout["history_before_ed_sha256"]),
                    })
                    for window_name, window in observed["windows"].items():
                        if not window["available"]:
                            continue
                        score = window["suppressed"]
                        expected_sources = source[base]["target_positions"]
                        if readout == "local_use":
                            analyzed = analyzed_source[(base, event_id, window_name)]["local_use"]["condition_metrics"][condition]
                            sign = 1.0 if condition in {"O", "O_sham"} else -1.0
                            expected_native = sign * float(window["native"]["D"])
                            expected_suppressed = sign * float(window["suppressed"]["D"])
                            sign_alignment.append({
                                "base_problem_id": base,
                                "event_id": event_id,
                                "window": window_name,
                                "condition": condition,
                                "orientation_exact": float(analyzed["aligned_native_D"]) == expected_native and float(analyzed["aligned_suppressed_D"]) == expected_suppressed,
                                "source_loss_exact": float(analyzed["source_loss"]) == expected_native - expected_suppressed,
                            })
                        for candidate in CANDIDATES:
                            audits = score["candidate_audits"][candidate]
                            suppression.append({
                                "base_problem_id": base,
                                "event_id": event_id,
                                "condition": condition,
                                "readout": readout,
                                "window": window_name,
                                "candidate": candidate,
                                "layer_count_exact": len(audits) == 36 and sorted(int(row["layer_index"]) for row in audits) == list(range(36)),
                                "query_window_exact": all(row["query_positions"] == score["absolute_query_positions"] for row in audits),
                                "target_roi_exact": all(row["source_positions"] == expected_sources for row in audits),
                                "all_heads_exact": all(row["selected_heads"] == list(range(32)) for row in audits),
                                "outside_window_exact": all(float(row["outside_window_max_abs_delta"]) == 0.0 for row in audits),
                                "nonselected_heads_exact": all(float(row["nonselected_head_max_abs_delta"]) == 0.0 for row in audits),
                                "qkv_native": all(float(row["query_max_abs_delta"]) == 0.0 and float(row["key_max_abs_delta"]) == 0.0 and float(row["value_max_abs_delta"]) == 0.0 for row in audits),
                                "attention_native": all(float(row["attention_max_abs_delta"]) == 0.0 for row in audits),
                                "finite": all(row["all_outputs_finite"] for row in audits),
                            })
                        if window.get("deterministic_replay") is not None:
                            replay.append({"phase": "source", "base_problem_id": base, **window["deterministic_replay"]})
            for condition in ("O", "C"):
                local = raw_checkpoint["conditions"][condition]["local_use"]
                for window_name, window in local.get("windows", {}).items():
                    for state_name in ("native", "suppressed"):
                        for candidate in CANDIDATES:
                            audits = selected_layers(window["capture_audits"][state_name][candidate]["cache"])
                            cache_layout.append({
                                "base_problem_id": base,
                                "event_id": event_id,
                                "condition": condition,
                                "window": window_name,
                                "state": state_name,
                                "candidate": candidate,
                                "layer_count_exact": len(audits) == 36,
                                "native_gqa_exact": bool(audits) and all(row["key_shape"][1] == 8 and row["key_shape"][-1] == 128 and row["key_shape"] == row["value_shape"] and row["post_rope_key"] and row["value_projection"] for row in audits),
                            })
                    event_score = window["event_span_rescue"]
                    neighbor_score = window["matched_neighbor_rescue"]
                    for candidate in CANDIDATES:
                        event_audits = selected_layers(event_score["cache_patch_audits"][candidate])
                        neighbor_audits = selected_layers(neighbor_score["cache_patch_audits"][candidate])
                        span_selectivity.append({
                            "base_problem_id": base,
                            "event_id": event_id,
                            "condition": condition,
                            "window": window_name,
                            "candidate": candidate,
                            "layers_exact": len(event_audits) == 36,
                            "positions_exact": bool(event_audits) and all(row["positions_replaced"] == event_score["patch_absolute_positions"] for row in event_audits),
                            "nonselected_exact": bool(event_audits) and all(float(row["nonselected_key_max_abs_delta"]) == 0.0 and float(row["nonselected_value_max_abs_delta"]) == 0.0 for row in event_audits),
                            "visual_invariant": not event_score["visual_kv_donor_patched"] and bool(event_audits) and all(not row["visual_positions_replaced"] for row in event_audits),
                            "non_event_donor_patch": not event_score["non_event_cache_donor_patched"],
                        })
                        neighbor_selectivity.append({
                            "base_problem_id": base,
                            "event_id": event_id,
                            "condition": condition,
                            "window": window_name,
                            "candidate": candidate,
                            "same_width": len(event_score["patch_absolute_positions"]) == len(neighbor_score["patch_absolute_positions"]),
                            "positions_exact": bool(neighbor_audits) and all(row["positions_replaced"] == neighbor_score["patch_absolute_positions"] for row in neighbor_audits),
                            "disjoint": not set(event_score["patch_absolute_positions"]) & set(neighbor_score["patch_absolute_positions"]),
                            "nonselected_exact": bool(neighbor_audits) and all(float(row["nonselected_key_max_abs_delta"]) == 0.0 and float(row["nonselected_value_max_abs_delta"]) == 0.0 for row in neighbor_audits),
                        })
                    controls = window["self_controls"]
                    self_patch.append({
                        "phase": "checkpoint",
                        "base_problem_id": base,
                        "event_id": event_id,
                        "condition": condition,
                        "window": window_name,
                        "native_to_native_exact": controls["native_to_native_exact"],
                        "suppressed_to_suppressed_exact": controls["suppressed_to_suppressed_exact"],
                    })
                    if window.get("deterministic_replay") is not None:
                        replay.append({"phase": "checkpoint", "base_problem_id": base, **window["deterministic_replay"]})
        finite.extend(finite_flags(source[base]))
        finite.extend(finite_flags(checkpoint[base]))
    for base, result in routes.items():
        coordinates = result["coordinates"]
        for condition in ("O", "C"):
            row = result["conditions"][condition]
            for arm in ("prior_checkpoint", "short_history", "joint"):
                expected = coordinates["prior_checkpoint_positions"] if arm == "prior_checkpoint" else coordinates["short_history_positions"]
                expected_absolute = row[arm]["patch_absolute_positions"]
                audits_by_candidate = row["route_patch_audits"][arm]
                for candidate in CANDIDATES:
                    audits = selected_layers(audits_by_candidate[candidate])
                    route_order.append({
                        "base_problem_id": base,
                        "condition": condition,
                        "arm": arm,
                        "candidate": candidate,
                        "generated_positions_exact": row[arm]["patch_generated_indices"] == expected,
                        "absolute_positions_exact": bool(audits) and all(item["positions_replaced"] == expected_absolute for item in audits),
                        "patch_precedes_direct_window": max(expected) < min(coordinates["direct_w8_query_positions"]),
                        "first_query_after_patch": bool(audits) and all(int(item["first_patched_absolute_query"]) == max(expected_absolute) + 1 for item in audits),
                        "visual_invariant": bool(audits) and all(not item["visual_positions_replaced"] for item in audits),
                    })
            self_patch.append({
                "phase": "route",
                "base_problem_id": base,
                "condition": condition,
                "native_to_native_exact": row["native_self_control"]["exact"],
                "suppressed_to_suppressed_exact": None,
            })
            if row.get("deterministic_replay") is not None:
                replay.append({"phase": "route", "base_problem_id": base, **row["deterministic_replay"]})
        finite.extend(finite_flags(result))
    write_json(OUT / "audit/event_index_audit.json", {"rows": event_index, "passed": all(row["exact"] for row in event_index)})
    write_json(OUT / "audit/readout_index_audit.json", {"rows": readout_index, "passed": all(row["index_exact"] and row["prefix_hash_exact"] for row in readout_index)})
    write_json(OUT / "audit/suppression_partition_audit.json", {"rows": suppression, "passed": bool(suppression) and all(all(value for key, value in row.items() if key not in {"base_problem_id", "event_id", "condition", "readout", "window", "candidate"}) for row in suppression)})
    write_json(OUT / "audit/cache_layout.json", {"rows": cache_layout, "passed": bool(cache_layout) and all(row["layer_count_exact"] and row["native_gqa_exact"] for row in cache_layout)})
    write_json(OUT / "audit/span_patch_selectivity.json", {"rows": span_selectivity, "passed": bool(span_selectivity) and all(all(value for key, value in row.items() if key not in {"base_problem_id", "event_id", "condition", "window", "candidate"}) for row in span_selectivity)})
    write_json(OUT / "audit/neighbor_patch_selectivity.json", {"rows": neighbor_selectivity, "passed": bool(neighbor_selectivity) and all(all(value for key, value in row.items() if key not in {"base_problem_id", "event_id", "condition", "window", "candidate"}) for row in neighbor_selectivity)})
    write_json(OUT / "audit/route_patch_order.json", {"rows": route_order, "passed": bool(route_order) and all(all(value for key, value in row.items() if key not in {"base_problem_id", "condition", "arm", "candidate"}) for row in route_order)})
    write_json(OUT / "audit/self_patch_validation.json", {"rows": self_patch, "passed": bool(self_patch) and all(row["native_to_native_exact"] and row.get("suppressed_to_suppressed_exact") is not False for row in self_patch)})
    write_json(OUT / "audit/reproducibility.json", {
        "rows": replay,
        "streaming_full_prefix_parity_diagnostic": streaming_parity,
        "cross_path_exactness_is_readiness_gate": False,
        "calibration_basis": "outputs/a6000_calibration_v2/summaries/a6000_calibration_v2_acceptance.json",
        "passed": bool(replay) and all(row["exact"] for row in replay),
    })
    checks = {
        "1_exact_event_span_indices": all(row["exact"] for row in event_index),
        "2_exact_local_use_readout_indices": all(row["index_exact"] and row["prefix_hash_exact"] for row in readout_index),
        "3_exact_O_C_sign_alignment": bool(sign_alignment) and all(row["orientation_exact"] and row["source_loss_exact"] for row in sign_alignment),
        "4_W8_W16_suppression_isolation": bool(suppression) and all(row["query_window_exact"] and row["outside_window_exact"] for row in suppression),
        "5_target_ROI_only": bool(suppression) and all(row["target_roi_exact"] for row in suppression),
        "6_all_layer_all_head_partition": bool(suppression) and all(row["layer_count_exact"] and row["all_heads_exact"] for row in suppression),
        "7_exact_event_span_KV_positions": bool(span_selectivity) and all(row["positions_exact"] for row in span_selectivity),
        "8_native_GQA_cache_layout": bool(cache_layout) and all(row["native_gqa_exact"] for row in cache_layout),
        "9_visual_KV_invariance": bool(span_selectivity) and all(row["visual_invariant"] for row in span_selectivity) and all(row["visual_invariant"] for row in route_order),
        "10_non_event_cache_invariance": bool(span_selectivity) and all(row["nonselected_exact"] and row["non_event_donor_patch"] for row in span_selectivity),
        "11_matched_neighbor_isolation": bool(neighbor_selectivity) and all(row["same_width"] and row["positions_exact"] and row["disjoint"] and row["nonselected_exact"] for row in neighbor_selectivity),
        "12_route_intervention_ordering": bool(route_order) and all(row["patch_precedes_direct_window"] and row["first_query_after_patch"] for row in route_order),
        "13_native_native_self_patch": bool(self_patch) and all(row["native_to_native_exact"] for row in self_patch),
        "14_suppressed_suppressed_self_patch": any(row.get("suppressed_to_suppressed_exact") is True for row in self_patch) and all(row.get("suppressed_to_suppressed_exact") is not False for row in self_patch),
        "15_deterministic_same_path_replay": bool(replay) and all(row["exact"] for row in replay),
        "16_finite_scores": bool(finite) and all(finite),
    }
    result = {
        "checks": checks,
        "passed_count": sum(checks.values()),
        "total_checks": 16,
        "passed": all(checks.values()),
        "validation_unique_bases": len(manifest),
        "route_validation_unique_bases": len(routes),
    }
    write_json(OUT / "audit/mechanical_validation.json", result)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
