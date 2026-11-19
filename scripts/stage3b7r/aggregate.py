#!/usr/bin/env python3
"""Aggregate the prospectively frozen Stage 3B.7-R causal stages."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3b4.metrics import bootstrap_summary, one_sided_wilcoxon_greater
from visual_reasoning.stage3b4.protocol import holm_adjust
from visual_reasoning.stage3b7.protocol import classify_kv_mechanism
from visual_reasoning.stage3b7r.protocol import (
    bootstrap_median_ci,
    flatten_scoring_results,
    paired_margins,
    primary_roi_gate,
    select_historical_visual_row,
    spatial_category,
    target_validation_gate,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7r"
sys.path.insert(0, str(ROOT / "scripts/stage3b7"))
from aggregate import normalize_kv, normalize_spatial  # noqa: E402


SPATIAL_FILES = {
    "all_visual": "all_visual_results.jsonl",
    "target_roi": "target_roi_results.jsonl",
    "visual_complement": "complement_results.jsonl",
    "irrelevant_roi": "irrelevant_roi_results.jsonl",
    "target_ring": "ring_results.jsonl",
}
KV_FILES = {"K": "k_only_results.jsonl", "V": "v_only_results.jsonl", "KV": "kv_results.jsonl"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("validation_a", "primary_a", "validation_b", "primary_b"), required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--expected-bases", type=int, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evidence_type_lookup() -> dict[str, str]:
    """Load descriptive evidence types from the two frozen annotation sets."""

    paths = (
        ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl",
        OUT / "validation_cohort/annotations/discriminative_event_annotations.jsonl",
    )
    lookup: dict[str, str] = {}
    for path in paths:
        for row in read_jsonl(path):
            base_id = str(row["base_problem_id"])
            evidence_type = str(row["evidence_type"])
            if base_id in lookup and lookup[base_id] != evidence_type:
                raise RuntimeError(f"Conflicting evidence types for base {base_id}")
            lookup[base_id] = evidence_type
    return lookup


def flatten(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return flatten_scoring_results(rows, evidence_types=evidence_type_lookup())


def load_raw(root: Path, prefix: str, expected: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    directories = [root / f"{prefix}_{rank:02d}" for rank in range(2)]
    if not all((path / "result.json").is_file() for path in directories):
        raise RuntimeError(f"Both completed raw shards are required: {directories}")
    summaries = [read_json(path / "result.json") for path in directories]
    rows = [row for path in directories for row in read_jsonl(path / "results.jsonl")]
    if len(rows) != expected or len({str(row["base_problem_id"]) for row in rows}) != expected:
        raise RuntimeError(f"Expected {expected} unique bases, observed {len(rows)}")
    return rows, summaries


def target_id(row: dict[str, Any]) -> str:
    return str(row.get("target_id") or row["cell_id"])


def target_config_lookup() -> dict[str, dict[str, Any]]:
    config = read_json(OUT / "config/stage3b7r_config.json")
    return {str(row["cell_id"]): row for row in config["targets"]}


def stage3b6_source_paths() -> dict[tuple[str, str], Path]:
    found: dict[tuple[str, str], Path] = {}
    for path in sorted((ROOT / "outputs/stage3b6/scoring/raw").glob("source_*/examples/*/result.json")):
        base = path.parent.name
        row = read_json(path)
        for cell in row["cells"]:
            if any(unit["source_group"] == "V" for unit in cell["unit_results"]):
                found[(base, str(cell["cell_id"]))] = path
    return found


def historical_v_row(
    path: Path | None,
    cell_id: str,
    unit_id: str,
    heads: list[int],
) -> dict[str, Any] | None:
    if path is None:
        return None
    return select_historical_visual_row(
        read_json(path),
        cell_id=cell_id,
        unit_id=unit_id,
        heads=heads,
    )


def effect_summary(rows: list[dict[str, Any]], *, value: str, ratio: str | None = None) -> dict[str, Any]:
    values = [float(row[value]) for row in rows]
    summary = bootstrap_summary(values, seed=1234, resamples=10_000)
    ratios = [float(row[ratio]) for row in rows if ratio and row.get(ratio) is not None and math.isfinite(float(row[ratio]))]
    shams = [float(row["sham_to_semantic_ratio"]) for row in rows if row.get("sham_to_semantic_ratio") is not None and math.isfinite(float(row["sham_to_semantic_ratio"]))]
    return {
        "base_count": len(rows),
        "mean_effect": summary["mean"],
        "median_effect": summary["median"],
        "bootstrap_95_CI": summary["bootstrap_95_CI"],
        "bootstrap_resamples": summary["bootstrap_resamples"],
        "raw_one_sided_wilcoxon_p": one_sided_wilcoxon_greater(values),
        "bidirectional_count": sum(bool(row["bidirectionally_source_consistent"]) for row in rows),
        "bidirectional_fraction": float(np.mean([bool(row["bidirectionally_source_consistent"]) for row in rows])),
        "median_ratio": statistics.median(ratios) if ratios else None,
        "median_old_sham_to_semantic_ratio_secondary": statistics.median(shams) if shams else None,
        "all_self_exact": all(bool(row["all_self_restorations_exact"]) for row in rows),
        "all_scores_finite": all(bool(row["all_scores_finite"]) for row in rows),
        "all_head_and_source_isolation": all(
            bool(row["mechanical_audit"]["all_query_head_selectivity_valid"])
            and bool(row["mechanical_audit"]["all_source_group_isolation_valid"])
            for row in rows
        ),
    }


def robust(summary: dict[str, Any], holm: dict[str, Any]) -> bool:
    return bool(
        float(summary["median_effect"]) > 0.0
        and float(summary["bootstrap_95_CI"][0]) > 0.0
        and bool(holm["rejected"])
        and float(summary["bidirectional_fraction"]) >= 0.75
        and bool(summary["all_self_exact"])
        and bool(summary["all_scores_finite"])
        and bool(summary["all_head_and_source_isolation"])
    )


def margin_summary(target_rows: list[dict[str, Any]], irrelevant_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_base = {str(row["base_problem_id"]): row for row in irrelevant_rows}
    targets = np.asarray([float(row["BPR"]) for row in target_rows], dtype=np.float64)
    shams = np.asarray([float(row["sham_effect"]) for row in target_rows], dtype=np.float64)
    irrelevant = np.asarray([float(by_base[str(row["base_problem_id"])]["BPR"]) for row in target_rows], dtype=np.float64)
    sham_margin, irrelevant_margin = paired_margins(targets, shams, irrelevant)
    sham_ci = bootstrap_median_ci(sham_margin, iterations=10_000, seed=1235)
    irrelevant_ci = bootstrap_median_ci(irrelevant_margin, iterations=10_000, seed=1236)
    return {
        "base_count": len(target_rows),
        "sham_margin_median": float(np.median(sham_margin)),
        "sham_margin_bootstrap_95_CI": list(sham_ci),
        "irrelevant_margin_median": float(np.median(irrelevant_margin)),
        "irrelevant_margin_bootstrap_95_CI": list(irrelevant_ci),
        "target_greater_irrelevant_fraction": float(np.mean(targets > np.abs(irrelevant))),
        "per_base": [
            {
                "base_problem_id": str(row["base_problem_id"]),
                "target_effect": float(targets[index]),
                "sham_effect": float(shams[index]),
                "irrelevant_effect": float(irrelevant[index]),
                "sham_margin": float(sham_margin[index]),
                "irrelevant_margin": float(irrelevant_margin[index]),
            }
            for index, row in enumerate(target_rows)
        ],
    }


def validation_a(raw_root: Path, prefix: str, expected: int) -> None:
    bases, shards = load_raw(raw_root, prefix, expected)
    rows = normalize_spatial(flatten(bases))
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["cell_id"]), str(row["spatial_arm"]))].append(row)
    targets = target_config_lookup()
    global_checks = {
        "fresh_base_count_in_frozen_range": 12 <= expected <= 16,
        "all_shards_mechanical_pass": all(bool(row["all_mechanical_controls_passed"]) for row in shards),
        "all_condition_layout_exact": all(bool(base["condition_layout_exact"]) for base in bases),
        "all_roi_mappings_exact": all(bool(base["mechanical_controls"]["all_roi_mappings_exact"]) for base in bases),
        "all_determinism_repeats_exact": all(
            shard["determinism_repeat"] is not None and bool(shard["determinism_repeat"]["exact_public_result_match"])
            for shard in shards
        ),
    }
    semantic_rows = []
    statistics_rows = []
    eligible = []
    for cell, config_target in targets.items():
        target_rows = sorted(grouped[(cell, "target_roi")], key=lambda row: int(row["base_problem_id"]))
        irrelevant_rows = sorted(grouped[(cell, "irrelevant_roi")], key=lambda row: int(row["base_problem_id"]))
        all_v_rows = sorted(grouped[(cell, "all_visual")], key=lambda row: int(row["base_problem_id"]))
        if not all(len(group) == expected for group in (target_rows, irrelevant_rows, all_v_rows)):
            raise RuntimeError(f"Incomplete validation arm for {cell}")
        if not (
            [row["base_problem_id"] for row in target_rows]
            == [row["base_problem_id"] for row in irrelevant_rows]
            == [row["base_problem_id"] for row in all_v_rows]
        ):
            raise RuntimeError(f"Validation arms are not paired by base for {cell}")
        target_effects = np.asarray([float(row["BPR"]) for row in target_rows])
        sham_effects = np.asarray([float(row["sham_effect"]) for row in target_rows])
        irrelevant_effects = np.asarray([float(row["BPR"]) for row in irrelevant_rows])
        consistency = np.asarray([bool(row["bidirectionally_source_consistent"]) for row in target_rows])
        semantic = target_validation_gate(
            target_effects=target_effects,
            sham_effects=sham_effects,
            irrelevant_effects=irrelevant_effects,
            source_consistent=consistency,
            bootstrap_iterations=10_000,
            seed=1234,
        )
        all_v_tendency = {
            "median": float(np.median([float(row["BPR"]) for row in all_v_rows])),
            "bidirectional_fraction": float(np.mean([bool(row["bidirectionally_source_consistent"]) for row in all_v_rows])),
        }
        all_v_tendency["passed"] = bool(all_v_tendency["median"] > 0.0 and all_v_tendency["bidirectional_fraction"] >= 0.75)
        target_mechanics = {
            "self_swap_transparent": all(bool(row["all_self_restorations_exact"]) for arm in PHASE_A_ARMS for row in grouped[(cell, arm)]),
            "non_target_heads_recipient_native": all(bool(row["mechanical_audit"]["all_query_head_selectivity_valid"]) for arm in PHASE_A_ARMS for row in grouped[(cell, arm)]),
            "source_position_isolation_exact": all(bool(row["mechanical_audit"]["all_source_group_isolation_valid"]) for arm in PHASE_A_ARMS for row in grouped[(cell, arm)]),
            "bidirectional_swap_mechanics": all(set(row["recipient_scores"]) == {"O", "C"} for arm in PHASE_A_ARMS for row in grouped[(cell, arm)]),
            "finite_scores_only": all(bool(row["all_scores_finite"]) for arm in PHASE_A_ARMS for row in grouped[(cell, arm)]),
            "all_visual_legacy_implementation_exact": all(bool(row["legacy_all_v_recipient_scores_exact"]) for row in all_v_rows),
            "gqa_architecture_validated_at_runtime": True,
        }
        target_mechanical_pass = bool(all(target_mechanics.values()) and all(global_checks.values()))
        passed = bool(target_mechanical_pass and all_v_tendency["passed"] and semantic["semantic_pass"])
        semantic_row = {
            "target_id": config_target["target_id"],
            "cell_id": cell,
            "heads": config_target["heads"],
            **semantic,
            "all_visual_stage3b6_tendency": all_v_tendency,
            "mechanical_checks": target_mechanics,
            "mechanical_pass": target_mechanical_pass,
            "validation_pass": passed,
            "old_ratio_secondary_only": True,
        }
        semantic_rows.append(semantic_row)
        statistics_rows.extend({"cell_id": cell, "spatial_arm": arm, **effect_summary(grouped[(cell, arm)], value="BPR", ratio="PRR")} for arm in PHASE_A_ARMS)
        if passed:
            eligible.append(config_target)
    ensure_directory(OUT / "validation")
    write_json(OUT / "validation/mechanical_validation.json", {"global_checks": global_checks, "all_global_checks_pass": all(global_checks.values()), "target_checks": [{"target_id": row["target_id"], "mechanical_checks": row["mechanical_checks"], "mechanical_pass": row["mechanical_pass"]} for row in semantic_rows]})
    write_jsonl(OUT / "validation/semantic_validation_results.jsonl", semantic_rows)
    write_json(OUT / "validation/semantic_validation_statistics.json", {"base_count": expected, "target_results": semantic_rows, "arm_statistics": statistics_rows, "paired_margin_gate_primary": True, "old_ratio_secondary_only": True})
    write_json(OUT / "validation/eligible_targets.json", {"frozen_at": datetime.now(timezone.utc).isoformat(), "target_specific_gate": True, "target_count": len(eligible), "targets": eligible, "both_failed_stop_before_primary": len(eligible) == 0})
    lines = ["# Stage 3B.7-R fresh validation", "", f"Fresh validation used **{expected}** independent, disjoint base problems.", ""]
    for row in semantic_rows:
        lines.extend([
            f"## {row['target_id']} — {'PASS' if row['validation_pass'] else 'FAIL'}", "",
            f"- Target median BPR: `{row['target_median']:.6g}`; 95% bootstrap CI `{row['target_median_ci']}`",
            f"- Bidirectional fraction: `{row['bidirectional_fraction']:.3f}`",
            f"- Target-minus-|sham| median: `{row['sham_margin_median']:.6g}`; CI `{row['sham_margin_median_ci']}`",
            f"- Target-minus-|irrelevant| median: `{row['irrelevant_margin_median']:.6g}`; CI `{row['irrelevant_margin_median_ci']}`",
            f"- All-V tendency pass: `{row['all_visual_stage3b6_tendency']['passed']}`",
            f"- Failed semantic conditions: `{row['failed_conditions']}`", "",
        ])
    lines.extend(["The historical sham/semantic ratio is reported only as a secondary diagnostic. Attention was not used for selection or gating.", ""])
    write_text(OUT / "validation/validation_report.md", "\n".join(lines))


PHASE_A_ARMS = ("all_visual", "target_roi", "visual_complement", "irrelevant_roi", "target_ring")


def primary_a(raw_root: Path, prefix: str, expected: int) -> None:
    bases, shards = load_raw(raw_root, prefix, expected)
    eligible = read_json(OUT / "validation/eligible_targets.json")["targets"]
    if not eligible:
        raise RuntimeError("Both fresh targets failed; primary scoring is prohibited")
    rows = normalize_spatial(flatten(bases))
    expected_rows = expected * len(eligible) * len(PHASE_A_ARMS)
    if len(rows) != expected_rows:
        raise RuntimeError(f"Expected {expected_rows} primary spatial rows, observed {len(rows)}")
    ensure_directory(OUT / "scoring")
    for arm, filename in SPATIAL_FILES.items():
        write_jsonl(OUT / "scoring" / filename, [row for row in rows if row["spatial_arm"] == arm])
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["cell_id"]), str(row["spatial_arm"]))].append(row)
    primary_arms = ("all_visual", "target_roi", "visual_complement", "irrelevant_roi")
    statistics_rows = []
    p_values = {}
    for cell, arm in sorted(grouped):
        summary = {"test_id": f"{cell}__{arm}", "cell_id": cell, "spatial_arm": arm, **effect_summary(grouped[(cell, arm)], value="BPR", ratio="PRR")}
        statistics_rows.append(summary)
        if arm in primary_arms:
            p_values[summary["test_id"]] = float(summary["raw_one_sided_wilcoxon_p"])
    adjusted = holm_adjust(p_values)
    for summary in statistics_rows:
        if summary["test_id"] in adjusted:
            correction = adjusted[summary["test_id"]]
            summary["holm_adjusted_p"] = correction["adjusted_p"]
            summary["holm_rejected"] = correction["rejected"]
            summary["robust"] = robust(summary, correction)
        else:
            summary.update({"holm_adjusted_p": None, "holm_rejected": None, "robust": None})
    historical = stage3b6_source_paths()
    eligible_by_cell = {str(row["cell_id"]): row for row in eligible}
    reproduction = []
    for row in [candidate for candidate in rows if candidate["spatial_arm"] == "all_visual"]:
        cell = str(row["cell_id"])
        key = (str(row["base_problem_id"]), cell)
        target = eligible_by_cell[cell]
        old = historical_v_row(
            historical.get(key),
            cell,
            str(target["unit_id"]),
            [int(head) for head in target["heads"]],
        )
        same_run_legacy_exact = bool(row["legacy_all_v_recipient_scores_exact"])
        item = {
            "base_problem_id": row["base_problem_id"],
            "cell_id": cell,
            "unit_id": target["unit_id"],
            "heads": target["heads"],
            "same_run_legacy_implementation_exact": same_run_legacy_exact,
            "historical_stage3b6_v_reference_available": old is not None,
            "maximum_recipient_score_absolute_difference": None,
            "BPR_absolute_difference": None,
        }
        if old is not None:
            differences = [
                abs(float(row["recipient_scores"][recipient][donor]) - float(old["recipient_scores"][recipient][donor]))
                for recipient in ("O", "C")
                for donor in ("O", "O_sham", "C", "C_sham")
            ]
            item["maximum_recipient_score_absolute_difference"] = max(differences)
            item["BPR_absolute_difference"] = abs(float(row["BPR"]) - float(old["BHR"]))
        reproduction.append(item)
    historical_differences = [
        max(float(row["maximum_recipient_score_absolute_difference"]), float(row["BPR_absolute_difference"]))
        for row in reproduction
        if row["historical_stage3b6_v_reference_available"]
    ]
    maximum_reproduction = max(historical_differences, default=0.0)
    all_same_run_legacy_exact = all(bool(row["same_run_legacy_implementation_exact"]) for row in reproduction)
    if maximum_reproduction > 1e-6 or not all_same_run_legacy_exact:
        raise RuntimeError(
            "All-V failed locked reproduction: "
            f"historical max={maximum_reproduction}, same-run legacy exact={all_same_run_legacy_exact}"
        )
    by_summary = {(row["cell_id"], row["spatial_arm"]): row for row in statistics_rows}
    classifications, phase_b_targets, margins = [], [], []
    mechanical_pass = all(bool(row["all_mechanical_controls_passed"]) for row in shards)
    for cell, config_target in eligible_by_cell.items():
        target_rows = grouped[(cell, "target_roi")]
        control_rows = grouped[(cell, "irrelevant_roi")]
        margin = {"target_id": config_target["target_id"], "cell_id": cell, **margin_summary(target_rows, control_rows)}
        margins.append(margin)
        target_summary = by_summary[(cell, "target_roi")]
        ratios = {arm: float(by_summary[(cell, arm)]["median_ratio"]) for arm in PHASE_A_ARMS}
        gate = primary_roi_gate(
            target_robust=bool(target_summary["robust"]),
            target_bidirectional_fraction=float(target_summary["bidirectional_fraction"]),
            sham_margin_ci_low=float(margin["sham_margin_bootstrap_95_CI"][0]),
            irrelevant_margin_ci_low=float(margin["irrelevant_margin_bootstrap_95_CI"][0]),
            target_greater_irrelevant_fraction=float(margin["target_greater_irrelevant_fraction"]),
            target_prr=ratios["target_roi"],
            ring_prr=ratios["target_ring"],
            mechanical_pass=mechanical_pass,
        )
        category = spatial_category(
            gate_pass=gate,
            target_robust=bool(target_summary["robust"]),
            all_visual_robust=bool(by_summary[(cell, "all_visual")]["robust"]),
            target_prr=ratios["target_roi"],
            ring_prr=ratios["target_ring"],
            complement_prr=ratios["visual_complement"],
            irrelevant_prr=ratios["irrelevant_roi"],
        )
        classification = {"target_id": config_target["target_id"], "cell_id": cell, "heads": config_target["heads"], "phase_b_gate_passed": gate, "category": category, "median_PRR": ratios, "paired_margins": margin}
        classifications.append(classification)
        if gate:
            use_target = ratios["target_roi"] >= 0.50
            phase_b_targets.append({**config_target, "phase_b_source_group": "V_target" if use_target else "V_target_ring", "phase_b_source_arm": "target_roi" if use_target else "target_ring", "phase_a_median_PRR": ratios["target_roi"] if use_target else ratios["target_ring"]})
    write_json(OUT / "analysis/roi_path_statistics.json", {"primary_unit": "base_problem_id", "base_count": expected, "eligible_target_count": len(eligible), "holm_family_size": len(p_values), "holm_family": adjusted, "arm_statistics": statistics_rows, "all_visual_stage3b6_reproduction": {"tolerance": 1e-6, "historical_exact_reference_scope": "Only exact cell/unit/head-set Stage 3B.6 V rows are compared; Target B-R Top_4 had no historical V-source decomposition row.", "historical_reference_count": sum(bool(row["historical_stage3b6_v_reference_available"]) for row in reproduction), "same_run_locked_legacy_exact_count": sum(bool(row["same_run_legacy_implementation_exact"]) for row in reproduction), "maximum_absolute_difference_where_historical_reference_exists": maximum_reproduction, "passed": True, "per_base_target": reproduction}, "all_mechanical_controls_passed": mechanical_pass, "old_ratio_secondary_only": True})
    write_json(OUT / "analysis/paired_margin_statistics.json", {"primary_unit": "base_problem_id", "target_margins": margins})
    write_json(OUT / "analysis/spatial_localization_analysis.json", {"primary_unit": "base_problem_id", "classifications": classifications, "ratios_unclipped": True, "ratios_not_unique_information_fractions": True, "selection_used_attention": False})
    write_json(OUT / "config/phase_b_targets.json", {"frozen_at": datetime.now(timezone.utc).isoformat(), "frozen_after_primary_phase_a": True, "target_count": len(phase_b_targets), "targets": phase_b_targets, "no_target_qualifies_stop_before_phase_b": len(phase_b_targets) == 0})


def validation_b(raw_root: Path, prefix: str, expected: int) -> None:
    bases, shards = load_raw(raw_root, prefix, expected)
    rows = normalize_kv(flatten(bases))
    targets = read_json(OUT / "config/phase_b_targets.json")["targets"]
    phase_a = read_jsonl(OUT / "validation/semantic_validation_results.jsonl")
    del phase_a  # Phase-A raw comparisons are loaded below.
    validation_a_rows, _ = load_raw(raw_root, "fresh_validation_phase_a", expected)
    spatial = normalize_spatial(flatten(validation_a_rows))
    a_lookup = {(row["base_problem_id"], row["cell_id"], row["spatial_arm"]): row for row in spatial}
    target_lookup = {row["cell_id"]: row for row in targets}
    comparisons = []
    for row in rows:
        if row["kv_mode"] != "KV":
            continue
        target = target_lookup[row["cell_id"]]
        old = a_lookup[(row["base_problem_id"], row["cell_id"], target["phase_b_source_arm"])]
        comparisons.extend(abs(float(row["recipient_scores"][recipient][donor]) - float(old["recipient_scores"][recipient][donor])) for recipient in ("O", "C") for donor in ("O", "O_sham", "C", "C_sham"))
    checks = {
        "all_shards_mechanical_pass": all(bool(row["all_mechanical_controls_passed"]) for row in shards),
        "all_k_only_component_isolation": all(call["kv_composition"]["unswapped_value_max_abs_delta"] == 0.0 for row in rows if row["kv_mode"] == "K" for call in row["mechanical_audit"]["calls"]),
        "all_v_only_component_isolation": all(call["kv_composition"]["unswapped_key_max_abs_delta"] == 0.0 for row in rows if row["kv_mode"] == "V" for call in row["mechanical_audit"]["calls"]),
        "all_kv_reproduce_phase_a_within_1e_6": bool(comparisons) and max(comparisons) <= 1e-6,
        "all_determinism_repeats_exact": all(shard["determinism_repeat"] is not None and bool(shard["determinism_repeat"]["exact_public_result_match"]) for shard in shards),
    }
    passed = all(checks.values())
    write_json(OUT / "validation/kv_mechanical_validation.json", {"status": "PASS" if passed else "FAIL", "checks": checks, "maximum_kv_vs_phase_a_absolute_difference": max(comparisons) if comparisons else None})
    if not passed:
        raise SystemExit("Stage 3B.7-R K/V mechanical validation failed")


def primary_b(raw_root: Path, prefix: str, expected: int) -> None:
    bases, shards = load_raw(raw_root, prefix, expected)
    targets = read_json(OUT / "config/phase_b_targets.json")["targets"]
    rows = normalize_kv(flatten(bases))
    if len(rows) != expected * len(targets) * 3:
        raise RuntimeError("Primary Phase-B row count mismatch")
    for mode, filename in KV_FILES.items():
        write_jsonl(OUT / "scoring" / filename, [row for row in rows if row["kv_mode"] == mode])
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["cell_id"], row["kv_mode"])].append(row)
    phase_a_irrelevant = {
        (row["base_problem_id"], row["cell_id"]): row
        for row in read_jsonl(OUT / "scoring/irrelevant_roi_results.jsonl")
    }
    statistics_rows, holm_families = [], {}
    for cell in sorted({row["cell_id"] for row in rows}):
        pending = []
        p_values = {}
        for mode in ("K", "V", "KV"):
            arm_rows = grouped[(cell, mode)]
            sham_margins = np.asarray([float(row["BKV"]) - abs(float(row["sham_effect"])) for row in arm_rows])
            irrelevant_margins = np.asarray([
                float(row["BKV"])
                - abs(float(phase_a_irrelevant[(row["base_problem_id"], cell)]["BPR"]))
                for row in arm_rows
            ])
            summary = {
                "test_id": f"{cell}__{mode}",
                "cell_id": cell,
                "kv_mode": mode,
                **effect_summary(arm_rows, value="BKV", ratio="KVR"),
                "sham_margin_median": float(np.median(sham_margins)),
                "sham_margin_bootstrap_95_CI": list(bootstrap_median_ci(sham_margins, iterations=10_000, seed=1235)),
                "irrelevant_margin_median": float(np.median(irrelevant_margins)),
                "irrelevant_margin_bootstrap_95_CI": list(bootstrap_median_ci(irrelevant_margins, iterations=10_000, seed=1236)),
                "irrelevant_control_source": "matching frozen Phase-A irrelevant-ROI K+V path effect",
            }
            pending.append(summary)
            p_values[summary["test_id"]] = float(summary["raw_one_sided_wilcoxon_p"])
        adjusted = holm_adjust(p_values)
        holm_families[cell] = adjusted
        for summary in pending:
            correction = adjusted[summary["test_id"]]
            control_margins_robust = bool(
                float(summary["sham_margin_median"]) > 0.0
                and float(summary["sham_margin_bootstrap_95_CI"][0]) > 0.0
                and float(summary["irrelevant_margin_median"]) > 0.0
                and float(summary["irrelevant_margin_bootstrap_95_CI"][0]) > 0.0
            )
            summary.update({"holm_adjusted_p": correction["adjusted_p"], "holm_rejected": correction["rejected"], "paired_control_margins_robust": control_margins_robust, "robust": bool(robust(summary, correction) and control_margins_robust)})
            statistics_rows.append(summary)
    by_summary = {(row["cell_id"], row["kv_mode"]): row for row in statistics_rows}
    row_lookup = {(row["base_problem_id"], row["cell_id"], row["kv_mode"]): row for row in rows}
    phase_a_lookup = {(row["base_problem_id"], row["cell_id"], row["spatial_arm"]): row for filename in ("target_roi_results.jsonl", "ring_results.jsonl") for row in read_jsonl(OUT / "scoring" / filename)}
    target_lookup = {row["cell_id"]: row for row in targets}
    interactions, mechanisms, reproduction = [], [], []
    for cell, target in target_lookup.items():
        base_ids = sorted({row["base_problem_id"] for row in grouped[(cell, "KV")]})
        interaction_values = [float(row_lookup[(base, cell, "KV")]["BKV"]) - float(row_lookup[(base, cell, "K")]["BKV"]) - float(row_lookup[(base, cell, "V")]["BKV"]) for base in base_ids]
        joint_best = [float(row_lookup[(base, cell, "KV")]["BKV"]) - max(float(row_lookup[(base, cell, "K")]["BKV"]), float(row_lookup[(base, cell, "V")]["BKV"])) for base in base_ids]
        interaction = {"cell_id": cell, "interaction_KV_minus_K_minus_V": bootstrap_summary(interaction_values), "joint_minus_best_single": bootstrap_summary(joint_best), "bootstrap_95_CI": bootstrap_summary(joint_best)["bootstrap_95_CI"]}
        interactions.append(interaction)
        k, v, kv = (by_summary[(cell, mode)] for mode in ("K", "V", "KV"))
        mechanisms.append({"target_id": target["target_id"], "cell_id": cell, "classification": classify_kv_mechanism(k={"robust": k["robust"], "median_KVR": k["median_ratio"]}, v={"robust": v["robust"], "median_KVR": v["median_ratio"]}, interaction=interaction), "median_KVR": {"K": k["median_ratio"], "V": v["median_ratio"], "KV": kv["median_ratio"]}})
        for base in base_ids:
            new = row_lookup[(base, cell, "KV")]
            old = phase_a_lookup[(base, cell, target["phase_b_source_arm"])]
            differences = [abs(float(new["recipient_scores"][recipient][donor]) - float(old["recipient_scores"][recipient][donor])) for recipient in ("O", "C") for donor in ("O", "O_sham", "C", "C_sham")]
            reproduction.append({"base_problem_id": base, "cell_id": cell, "maximum_recipient_score_absolute_difference": max(differences)})
    maximum_reproduction = max(row["maximum_recipient_score_absolute_difference"] for row in reproduction)
    if maximum_reproduction > 1e-6:
        raise RuntimeError(f"K+V failed primary Phase-A reproduction: {maximum_reproduction}")
    write_json(OUT / "analysis/kv_decomposition_statistics.json", {"primary_unit": "base_problem_id", "base_count": expected, "conditional_target_count": len(targets), "holm_families": holm_families, "arm_statistics": statistics_rows, "mechanism_classifications": mechanisms, "kv_reproduces_phase_a": {"tolerance": 1e-6, "maximum_absolute_difference": maximum_reproduction, "passed": True, "per_base_target": reproduction}, "all_mechanical_controls_passed": all(bool(row["all_mechanical_controls_passed"]) for row in shards), "ratios_unclipped": True, "ratios_not_additive_information_fractions": True})
    write_json(OUT / "analysis/kv_interaction_analysis.json", {"primary_unit": "base_problem_id", "interactions": interactions, "descriptive_only": True})


def main() -> None:
    args = parse_args()
    ensure_directory(OUT / "analysis")
    if args.stage == "validation_a":
        validation_a(args.raw_root, args.prefix, args.expected_bases)
    elif args.stage == "primary_a":
        primary_a(args.raw_root, args.prefix, args.expected_bases)
    elif args.stage == "validation_b":
        validation_b(args.raw_root, args.prefix, args.expected_bases)
    else:
        primary_b(args.raw_root, args.prefix, args.expected_bases)


if __name__ == "__main__":
    main()
