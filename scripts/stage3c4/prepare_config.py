#!/usr/bin/env python3
"""Freeze Stage 3C.4 cohorts, scopes, controls, and confirmatory family."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage3c4.protocol import frozen_layer_scopes, temporal_query_indices


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c4"
SOURCE = ROOT / "outputs/stage3c3r"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    created = datetime.now(timezone.utc).isoformat()
    source_config_path = SOURCE / "config/stage3c3r_config.json"
    source_config = read_json(source_config_path)
    validation_source = SOURCE / "cohort/validation_manifest.jsonl"
    primary_source = SOURCE / "cohort/primary_manifest.jsonl"
    validation = read_jsonl(validation_source)
    primary = read_jsonl(primary_source)
    validation_ids = [str(row["base_problem_id"]) for row in validation]
    primary_ids = [str(row["base_problem_id"]) for row in primary]
    if len(validation_ids) != 7 or len(primary_ids) != 24 or set(validation_ids) & set(primary_ids):
        raise RuntimeError("Stage 3C.4 requires the exact disjoint Stage 3C.3-R 7/24 split")
    targets = source_config["targets"]
    expected_targets = {
        "target_a": {
            "coordinate": "E_d", "layer_index": 29,
            "causal_heads": [11, 6, 15, 12], "noncausal_heads": [0, 1, 2, 3],
        },
        "target_b": {
            "coordinate": "E_d-1", "layer_index": 28,
            "causal_heads": [16, 0, 3, 6], "noncausal_heads": [1, 2, 4, 5],
        },
    }
    if targets != expected_targets:
        raise RuntimeError("Frozen Stage 3C.3-R target definitions changed")

    validation_rows = [
        {**row, "stage3c4_cohort_role": "validation", "reused_without_reselection": True}
        for row in validation
    ]
    primary_rows = [
        {**row, "stage3c4_cohort_role": "primary", "reused_without_reselection": True}
        for row in primary
    ]
    write_jsonl(OUT / "cohort/validation_manifest.jsonl", validation_rows)
    write_jsonl(OUT / "cohort/primary_manifest.jsonl", primary_rows)
    write_jsonl(OUT / "cohort/exclusions.jsonl", [])

    scopes = frozen_layer_scopes(language_layers=36)
    layer_scope_config = {
        "frozen_at": created,
        "frozen_before_outcome_scoring": True,
        "logical_query_heads": list(range(32)),
        "scopes": scopes,
        "descriptions": {
            "L0": "W4, layers 28-29",
            "L1": "W4+W5, layers 28-33",
            "L2": "late layers 24-35",
            "L3": "mid+late layers 16-35",
            "L4": "all language layers 0-35",
        },
        "nested": all(set(scopes[left]) <= set(scopes[right]) for left, right in zip(scopes, list(scopes)[1:])),
    }
    write_json(OUT / "config/layer_scopes.json", layer_scope_config)

    windows = {"T0": 0, "T1": 1, "T2": 2, "T4": 4, "T8": 8, "T16": 16}
    write_json(OUT / "config/temporal_windows.json", {
        "frozen_at": created,
        "frozen_before_outcome_scoring": True,
        "window_definition": "inclusive [t*-backward, t*] in positive generated-token coordinates",
        "backward_offsets": windows,
        "missing_history_rule": "mark unavailable; do not substitute normalized positions",
    })
    interactions = {
        "C1": {"layers": list(range(24, 36)), "backward": 4},
        "C2": {"layers": list(range(24, 36)), "backward": 8},
        "C3": {"layers": list(range(36)), "backward": 4},
        "C4": {"layers": list(range(36)), "backward": 8},
    }
    write_json(OUT / "config/interaction_cells.json", {
        "frozen_at": created,
        "frozen_before_phase_ab_scoring": True,
        "cells": interactions,
        "posthoc_cells_allowed": False,
    })

    availability = []
    for cohort_role, rows in (("validation", validation_rows), ("primary", primary_rows)):
        for row in rows:
            by_target = {item["target_id"]: item for item in row["state_pairs"]}
            for target_id in ("target_a", "target_b"):
                current = int(by_target[target_id]["state_R"]["generated_index"])
                available = {}
                for label, backward in windows.items():
                    try:
                        available[label] = {
                            "available": True,
                            "query_generated_indices": temporal_query_indices(
                                current_generated_index=current, backward=backward
                            ),
                        }
                    except ValueError:
                        available[label] = {"available": False, "query_generated_indices": []}
                availability.append({
                    "base_problem_id": str(row["base_problem_id"]),
                    "cohort_role": cohort_role,
                    "target_id": target_id,
                    "current_generated_index": current,
                    "windows": available,
                })
    write_jsonl(OUT / "cohort/temporal_availability.jsonl", availability)

    family = [
        "L1_vs_L0", "L2_vs_L0", "L3_vs_L0", "L4_vs_L0", "monotonic_layer_scope_trend",
        "T1_vs_T0", "T2_vs_T0", "T4_vs_T0", "T8_vs_T0", "T16_vs_T0",
        "monotonic_temporal_window_trend", "T_vs_M_suppression", "T_vs_I_suppression",
        "frozen_layer_by_time_interaction",
    ]
    write_json(OUT / "config/primary_family.json", {
        "frozen_at": created,
        "frozen_before_outcome_scoring": True,
        "primary_unit": "base_problem_id",
        "tests": family,
        "test_count": 14,
        "multiplicity": "Holm correction across the 14 frozen base-aggregated one-sided tests",
        "target_aggregation": "arithmetic mean of Target A and Target B within each base",
        "primary_readout": "unnormalized evidence loss D_native - D_suppressed",
        "retention": "descriptive D_suppressed/D_native, unclipped",
        "control_aggregation": "mean target-vs-control loss contrast across both targets and current/last-4 scopes",
        "interaction_test": "mean over last-4/last-8 of all-layer loss minus matched layers24-35 loss",
        "trend_test": "negative per-base least-squares slope of D across ordinal scope/window index",
        "substantial_retention_threshold": 0.80,
        "bootstrap_seed": 20260904,
        "bootstrap_resamples": 10000,
    })

    frozen_targets = {
        "frozen_at": created,
        "source": "outputs/stage3c3r/config/frozen_targets.json",
        "source_sha256": sha256(SOURCE / "config/frozen_targets.json"),
        "targets": targets,
        "target_roi": "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl:absolute_source_groups.V_target",
        "mention_roi": "outputs/stage3c2/annotations/mention_roi_annotations.jsonl:mention_absolute_source_positions",
        "irrelevant_roi": "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl:absolute_source_groups.V_irrelevant",
        "selection_used_attention": False,
    }
    write_json(OUT / "config/frozen_targets.json", frozen_targets)

    config = {
        "created_at": created,
        "source_plan": "plan/stage3c4_plan.md",
        "source_plan_sha256": sha256(ROOT / "plan/stage3c4_plan.md"),
        "source_stage3c3r_config": "outputs/stage3c3r/config/stage3c3r_config.json",
        "source_stage3c3r_config_sha256": sha256(source_config_path),
        "model": source_config["model"],
        "model_checkpoint": source_config["model_checkpoint"],
        "dataset_root": source_config["dataset_root"],
        "seed": int(source_config["seed"]),
        "condition": "O",
        "targets": targets,
        "architecture_expected": source_config["architecture_expected"],
        "validation_base_problem_ids": validation_ids,
        "primary_base_problem_ids": primary_ids,
        "validation_base_count": len(validation_ids),
        "primary_base_count": len(primary_ids),
        "intervention": {
            "object": "target-ROI contribution c_T=sum_j alpha_j V_j before W_O",
            "gain": 0.0,
            "partition_compute_dtype": "float32",
            "all_heads": list(range(32)),
            "teacher_forced_tokens_frozen": True,
            "downstream_recomputation_allowed": True,
        },
        "phase_a_scopes": list(scopes),
        "phase_b_windows": list(windows),
        "phase_c_cells": list(interactions),
        "control_sources": ["M", "I"],
        "control_windows": ["T0", "T4"],
        "optional_nonvisual_state_readout": False,
        "gpu": source_config["gpu"],
        "selection_used_attention": False,
        "sink_manipulated": False,
        "donor_state_patched": False,
        "q_r_or_residual_patched": False,
        "windows_earlier_than_16_allowed": False,
        "stage4_authorized": False,
    }
    write_json(OUT / "config/stage3c4_config.json", config)
    write_json(OUT / "audit/contribution_definition.json", {
        "frozen_at": created,
        "definition": "c_T(t,l,h)=sum_{j in T} alpha(t,l,h,j)*V(l,h,j)",
        "intervention": "c_T -> 0 in FP32 partition arithmetic, cast patched head output to native dtype before W_O",
        "reused_runtime_semantics": "code/visual_reasoning/stage3c3r/runtime.py:apply_source_contribution_gain",
        "extended_runtime": "code/visual_reasoning/stage3c4/runtime.py:apply_source_contribution_window",
        "directly_fixed": ["Q", "K", "V", "attention probabilities", "non-target source contribution"],
        "downstream_recomputation": True,
    })
    print(json.dumps({
        "validation": validation_ids,
        "primary": primary_ids,
        "layer_scopes": scopes,
        "temporal_windows": windows,
        "interaction_cells": {key: {"layer_count": len(value["layers"]), "backward": value["backward"]} for key, value in interactions.items()},
        "all_primary_t16_available": all(
            row["windows"]["T16"]["available"] for row in availability if row["cohort_role"] == "primary"
        ),
    }, indent=2))


if __name__ == "__main__":
    main()
