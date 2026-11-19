#!/usr/bin/env python3
"""Independently validate the persisted Stage 3C.1 artifact bundle."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "stage3c1"

REQUIRED_JSON = [
    "config/stage3c1_config.json",
    "config/frozen_targets.json",
    "config/temporal_grid.json",
    "config/control_heads.json",
    "config/source_classes.json",
    "audit/gqa_mapping.json",
    "audit/tensor_layout.json",
    "audit/reconstruction_check.json",
    "audit/instrumentation_faithfulness.json",
    "analysis/full_extraction_validation.json",
    "analysis/retrieval_time_contrasts.json",
    "analysis/roi_selectivity_statistics.json",
    "analysis/qk_decomposition_statistics.json",
    "analysis/softmax_competition_statistics.json",
    "analysis/attention_vs_value_statistics.json",
    "analysis/source_mass_profiles.json",
    "analysis/sink_candidate_summary.json",
    "analysis/causal_effect_correlations.json",
    "analysis/per_head_phenotypes.json",
    "summaries/stage3c1_acceptance.json",
]

REQUIRED_TEXT = [
    "audit/attention_equations.md",
    "summaries/stage3c1_summary.md",
    "summaries/next_stage_recommendation.md",
]

JSONL_COUNTS = {
    "extraction/per_head_per_time_metrics.jsonl": 14_820,
    "extraction/source_attention_mass.jsonl": 14_820,
    "extraction/qk_geometry.jsonl": 14_820,
    "extraction/softmax_competition.jsonl": 14_820,
    "extraction/entropy_metrics.jsonl": 14_820,
    "extraction/value_contributions.jsonl": 14_820,
    "extraction/wo_residual_contributions.jsonl": 14_820,
    "controls/irrelevant_roi_comparison.jsonl": 1_184,
    "controls/noncausal_head_comparison.jsonl": 2_368,
    "controls/upstream_state_control.jsonl": 444,
    "controls/w5_head10_secondary.jsonl": 148,
    "controls/sink_candidate_metrics.jsonl": 7_040,
}

REQUIRED_FIGURES = {
    "01_target_a_attention_over_time.png",
    "02_target_b_attention_over_time.png",
    "03_target_vs_irrelevant_density.png",
    "04_qk_norm_cosine_logit_decomposition.png",
    "05_competition_margin_over_time.png",
    "06_all_and_visual_entropy_over_time.png",
    "07_attention_vs_alpha_v.png",
    "08_attention_vs_post_wo.png",
    "09_source_mass_composition.png",
    "10_causal_vs_noncausal_heads.png",
    "11_w4_vs_w5_upstream.png",
    "12_shared_head6_profile.png",
    "13_candidate_sink_mass_over_time.png",
    "14_attention_vs_causal_roi_effect.png",
}

RAW_VECTOR_KEYS = {
    "k_norm",
    "value_norm",
    "cosine",
    "raw_dot",
    "scaled_logits",
    "final_logits",
    "attention",
}


def load_json(relative: str) -> object:
    with (OUT / relative).open(encoding="utf-8") as handle:
        return json.load(handle)


def check_jsonl(relative: str, expected: int) -> tuple[int, set[str]]:
    count = 0
    bases: set[str] = set()
    with (OUT / relative).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            row = json.loads(line)
            if "base_problem_id" not in row:
                raise AssertionError(f"{relative}:{line_number} lacks base_problem_id")
            bases.add(str(row["base_problem_id"]))
            count += 1
    if count != expected:
        raise AssertionError(f"{relative}: expected {expected} rows, observed {count}")
    return count, bases


def validate_raw_npz() -> dict[str, object]:
    paths = sorted((OUT / "extraction" / "raw_tensors").glob("*/*.npz"))
    if len(paths) != 444:
        raise AssertionError(f"expected 444 raw NPZ files, observed {len(paths)}")

    bases: set[str] = set()
    conditions: Counter[str] = Counter()
    layer_counts: Counter[int] = Counter()
    checked_slices = 0
    unavailable_checkpoints = 0

    for path in paths:
        bases.add(path.parent.name)
        stem_parts = path.stem.rsplit("_layer", 1)
        condition = stem_parts[0]
        layer = int(stem_parts[1])
        conditions[condition] += 1
        layer_counts[layer] += 1

        with np.load(path, allow_pickle=False) as arrays:
            required = {
                "offsets_from_E_d",
                "absolute_query_positions",
                "valid_source_lengths",
                "logical_heads",
                "q_norm",
                *RAW_VECTOR_KEYS,
            }
            if set(arrays.files) != required:
                raise AssertionError(f"{path}: unexpected keys {sorted(arrays.files)}")

            offsets = arrays["offsets_from_E_d"]
            absolute = arrays["absolute_query_positions"]
            valid = arrays["valid_source_lengths"]
            logical_heads = arrays["logical_heads"]
            full_w4_grid = [-16, -8, -4, -2, -1, 0]
            observed_offsets = offsets.tolist()
            if layer == 32:
                expected_offsets = [-1, 0]
            else:
                if observed_offsets not in (full_w4_grid, full_w4_grid[1:]):
                    raise AssertionError(f"{path}: temporal grid mismatch")
                expected_offsets = observed_offsets
                unavailable_checkpoints += len(full_w4_grid) - len(observed_offsets)
            expected_heads = 4 if layer == 32 else 8
            if observed_offsets != expected_offsets:
                raise AssertionError(f"{path}: temporal grid mismatch")
            expected_times = len(expected_offsets)
            if (
                offsets.shape != absolute.shape
                or offsets.shape != valid.shape
                or offsets.shape != (expected_times,)
            ):
                raise AssertionError(f"{path}: checkpoint metadata shape mismatch")
            if logical_heads.shape != (expected_times, expected_heads):
                raise AssertionError(f"{path}: logical-head shape mismatch")
            if arrays["q_norm"].shape != (expected_times, expected_heads):
                raise AssertionError(f"{path}: q_norm shape mismatch")

            vector_shape = arrays["attention"].shape
            if vector_shape[:2] != (expected_times, expected_heads):
                raise AssertionError(f"{path}: vector tensor shape mismatch")
            if any(arrays[key].shape != vector_shape for key in RAW_VECTOR_KEYS):
                raise AssertionError(f"{path}: raw vector tensors do not share a shape")

            for time_index, source_length in enumerate(valid.tolist()):
                if source_length == 0:
                    unavailable_checkpoints += 1
                    if absolute[time_index] != -1:
                        raise AssertionError(f"{path}: unavailable checkpoint has a query position")
                    continue
                if source_length != absolute[time_index] + 1:
                    raise AssertionError(f"{path}: causal source length does not close at query")
                active_heads = logical_heads[time_index] >= 0
                if not np.any(active_heads):
                    raise AssertionError(f"{path}: valid checkpoint has no active heads")
                if not np.isfinite(arrays["q_norm"][time_index, active_heads]).all():
                    raise AssertionError(f"{path}: nonfinite q norm at a valid checkpoint")
                for key in RAW_VECTOR_KEYS:
                    if not np.isfinite(arrays[key][time_index, active_heads, :source_length]).all():
                        raise AssertionError(f"{path}: nonfinite {key} in a valid source slice")
                checked_slices += 1

    if len(bases) != 37:
        raise AssertionError(f"expected 37 raw-tensor bases, observed {len(bases)}")
    if conditions != Counter({name: 111 for name in ["O", "O_sham", "C", "C_sham"]}):
        raise AssertionError(f"raw-tensor condition counts mismatch: {conditions}")
    if layer_counts != Counter({28: 148, 29: 148, 32: 148}):
        raise AssertionError(f"raw-tensor layer counts mismatch: {layer_counts}")

    return {
        "file_count": len(paths),
        "base_problem_count": len(bases),
        "condition_counts": dict(conditions),
        "layer_counts": {str(key): value for key, value in layer_counts.items()},
        "valid_checkpoint_slices_checked": checked_slices,
        "unavailable_checkpoint_slices": unavailable_checkpoints,
    }


def main() -> None:
    checks: list[dict[str, object]] = []

    for relative in REQUIRED_JSON:
        load_json(relative)
    checks.append({"name": "required_json_parse", "passed": True, "count": len(REQUIRED_JSON)})

    missing_text = [relative for relative in REQUIRED_TEXT if not (OUT / relative).is_file()]
    if missing_text:
        raise AssertionError(f"missing text outputs: {missing_text}")
    checks.append({"name": "required_text_exists", "passed": True, "count": len(REQUIRED_TEXT)})

    line_counts: dict[str, int] = {}
    jsonl_bases: set[str] | None = None
    for relative, expected in JSONL_COUNTS.items():
        count, bases = check_jsonl(relative, expected)
        line_counts[relative] = count
        if jsonl_bases is None:
            jsonl_bases = bases
        if bases != jsonl_bases:
            raise AssertionError(f"{relative}: base cohort mismatch")
    if len(jsonl_bases or set()) != 37:
        raise AssertionError("JSONL files do not cover exactly 37 bases")
    checks.append({"name": "jsonl_integrity", "passed": True, "row_counts": line_counts})

    config = load_json("config/stage3c1_config.json")
    targets = load_json("config/frozen_targets.json")
    controls = load_json("config/control_heads.json")
    assert isinstance(config, dict) and isinstance(targets, dict) and isinstance(controls, dict)
    expected_targets = [
        {"target_id": "target_a", "coordinate": "E_d", "window": "W4", "layer_index": 29, "causal_heads": [11, 6, 15, 12]},
        {"target_id": "target_b", "coordinate": "E_d-1", "window": "W4", "layer_index": 28, "causal_heads": [16, 0, 3, 6]},
    ]
    if targets["targets"] != expected_targets:
        raise AssertionError("frozen target definitions differ from the plan")
    if controls["target_a_layer29"] != [0, 1, 2, 3] or controls["target_b_layer28"] != [1, 2, 4, 5]:
        raise AssertionError("prospective noncausal controls differ from the plan")
    if config["base_problem_count"] != 37 or config["selection_used_stage3c1_attention"]:
        raise AssertionError("cohort or selection-freeze configuration mismatch")
    checks.append({"name": "frozen_design", "passed": True})

    validation = load_json("analysis/full_extraction_validation.json")
    assert isinstance(validation, dict)
    tolerances_ok = (
        validation["base_problem_count"] == 37
        and validation["condition_count"] == 4
        and validation["head_row_count"] == 14_820
        and validation["maximum_probability_reconstruction_error"] == 0.0
        and validation["maximum_head_output_reconstruction_error"] == 0.0
        and validation["maximum_source_mass_error"] <= 0.005
        and validation["maximum_alpha_v_partition_error"] <= 1e-5
        and validation["maximum_wo_partition_error"] <= 1e-5
        and validation["all_finite"]
        and validation["all_condition_layouts_exact"]
        and not validation["selection_used_stage3c1_attention"]
        and not validation["attention_manipulated"]
    )
    if not tolerances_ok:
        raise AssertionError("full extraction validation is outside frozen tolerances")
    checks.append({"name": "numerical_validation", "passed": True})

    raw_summary = validate_raw_npz()
    checks.append({"name": "raw_tensor_integrity", "passed": True, **raw_summary})

    observed_figures = {path.name for path in (OUT / "analysis" / "figures").glob("*.png")}
    missing_figures = sorted(REQUIRED_FIGURES - observed_figures)
    if missing_figures:
        raise AssertionError(f"missing required figures: {missing_figures}")
    checks.append({"name": "required_figures", "passed": True, "required": 14, "observed": len(observed_figures)})

    acceptance = load_json("summaries/stage3c1_acceptance.json")
    assert isinstance(acceptance, dict)
    if not (
        acceptance["status"] == "PASS"
        and acceptance["passed"] == acceptance["total"] == 20
        and all(item["passed"] for item in acceptance["criteria"])
        and acceptance["recommendation_count"] == 1
        and not acceptance["stage3c2_or_stage4_started"]
    ):
        raise AssertionError("acceptance or stop-boundary record failed")
    later_outputs = [path.as_posix() for path in ROOT.glob("outputs/stage3c2*")] + [
        path.as_posix() for path in ROOT.glob("outputs/stage4*")
    ]
    if later_outputs:
        raise AssertionError(f"prohibited later-stage outputs exist: {later_outputs}")
    checks.append({"name": "acceptance_and_stop_boundary", "passed": True})

    report = {
        "stage": "Stage 3C.1",
        "status": "PASS",
        "checks_passed": len(checks),
        "checks_total": len(checks),
        "checks": checks,
        "stage_acceptance": "20/20 PASS",
        "attention_is_descriptive_not_causal": True,
        "later_experiment_started": False,
    }
    output_path = OUT / "summaries" / "artifact_validation.json"
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
