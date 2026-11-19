#!/usr/bin/env python3
"""Aggregate exhaustive Stage 3C8 recent-reasoning carrier results."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3c8.analysis import (
    holm_adjust,
    inferential_summary,
    recency_matched_pairs,
    robust_positive,
)
from visual_reasoning.stage3c8.protocol import phase_d_gate


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--fresh-root", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def results(root: Path) -> list[dict[str, Any]]:
    return [read_json(path) for path in sorted(root.glob("**/examples/*/result.json"))]


def aligned(value: float, condition: str) -> float:
    return float(value) if condition == "O" else -float(value)


def aggregate_arm(coordinate: dict[str, Any], getter) -> tuple[float, float, dict[str, Any]]:
    losses, gains, per_condition = [], [], {}
    for condition, scores in coordinate["conditions"].items():
        native = aligned(scores["native"]["D"], condition)
        suppressed = aligned(scores["suppressed"]["D"], condition)
        arm = getter(scores)
        loss = native - suppressed
        gain = aligned(arm["D"], condition) - suppressed
        losses.append(loss)
        gains.append(gain)
        per_condition[condition] = {"suppression_loss": loss, "rescue_gain": gain, "arm_D": float(arm["D"])}
    mean_loss, mean_gain = float(np.mean(losses)), float(np.mean(gains))
    return mean_gain, mean_loss, per_condition


def main() -> None:
    args = parse_args()
    annotations = read_jsonl(args.annotations)
    annotation_lookup = {
        (str(row["base_problem_id"]), str(row["coordinate"]), int(row["generated_index"])): row
        for row in annotations if row["stream"] == "PREVIOUS_REASONING"
    }
    all_recent_rows, position_rows, fixed_rows, span_rows, group_rows, cumulative_rows = [], [], [], [], [], []
    for role, root in (("historical", args.historical_root), ("fresh", args.fresh_root)):
        raw = results(root)
        expected = 24 if role == "historical" else len(read_jsonl(OUT / "cohort/fresh_atlas_manifest.jsonl"))
        if len(raw) != expected:
            raise RuntimeError(f"Phase-B {role} result count mismatch: {len(raw)}/{expected}")
        for result in raw:
            base = str(result["base_problem_id"])
            for coordinate_name, coordinate in result["coordinates"].items():
                current = int(coordinate["current_generated_index"])
                gain, loss, details = aggregate_arm(coordinate, lambda scores: scores["all_recent"])
                all_recent_rows.append({
                    "base_problem_id": base,
                    "cohort_role": role,
                    "coordinate": coordinate_name,
                    "current_generated_index": current,
                    "suppression_loss": loss,
                    "gain": gain,
                    "RR": None if loss == 0 else gain / loss,
                    "condition_metrics": details,
                })
                for position in coordinate["recent_generated_indices"]:
                    gain, loss, details = aggregate_arm(coordinate, lambda scores, p=str(position): scores["per_position"][p])
                    annotation = annotation_lookup[(base, coordinate_name, int(position))]
                    position_rows.append({
                        "base_problem_id": base,
                        "cohort_role": role,
                        "coordinate": coordinate_name,
                        "position": int(position),
                        "distance": current - int(position),
                        "token_id": int(annotation["token_id"]),
                        "token_text": annotation["decoded_text"],
                        "token_class": annotation["lexical_semantic_class"],
                        "visual_alignment": annotation["visual_alignment"],
                        "structural_role": annotation["structural_role"],
                        "reasoning_role": annotation["reasoning_role"],
                        "suppression_loss": loss,
                        "gain": gain,
                        "RR": None if loss == 0 else gain / loss,
                        "condition_metrics": details,
                    })
                for distance in sorted(coordinate["conditions"]["O"]["fixed_position_kv"], key=int):
                    for mode in ("K", "V", "KV"):
                        gain, loss, details = aggregate_arm(coordinate, lambda scores, d=distance, m=mode: scores["fixed_position_kv"][d][m])
                        fixed_rows.append({
                            "base_problem_id": base,
                            "cohort_role": role,
                            "coordinate": coordinate_name,
                            "distance": int(distance),
                            "position": current - int(distance),
                            "mode": mode,
                            "gain": gain,
                            "RR": None if loss == 0 else gain / loss,
                            "suppression_loss": loss,
                            "condition_metrics": details,
                        })
                for span_id, span in {str(row["span_id"]): row for row in coordinate["multi_token_spans"]}.items():
                    gain, loss, details = aggregate_arm(coordinate, lambda scores, key=span_id: scores["span_rescue"][key])
                    span_rows.append({
                        "base_problem_id": base,
                        "cohort_role": role,
                        "coordinate": coordinate_name,
                        "span_id": span_id,
                        "decoded_text": span["decoded_text"],
                        "generated_indices": span["generated_indices"],
                        "token_count": len(span["generated_indices"]),
                        "token_class": span["lexical_semantic_class"],
                        "gain": gain,
                        "RR": None if loss == 0 else gain / loss,
                        "suppression_loss": loss,
                        "condition_metrics": details,
                    })
                for group in coordinate["conditions"]["O"]["type_group_rescue"]:
                    gain, loss, details = aggregate_arm(coordinate, lambda scores, key=group: scores["type_group_rescue"][key])
                    group_rows.append({
                        "base_problem_id": base,
                        "cohort_role": role,
                        "coordinate": coordinate_name,
                        "group": group,
                        "gain": gain,
                        "RR": None if loss == 0 else gain / loss,
                        "suppression_loss": loss,
                        "condition_metrics": details,
                    })
                for width in sorted(coordinate["conditions"]["O"]["fixed_recency_cumulative"], key=int):
                    gain, loss, details = aggregate_arm(coordinate, lambda scores, w=width: scores["fixed_recency_cumulative"][w])
                    cumulative_rows.append({
                        "base_problem_id": base,
                        "cohort_role": role,
                        "coordinate": coordinate_name,
                        "recent_width": int(width),
                        "gain": gain,
                        "RR": None if loss == 0 else gain / loss,
                        "suppression_loss": loss,
                        "condition_metrics": details,
                    })
    sort_key = lambda row: (row["cohort_role"], int(row["base_problem_id"]), row["coordinate"])
    all_recent_rows.sort(key=sort_key)
    position_rows.sort(key=lambda row: (*sort_key(row), row["position"]))
    fixed_rows.sort(key=lambda row: (*sort_key(row), row["distance"], row["mode"]))
    span_rows.sort(key=lambda row: (*sort_key(row), row["generated_indices"][0]))
    group_rows.sort(key=lambda row: (*sort_key(row), row["group"]))
    write_jsonl(OUT / "phase_b_recent/all_recent_cache_reference.jsonl", all_recent_rows)
    write_jsonl(OUT / "phase_b_recent/per_position_rescue.jsonl", position_rows)
    write_jsonl(OUT / "phase_b_recent/fixed_position_kv_decomposition.jsonl", fixed_rows)
    write_jsonl(OUT / "phase_b_recent/span_rescue.jsonl", span_rows)
    write_jsonl(OUT / "phase_b_recent/type_group_rescue.jsonl", group_rows)
    write_jsonl(OUT / "phase_b_recent/fixed_recency_cumulative.jsonl", cumulative_rows)

    fresh_positions = [row for row in position_rows if row["cohort_role"] == "fresh"]
    matched_rows = []
    position_type_stats: dict[str, Any] = {}
    for coordinate in sorted({row["coordinate"] for row in fresh_positions}):
        selected = [row for row in fresh_positions if row["coordinate"] == coordinate]
        coordinate_stats = {}
        classes = sorted({row["token_class"] for row in selected})
        match_by_class = {}
        for token_class in classes:
            pairs = recency_matched_pairs(selected, focal_class=token_class)
            for pair in pairs:
                pair["coordinate"] = coordinate
                pair["comparison_family"] = "lexical_semantic_class"
            matched_rows.extend(pairs)
            by_base: dict[str, list[float]] = defaultdict(list)
            for pair in pairs:
                by_base[pair["base_problem_id"]].append(float(pair["gain_difference"]))
            values = {base: float(np.mean(items)) for base, items in by_base.items()}
            summary = inferential_summary(values)
            summary["inferentially_eligible"] = len(values) >= 12
            match_by_class[token_class] = summary
        eligible = [name for name in classes if match_by_class[name]["inferentially_eligible"]]
        adjusted = holm_adjust([match_by_class[name]["wilcoxon_p"] for name in eligible])
        for name, p_value in zip(eligible, adjusted):
            match_by_class[name]["holm_p"] = p_value
            match_by_class[name]["robust_positive"] = robust_positive(match_by_class[name])
        for name in set(classes) - set(eligible):
            match_by_class[name]["holm_p"] = None
            match_by_class[name]["robust_positive"] = False
        coordinate_stats["recency_matched_type_effects"] = match_by_class
        group_stats = {}
        lexical_groups = sorted({row["group"] for row in group_rows if row["cohort_role"] == "fresh" and row["coordinate"] == coordinate and row["group"].startswith("lexical:")})
        for group in lexical_groups:
            values = {row["base_problem_id"]: float(row["gain"]) for row in group_rows if row["cohort_role"] == "fresh" and row["coordinate"] == coordinate and row["group"] == group}
            summary = inferential_summary(values)
            summary["inferentially_eligible"] = len(values) >= 12
            group_stats[group] = summary
        eligible_groups = [name for name in lexical_groups if group_stats[name]["inferentially_eligible"]]
        adjusted = holm_adjust([group_stats[name]["wilcoxon_p"] for name in eligible_groups])
        for name, p_value in zip(eligible_groups, adjusted):
            group_stats[name]["holm_p"] = p_value
            group_stats[name]["robust_positive"] = robust_positive(group_stats[name])
        for name in set(lexical_groups) - set(eligible_groups):
            group_stats[name]["holm_p"] = None
            group_stats[name]["robust_positive"] = False
        coordinate_stats["joint_type_groups"] = group_stats
        visual_match_stats = {}
        visual_rows = [{**row, "token_class": row["visual_alignment"]} for row in selected]
        for alignment in sorted({row["visual_alignment"] for row in selected}):
            pairs = recency_matched_pairs(visual_rows, focal_class=alignment)
            for pair in pairs:
                pair["coordinate"] = coordinate
                pair["comparison_family"] = "visual_alignment"
            matched_rows.extend(pairs)
            by_base: dict[str, list[float]] = defaultdict(list)
            for pair in pairs:
                by_base[pair["base_problem_id"]].append(float(pair["gain_difference"]))
            values = {base: float(np.mean(items)) for base, items in by_base.items()}
            summary = inferential_summary(values)
            summary["inferentially_eligible"] = len(values) >= 12
            visual_match_stats[alignment] = summary
        eligible_visual = [name for name, row in visual_match_stats.items() if row["inferentially_eligible"]]
        adjusted = holm_adjust([visual_match_stats[name]["wilcoxon_p"] for name in eligible_visual])
        for name, p_value in zip(eligible_visual, adjusted):
            visual_match_stats[name]["holm_p"] = p_value
            visual_match_stats[name]["robust_positive"] = robust_positive(visual_match_stats[name])
        for name in set(visual_match_stats) - set(eligible_visual):
            visual_match_stats[name]["holm_p"] = None
            visual_match_stats[name]["robust_positive"] = False
        coordinate_stats["recency_matched_visual_alignment_effects"] = visual_match_stats
        visual_group_stats = {}
        visual_groups = sorted({
            row["group"] for row in group_rows
            if row["cohort_role"] == "fresh"
            and row["coordinate"] == coordinate
            and row["group"].startswith("visual_alignment:")
        })
        for group in visual_groups:
            values = {
                row["base_problem_id"]: float(row["gain"])
                for row in group_rows
                if row["cohort_role"] == "fresh" and row["coordinate"] == coordinate and row["group"] == group
            }
            summary = inferential_summary(values)
            summary["inferentially_eligible"] = len(values) >= 12
            visual_group_stats[group] = summary
        eligible_visual_groups = [name for name, row in visual_group_stats.items() if row["inferentially_eligible"]]
        adjusted = holm_adjust([visual_group_stats[name]["wilcoxon_p"] for name in eligible_visual_groups])
        for name, p_value in zip(eligible_visual_groups, adjusted):
            visual_group_stats[name]["holm_p"] = p_value
            visual_group_stats[name]["robust_positive"] = robust_positive(visual_group_stats[name])
        for name in set(visual_group_stats) - set(eligible_visual_groups):
            visual_group_stats[name]["holm_p"] = None
            visual_group_stats[name]["robust_positive"] = False
        coordinate_stats["joint_visual_alignment_groups"] = visual_group_stats
        fixed_stats = {}
        fixed_keys = [
            (distance, mode)
            for distance in sorted({row["distance"] for row in fixed_rows if row["cohort_role"] == "fresh" and row["coordinate"] == coordinate})
            for mode in ("K", "V", "KV")
        ]
        for distance, mode in fixed_keys:
            values = {
                row["base_problem_id"]: float(row["gain"])
                for row in fixed_rows
                if row["cohort_role"] == "fresh"
                and row["coordinate"] == coordinate
                and int(row["distance"]) == int(distance)
                and row["mode"] == mode
            }
            fixed_stats[f"distance_{distance}:{mode}"] = inferential_summary(values)
        adjusted = holm_adjust([fixed_stats[key]["wilcoxon_p"] for key in fixed_stats])
        for key, p_value in zip(fixed_stats, adjusted):
            fixed_stats[key]["holm_p"] = p_value
            fixed_stats[key]["robust_positive"] = robust_positive(fixed_stats[key])
        coordinate_stats["fixed_position_kv"] = fixed_stats
        position_type_stats[coordinate] = coordinate_stats
    write_jsonl(OUT / "phase_b_recent/recency_matched_controls.jsonl", matched_rows)
    write_json(OUT / "analysis/position_vs_type_analysis.json", position_type_stats)

    fresh_all = [row for row in all_recent_rows if row["cohort_role"] == "fresh" and row["RR"] is not None]
    rr_by_base: dict[str, list[float]] = defaultdict(list)
    for row in fresh_all:
        rr_by_base[row["base_problem_id"]].append(float(row["RR"]))
    median_all_recent_rr = float(np.median([np.mean(values) for values in rr_by_base.values()]))
    local_or_group_robust = any(
        summary.get("robust_positive", False)
        for coordinate in position_type_stats.values()
        for family in coordinate.values()
        for summary in family.values()
    )
    phase_a = read_json(OUT / "phase_a_tpre/token_type_statistics.json")
    phase_a_robust = {name: bool(summary["robust_positive"]) for name, summary in phase_a["overall_kv_gate"].items()}
    gate = phase_d_gate(
        phase_a_robust=phase_a_robust,
        phase_b_all_recent_median_rr=median_all_recent_rr,
        phase_b_local_or_group_robust=local_or_group_robust,
    )
    gate.update({"fresh_unique_bases": len(rr_by_base), "evaluated_after_phase_a_b_frozen": True, "attention_used": False})
    write_json(OUT / "phase_d_anchor/gate.json", gate)

    boundary_classes = {"CLAUSE_FINAL", "SENTENCE_FINAL", "SPAN_FINAL"}
    boundary_values: dict[str, list[float]] = defaultdict(list)
    for row in fresh_positions:
        boundary_values[row["base_problem_id"]].append(float(row["gain"]) if row["structural_role"] in boundary_classes else -float(row["gain"]))
    write_json(OUT / "analysis/boundary_analysis.json", {
        "note": "Descriptive sign-coded summary; matched token-type controls are primary.",
        "boundary_position_count": sum(row["structural_role"] in boundary_classes for row in fresh_positions),
        "nonboundary_position_count": sum(row["structural_role"] not in boundary_classes for row in fresh_positions),
    })
    write_json(OUT / "analysis/sparse_vs_distributed_analysis.json", {
        "fixed_recency_cumulative": cumulative_rows,
        "interpretation_rule": "Prospectively fixed recent widths 1/2/4/8/16; no outcome-ranked fresh positions.",
        "top_k_outcome_selection_used": False,
    })
    print(json.dumps({"all_recent": len(all_recent_rows), "positions": len(position_rows), "groups": len(group_rows), "phase_d_gate": gate}, indent=2))


if __name__ == "__main__":
    main()
