#!/usr/bin/env python3
"""Aggregate Stage 3B.7 validation, spatial, and conditional K/V phases."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3b4.metrics import bootstrap_summary, one_sided_wilcoxon_greater
from visual_reasoning.stage3b4.protocol import holm_adjust
from visual_reasoning.stage3b7.protocol import classify_kv_mechanism, phase_a_gate_passes


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7"
SPATIAL_FILES = {
    "all_visual": "all_visual_path_results.jsonl",
    "target_roi": "target_roi_results.jsonl",
    "visual_complement": "visual_complement_results.jsonl",
    "irrelevant_roi": "irrelevant_roi_results.jsonl",
    "target_ring": "target_ring_results.jsonl",
}
KV_FILES = {"K": "k_only_results.jsonl", "V": "v_only_results.jsonl", "KV": "kv_results.jsonl"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("validation_a", "primary_a", "validation_b", "primary_b"),
        required=True,
    )
    parser.add_argument("--raw-root", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_raw(root: Path, prefix: str, expected: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    directories = sorted(root.glob(f"{prefix}_*"))
    if len(directories) != 2:
        raise RuntimeError(f"Expected two {prefix} shards, observed {len(directories)}")
    summaries = [read_json(path / "result.json") for path in directories]
    rows = [row for path in directories for row in read_jsonl(path / "results.jsonl")]
    if len(rows) != expected or len({str(row["base_problem_id"]) for row in rows}) != expected:
        raise RuntimeError(f"Expected {expected} unique bases for {prefix}, observed {len(rows)}")
    return rows, summaries


def flatten(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "base_problem_id": str(base["base_problem_id"]),
            "example_id": str(base["example_id"]),
            "evidence_type": base["evidence_type"],
            **arm,
        }
        for base in rows
        for target in base["targets"]
        for arm in target["arm_results"]
    ]


def median(values: list[float]) -> float:
    return float(statistics.median(values))


def summarize(rows: list[dict[str, Any]], ratio_key: str) -> dict[str, Any]:
    effects = [float(row["BHR"]) for row in rows]
    ratios = [float(row[ratio_key]) for row in rows if row.get(ratio_key) is not None]
    shams = [
        float(row["sham_to_semantic_ratio"])
        for row in rows
        if row.get("sham_to_semantic_ratio") is not None
        and math.isfinite(float(row["sham_to_semantic_ratio"]))
    ]
    bootstrap = bootstrap_summary(effects)
    return {
        "base_count": len(rows),
        "mean_effect": bootstrap["mean"],
        "median_effect": bootstrap["median"],
        "bootstrap_95_CI": bootstrap["bootstrap_95_CI"],
        "bootstrap_resamples": bootstrap["bootstrap_resamples"],
        "raw_p": one_sided_wilcoxon_greater(effects),
        f"median_{ratio_key}": median(ratios) if ratios else None,
        "bidirectional_count": sum(
            bool(row["bidirectionally_source_consistent"]) for row in rows
        ),
        "bidirectional_fraction": sum(
            bool(row["bidirectionally_source_consistent"]) for row in rows
        ) / len(rows),
        "median_sham_to_semantic_ratio": median(shams) if shams else None,
        "all_self_exact": all(bool(row["all_self_restorations_exact"]) for row in rows),
        "all_scores_finite": all(bool(row["all_scores_finite"]) for row in rows),
        "all_mechanical_controls_pass": all(
            bool(row["mechanical_audit"]["all_query_head_selectivity_valid"])
            and bool(row["mechanical_audit"]["all_source_group_isolation_valid"])
            for row in rows
        ),
    }


def robust(summary: dict[str, Any], adjustment: dict[str, Any]) -> bool:
    sham = summary["median_sham_to_semantic_ratio"]
    return bool(
        adjustment["rejected"]
        and float(summary["bootstrap_95_CI"][0]) > 0.0
        and float(summary["bidirectional_fraction"]) >= 0.70
        and sham is not None
        and float(sham) < 0.25
        and bool(summary["all_self_exact"])
        and bool(summary["all_scores_finite"])
        and bool(summary["all_mechanical_controls_pass"])
    )


def stage3b6_source_paths() -> dict[tuple[str, str], Path]:
    found: dict[tuple[str, str], Path] = {}
    for path in sorted((ROOT / "outputs/stage3b6/scoring/raw").glob("source_*/examples/*/result.json")):
        base = path.parent.name
        row = read_json(path)
        for cell in row["cells"]:
            for unit in cell["unit_results"]:
                if unit["source_group"] == "V":
                    found[(base, cell["cell_id"])] = path
    return found


def historical_v_row(path: Path, cell_id: str) -> dict[str, Any]:
    row = read_json(path)
    return next(
        unit
        for cell in row["cells"]
        for unit in cell["unit_results"]
        if cell["cell_id"] == cell_id and unit["source_group"] == "V"
    )


def normalize_spatial(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {
        (row["base_problem_id"], row["cell_id"], row["spatial_arm"]): row
        for row in rows
    }
    normalized = []
    for row in rows:
        all_visual = lookup[(row["base_problem_id"], row["cell_id"], "all_visual")]
        denominator = float(all_visual["BHR"])
        normalized.append({
            **row,
            "BPR_O": float(row["BHR_O"]),
            "BPR_C": float(row["BHR_C"]),
            "BPR": float(row["BHR"]),
            "PRR": None if denominator == 0.0 else float(row["BHR"]) / denominator,
            "all_visual_BPR": denominator,
        })
    return normalized


def validation_a(raw_root: Path) -> None:
    bases, shards = load_raw(raw_root, "validation_phase_a", 8)
    rows = normalize_spatial(flatten(bases))
    all_v = [row for row in rows if row["spatial_arm"] == "all_visual"]
    all_v_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in all_v:
        all_v_by_target[row["cell_id"]].append(row)
    target_semantics = {
        cell: {
            "median_BPR": median([float(row["BPR"]) for row in cell_rows]),
            "bidirectional_fraction": sum(
                bool(row["bidirectionally_source_consistent"]) for row in cell_rows
            ) / len(cell_rows),
            "median_sham_to_semantic_ratio": median([
                float(row["sham_to_semantic_ratio"])
                for row in cell_rows
                if row["sham_to_semantic_ratio"] is not None
            ]),
        }
        for cell, cell_rows in all_v_by_target.items()
    }
    checks = {
        "all_shards_mechanical_pass": all(
            bool(row["all_mechanical_controls_passed"]) for row in shards
        ),
        "all_legacy_all_v_exact": all(
            bool(row.get("legacy_all_v_recipient_scores_exact")) for row in all_v
        ),
        "all_roi_layout_and_isolation_exact": all(
            bool(base["mechanical_controls"]["all_roi_mappings_exact"])
            and bool(base["condition_layout_exact"])
            for base in bases
        ),
        "all_self_exact": all(bool(row["all_self_restorations_exact"]) for row in rows),
        "all_scores_finite": all(bool(row["all_scores_finite"]) for row in rows),
        "all_determinism_repeats_exact": all(
            shard["determinism_repeat"] is not None
            and bool(shard["determinism_repeat"]["exact_public_result_match"])
            for shard in shards
        ),
        "all_v_semantic_direction_valid": all(
            float(summary["median_BPR"]) > 0.0
            and float(summary["bidirectional_fraction"]) >= 0.50
            for summary in target_semantics.values()
        ),
        "all_v_sham_small": all(
            float(summary["median_sham_to_semantic_ratio"]) < 0.25
            for summary in target_semantics.values()
        ),
    }
    passed = all(checks.values())
    payload = {
        "status": "PASS" if passed else "FAIL",
        "gate_passed": passed,
        "base_count": 8,
        "target_count": 2,
        "selection_used_attention": False,
        "checks": checks,
        "all_v_semantic_summary": target_semantics,
        "note": "Scientific ROI localization was not selected or inferred from the validation cohort.",
    }
    write_json(OUT / "validation/roi_path_validation.json", payload)
    write_jsonl(OUT / "validation/validation_phase_a_results.jsonl", rows)
    report = [
        "# Stage 3B.7 Validation Report",
        "",
        f"Phase A validation: **{payload['status']}** on 8 disjoint bases.",
        "",
        "The gate checks exact legacy all-V equivalence, ROI/source isolation, self transparency, finite scores, deterministic replication, and controlled all-V semantic direction. ROI outcome patterns were not used for primary selection.",
        "",
    ]
    for key, value in checks.items():
        report.append(f"- {key}: `{value}`")
    (OUT / "validation/validation_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    if not passed:
        raise SystemExit("Stage 3B.7 validation Phase A gate failed")


def primary_a(raw_root: Path) -> None:
    bases, shards = load_raw(raw_root, "primary_phase_a", 37)
    if not all(bool(row["all_mechanical_controls_passed"]) for row in shards):
        raise RuntimeError("Primary Phase-A mechanical controls failed")
    rows = normalize_spatial(flatten(bases))
    if len(rows) != 37 * 2 * 5:
        raise RuntimeError(f"Expected 370 spatial rows, observed {len(rows)}")
    ensure_directory(OUT / "scoring")
    for arm, filename in SPATIAL_FILES.items():
        write_jsonl(OUT / "scoring" / filename, [row for row in rows if row["spatial_arm"] == arm])

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["cell_id"], row["spatial_arm"])].append(row)
    summaries = []
    primary_p = {}
    primary_arms = set(read_json(OUT / "config/stage3b7_config.json")["phase_a"]["primary_arms"])
    for (cell, arm), arm_rows in sorted(grouped.items()):
        if len(arm_rows) != 37:
            raise RuntimeError(f"{cell}/{arm} has {len(arm_rows)} bases")
        summary = {
            "test_id": f"{cell}__{arm}",
            "cell_id": cell,
            "unit_id": arm_rows[0]["unit_id"],
            "heads": arm_rows[0]["heads"],
            "spatial_arm": arm,
            "primary_family": arm in primary_arms,
            **summarize(arm_rows, "PRR"),
        }
        summaries.append(summary)
        if arm in primary_arms:
            primary_p[summary["test_id"]] = float(summary["raw_p"])
    adjusted = holm_adjust(primary_p)
    for summary in summaries:
        if summary["primary_family"]:
            correction = adjusted[summary["test_id"]]
            summary["holm_adjusted_p"] = float(correction["adjusted_p"])
            summary["holm_rejected"] = bool(correction["rejected"])
            summary["robust"] = robust(summary, correction)
        else:
            summary["holm_adjusted_p"] = None
            summary["holm_rejected"] = None
            summary["robust"] = None

    historical = stage3b6_source_paths()
    reproduction_rows = []
    for row in [candidate for candidate in rows if candidate["spatial_arm"] == "all_visual"]:
        old = historical_v_row(historical[(row["base_problem_id"], row["cell_id"])], row["cell_id"])
        differences = [
            abs(float(row["recipient_scores"][recipient][donor]) - float(old["recipient_scores"][recipient][donor]))
            for recipient in ("O", "C")
            for donor in ("O", "O_sham", "C", "C_sham")
        ]
        reproduction_rows.append({
            "base_problem_id": row["base_problem_id"],
            "cell_id": row["cell_id"],
            "maximum_recipient_score_absolute_difference": max(differences),
            "BPR_absolute_difference": abs(float(row["BPR"]) - float(old["BHR"])),
        })
    max_reproduction = max(
        max(row["maximum_recipient_score_absolute_difference"], row["BPR_absolute_difference"])
        for row in reproduction_rows
    )
    if max_reproduction > 1e-6:
        raise RuntimeError(f"All-V failed Stage 3B.6 reproduction: {max_reproduction}")

    by_cell = defaultdict(dict)
    for summary in summaries:
        by_cell[summary["cell_id"]][summary["spatial_arm"]] = summary
    row_lookup = {
        (row["base_problem_id"], row["cell_id"], row["spatial_arm"]): row
        for row in rows
    }
    classifications = []
    phase_b_targets = []
    contrasts = []
    for cell, arms in sorted(by_cell.items()):
        target_rows = grouped[(cell, "target_roi")]
        differences = [
            float(row["BPR"])
            - float(row_lookup[(row["base_problem_id"], cell, "irrelevant_roi")]["BPR"])
            for row in target_rows
        ]
        contrast_bootstrap = bootstrap_summary(differences)
        contrast = {
            "cell_id": cell,
            "mean_target_minus_irrelevant": contrast_bootstrap["mean"],
            "median_target_minus_irrelevant": contrast_bootstrap["median"],
            "bootstrap_95_CI": contrast_bootstrap["bootstrap_95_CI"],
            "target_greater_fraction": sum(value > 0 for value in differences) / len(differences),
        }
        contrasts.append(contrast)
        gate = phase_a_gate_passes(
            target_summary={
                "robust": arms["target_roi"]["robust"],
                "median_PRR": arms["target_roi"]["median_PRR"],
            },
            ring_summary={"median_PRR": arms["target_ring"]["median_PRR"]},
            target_minus_irrelevant=contrast,
        )
        target_prr = float(arms["target_roi"]["median_PRR"])
        ring_prr = float(arms["target_ring"]["median_PRR"])
        complement_prr = float(arms["visual_complement"]["median_PRR"])
        irrelevant_prr = float(arms["irrelevant_roi"]["median_PRR"])
        if not gate:
            category = "ROI-Inconclusive"
        elif (
            bool(arms["target_roi"]["robust"])
            and target_prr >= 0.75
            and complement_prr < 0.50
            and irrelevant_prr < 0.25
        ):
            category = "ROI-Local"
        elif (
            bool(arms["target_roi"]["robust"])
            and target_prr >= 0.25
            and ring_prr >= 0.75
            and ring_prr - target_prr >= 0.20
        ):
            category = "ROI-Local-Plus-Context"
        elif bool(arms["all_visual"]["robust"]) and (
            complement_prr >= 0.50 or max(target_prr, ring_prr) < 0.50
        ):
            category = "Visual-Distributed"
        else:
            category = "ROI-Inconclusive"
        classification = {
            "cell_id": cell,
            "unit_id": arms["target_roi"]["unit_id"],
            "heads": arms["target_roi"]["heads"],
            "category": category,
            "phase_b_gate_passed": gate,
            "median_PRR": {name: value["median_PRR"] for name, value in arms.items()},
            "target_minus_irrelevant": contrast,
        }
        classifications.append(classification)
        if gate:
            source_group = "V_target" if target_prr >= 0.50 else "V_target_ring"
            source_arm = "target_roi" if source_group == "V_target" else "target_ring"
            target_config = next(
                row
                for row in read_json(OUT / "config/stage3b7_config.json")["primary_targets"]
                if row["cell_id"] == cell
            )
            phase_b_targets.append({
                **target_config,
                "source_group": source_group,
                "source_arm": source_arm,
                "source_region_selection_rule": "pre-score protocol amendment",
                "phase_a_median_PRR": target_prr if source_group == "V_target" else ring_prr,
            })

    write_json(OUT / "analysis/roi_path_statistics.json", {
        "primary_unit": "base_problem_id",
        "base_count": 37,
        "frozen_primary_family_size": 8,
        "holm_family": adjusted,
        "arm_statistics": summaries,
        "all_visual_stage3b6_reproduction": {
            "tolerance": 1e-6,
            "maximum_absolute_difference": max_reproduction,
            "passed": max_reproduction <= 1e-6,
            "per_base_target": reproduction_rows,
        },
        "all_mechanical_controls_passed": all(
            bool(shard["all_mechanical_controls_passed"]) for shard in shards
        ),
    })
    write_json(OUT / "analysis/spatial_localization_analysis.json", {
        "primary_unit": "base_problem_id",
        "classifications": classifications,
        "target_minus_irrelevant_contrasts": contrasts,
        "ratios_are_unclipped": True,
        "ratios_are_not_unique_information_fractions": True,
        "selection_used_attention": False,
    })
    write_json(OUT / "config/phase_b_targets.json", {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "frozen_after_primary_phase_a": True,
        "gate_passed": bool(phase_b_targets),
        "target_count": len(phase_b_targets),
        "targets": phase_b_targets,
        "selection_used_attention": False,
    })


def normalize_kv(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {
        (row["base_problem_id"], row["cell_id"], row["kv_mode"]): row
        for row in rows
    }
    normalized = []
    for row in rows:
        kv = lookup[(row["base_problem_id"], row["cell_id"], "KV")]
        denominator = float(kv["BHR"])
        normalized.append({
            **row,
            "BKV_O": float(row["BHR_O"]),
            "BKV_C": float(row["BHR_C"]),
            "BKV": float(row["BHR"]),
            "KVR": None if denominator == 0.0 else float(row["BHR"]) / denominator,
            "joint_KV_BKV": denominator,
        })
    return normalized


def validation_b(raw_root: Path) -> None:
    bases, shards = load_raw(raw_root, "validation_phase_b", 8)
    rows = normalize_kv(flatten(bases))
    phase_a = read_jsonl(OUT / "validation/validation_phase_a_results.jsonl")
    a_lookup = {
        (row["base_problem_id"], row["cell_id"], row["spatial_arm"]): row
        for row in phase_a
    }
    targets = read_json(OUT / "config/phase_b_targets.json")["targets"]
    target_lookup = {row["cell_id"]: row for row in targets}
    comparisons = []
    for row in rows:
        if row["kv_mode"] != "KV":
            continue
        target = target_lookup[row["cell_id"]]
        phase_a_row = a_lookup[(row["base_problem_id"], row["cell_id"], target["source_arm"])]
        differences = [
            abs(float(row["recipient_scores"][recipient][donor]) - float(phase_a_row["recipient_scores"][recipient][donor]))
            for recipient in ("O", "C")
            for donor in ("O", "O_sham", "C", "C_sham")
        ]
        comparisons.append(max(differences))
    checks = {
        "all_shards_mechanical_pass": all(
            bool(row["all_mechanical_controls_passed"]) for row in shards
        ),
        "all_k_only_component_isolation": all(
            call["kv_composition"]["unswapped_value_max_abs_delta"] == 0.0
            for row in rows if row["kv_mode"] == "K"
            for call in row["mechanical_audit"]["calls"]
        ),
        "all_v_only_component_isolation": all(
            call["kv_composition"]["unswapped_key_max_abs_delta"] == 0.0
            for row in rows if row["kv_mode"] == "V"
            for call in row["mechanical_audit"]["calls"]
        ),
        "all_kv_reproduce_phase_a_within_tolerance": bool(comparisons) and max(comparisons) <= 1e-6,
        "all_self_exact": all(bool(row["all_self_restorations_exact"]) for row in rows),
        "all_scores_finite": all(bool(row["all_scores_finite"]) for row in rows),
        "all_determinism_repeats_exact": all(
            shard["determinism_repeat"] is not None
            and bool(shard["determinism_repeat"]["exact_public_result_match"])
            for shard in shards
        ),
    }
    passed = all(checks.values())
    write_json(OUT / "validation/kv_decomposition_validation.json", {
        "status": "PASS" if passed else "FAIL",
        "gate_passed": passed,
        "base_count": 8,
        "target_count": len(targets),
        "checks": checks,
        "maximum_kv_vs_phase_a_recipient_score_absolute_difference": max(comparisons) if comparisons else None,
    })
    write_jsonl(OUT / "validation/validation_phase_b_results.jsonl", rows)
    with (OUT / "validation/validation_report.md").open("a", encoding="utf-8") as stream:
        stream.write(f"\nPhase B validation: **{'PASS' if passed else 'FAIL'}**.\n\n")
        for key, value in checks.items():
            stream.write(f"- {key}: `{value}`\n")
    if not passed:
        raise SystemExit("Stage 3B.7 validation Phase B gate failed")


def primary_b(raw_root: Path) -> None:
    bases, shards = load_raw(raw_root, "primary_phase_b", 37)
    if not all(bool(row["all_mechanical_controls_passed"]) for row in shards):
        raise RuntimeError("Primary Phase-B mechanical controls failed")
    rows = normalize_kv(flatten(bases))
    target_count = read_json(OUT / "config/phase_b_targets.json")["target_count"]
    if len(rows) != 37 * target_count * 3:
        raise RuntimeError("Phase-B row count mismatch")
    for mode, filename in KV_FILES.items():
        write_jsonl(OUT / "scoring" / filename, [row for row in rows if row["kv_mode"] == mode])
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["cell_id"], row["kv_mode"])].append(row)
    statistics_rows = []
    by_cell_p: dict[str, dict[str, float]] = defaultdict(dict)
    for (cell, mode), arm_rows in sorted(grouped.items()):
        summary = {
            "test_id": f"{cell}__{mode}",
            "cell_id": cell,
            "unit_id": arm_rows[0]["unit_id"],
            "heads": arm_rows[0]["heads"],
            "kv_mode": mode,
            "source_group": arm_rows[0]["source_group"],
            **summarize(arm_rows, "KVR"),
        }
        statistics_rows.append(summary)
        by_cell_p[cell][summary["test_id"]] = float(summary["raw_p"])
    holm = {cell: holm_adjust(values) for cell, values in by_cell_p.items()}
    for summary in statistics_rows:
        correction = holm[summary["cell_id"]][summary["test_id"]]
        summary["holm_adjusted_p"] = float(correction["adjusted_p"])
        summary["holm_rejected"] = bool(correction["rejected"])
        summary["robust"] = robust(summary, correction)

    by_cell = defaultdict(dict)
    for summary in statistics_rows:
        by_cell[summary["cell_id"]][summary["kv_mode"]] = summary
    row_lookup = {
        (row["base_problem_id"], row["cell_id"], row["kv_mode"]): row
        for row in rows
    }
    mechanisms = []
    interactions = []
    for cell, arms in sorted(by_cell.items()):
        base_ids = sorted({row["base_problem_id"] for row in grouped[(cell, "KV")]})
        values = [
            float(row_lookup[(base, cell, "KV")]["BKV"])
            - float(row_lookup[(base, cell, "K")]["BKV"])
            - float(row_lookup[(base, cell, "V")]["BKV"])
            for base in base_ids
        ]
        joint_over_best = [
            float(row_lookup[(base, cell, "KV")]["BKV"])
            - max(
                float(row_lookup[(base, cell, "K")]["BKV"]),
                float(row_lookup[(base, cell, "V")]["BKV"]),
            )
            for base in base_ids
        ]
        interaction_summary = {
            "cell_id": cell,
            "interaction_KV_minus_K_minus_V": bootstrap_summary(values),
            "joint_minus_best_single": bootstrap_summary(joint_over_best),
            "bootstrap_95_CI": bootstrap_summary(joint_over_best)["bootstrap_95_CI"],
        }
        interactions.append(interaction_summary)
        mechanisms.append({
            "cell_id": cell,
            "unit_id": arms["KV"]["unit_id"],
            "heads": arms["KV"]["heads"],
            "classification": classify_kv_mechanism(
                k={"robust": arms["K"]["robust"], "median_KVR": arms["K"]["median_KVR"]},
                v={"robust": arms["V"]["robust"], "median_KVR": arms["V"]["median_KVR"]},
                interaction=interaction_summary,
            ),
            "median_KVR": {mode: arm["median_KVR"] for mode, arm in arms.items()},
        })

    phase_a_rows = {
        filename: read_jsonl(OUT / "scoring" / filename)
        for filename in ("target_roi_results.jsonl", "target_ring_results.jsonl")
    }
    targets = {row["cell_id"]: row for row in read_json(OUT / "config/phase_b_targets.json")["targets"]}
    phase_a_lookup = {
        (row["base_problem_id"], row["cell_id"], row["spatial_arm"]): row
        for file_rows in phase_a_rows.values()
        for row in file_rows
    }
    reproduction = []
    for row in [candidate for candidate in rows if candidate["kv_mode"] == "KV"]:
        target = targets[row["cell_id"]]
        old = phase_a_lookup[(row["base_problem_id"], row["cell_id"], target["source_arm"])]
        differences = [
            abs(float(row["recipient_scores"][recipient][donor]) - float(old["recipient_scores"][recipient][donor]))
            for recipient in ("O", "C")
            for donor in ("O", "O_sham", "C", "C_sham")
        ]
        reproduction.append({
            "base_problem_id": row["base_problem_id"],
            "cell_id": row["cell_id"],
            "maximum_recipient_score_absolute_difference": max(differences),
        })
    max_reproduction = max(row["maximum_recipient_score_absolute_difference"] for row in reproduction)
    if max_reproduction > 1e-6:
        raise RuntimeError(f"K+V failed Phase-A reproduction: {max_reproduction}")
    write_json(OUT / "analysis/kv_decomposition_statistics.json", {
        "primary_unit": "base_problem_id",
        "base_count": 37,
        "conditional_target_count": target_count,
        "holm_families": holm,
        "arm_statistics": statistics_rows,
        "mechanism_classifications": mechanisms,
        "kv_reproduces_phase_a": {
            "tolerance": 1e-6,
            "maximum_absolute_difference": max_reproduction,
            "passed": True,
            "per_base_target": reproduction,
        },
        "all_mechanical_controls_passed": all(
            bool(shard["all_mechanical_controls_passed"]) for shard in shards
        ),
        "ratios_are_unclipped": True,
        "ratios_are_not_additive_information_fractions": True,
    })
    write_json(OUT / "analysis/kv_interaction_analysis.json", {
        "primary_unit": "base_problem_id",
        "interactions": interactions,
        "descriptive_only": True,
    })


def main() -> None:
    args = parse_args()
    if args.stage == "validation_a":
        validation_a(args.raw_root)
    elif args.stage == "primary_a":
        primary_a(args.raw_root)
    elif args.stage == "validation_b":
        validation_b(args.raw_root)
    else:
        primary_b(args.raw_root)


if __name__ == "__main__":
    main()
