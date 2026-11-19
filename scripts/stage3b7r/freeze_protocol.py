#!/usr/bin/env python3
"""Freeze the Stage 3B.7-R redesign and outcome-blind prospective screen."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import write_json, write_jsonl, write_text
from visual_reasoning.stage3b7r.protocol import validate_disjoint_split


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7r"


# Prospective single-label edits selected by image/question inspection only.
# Each counterfactual maps to another answer choice without changing any other
# task-relevant visual content. Pixel ROIs remain pending coordinate audit.
SPECS = {
    "162": ("angle BAC is 40 degrees", "angle BAC is 30 degrees", "B", "central angle BOC changes from 80 to 60 degrees"),
    "173": ("central angle DOB is 50 degrees", "central angle DOB is 70 degrees", "D", "inscribed angle BAD changes from 25 to 35 degrees"),
    "183": ("circle radius is 2", "circle radius is 4", "B", "the tangent construction scales PC from 2sqrt(3) to 4sqrt(3)"),
    "184": ("circle radius is 2", "circle radius is 1", "B", "the tangent construction scales CD from 2sqrt(3) to sqrt(3)"),
    "190": ("angle APB is 50 degrees", "angle APB is 60 degrees", "B", "the tangent-chord geometry changes angle ACB from 65 to 60 degrees"),
    "199": ("chord CD is 24", "chord CD is 10", "B", "with radius 13, center-to-chord distance OX changes from 5 to 12"),
    "201": ("angle ATM is 28 degrees", "angle ATM is 14 degrees", "A", "equal chord distances preserve the copied angle, changing CAM from 28 to 14 degrees"),
    "202": ("upper transversal angle is 38 degrees", "upper transversal angle is 28 degrees", "C", "parallel-line angle sum changes ABC from 71 to 61 degrees"),
    "204": ("side XY is 10", "side XY is 6", "A", "with XM=2 and XN=6, NZ changes from 24 to 12"),
    "208": ("angle JMK is 55 degrees", "angle JMK is 20 degrees", "B", "rectangle complement changes KML from 35 to 70 degrees"),
    "210": ("segment ED is 5", "segment ED is 4", "A", "parallel-segment similarity changes AE from 15 to 12"),
    "214": ("angle DAB is 32 degrees", "angle DAB is 72 degrees", "C", "parallelogram supplement changes ADC from 128 to 108 degrees"),
    "216": ("small-triangle side FE is 3", "small-triangle side FE is 2", "C", "similarity scale 45/15 changes DE from 9 to 6"),
    "217": ("parallelogram side is 20", "parallelogram side is 18", "A", "with the other side 12, perimeter changes from 64 to 60"),
    "222": ("large rectangle area is 32", "large rectangle area is 2", "B", "area similarity with the 4-inch, area-8 rectangle changes x from 8 to 2"),
    "227": ("rectangle side is 16", "rectangle side is 8", "C", "with the other side 9, area changes from 144 to 72"),
    "229": ("upper trapezoid base is 54", "upper trapezoid base is 22", "B", "with lower base 86, the median changes from 70 to 54"),
    "233": ("isosceles apex angle is 70 degrees", "isosceles apex angle is 40 degrees", "B", "each base angle changes from 55 to 70 degrees"),
    "234": ("angle AGD is 108 degrees", "angle AGD is 72 degrees", "B", "similar polygons copy the corresponding angle ADC from 108 to 72 degrees"),
    "235": ("angle 3 is 110 degrees", "angle 3 is 55 degrees", "A", "parallel rays copy the corresponding angle 1 from 110 to 55 degrees"),
    "237": ("angle QRS is 33 degrees", "angle QRS is 12 degrees", "D", "with angle SQR=39, angle QSR changes from 108 to 129 degrees"),
    "241": ("right-triangle hypotenuse is 20", "right-triangle hypotenuse is 12", "B", "in the 30-60-90 triangle, y changes from 10 to 6"),
    "246": ("circle diameter is 6.2", "circle diameter is 12", "C", "circumference changes from approximately 19.5 to 37.7"),
    "252": ("median BE is 9", "median BE is 18", "D", "centroid division changes BQ from 6 to 12"),
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    sentinels = [
        OUT / "config/stage3b7r_config.json",
        OUT / "validation_cohort/candidate_screening.jsonl",
        OUT / "validation_cohort/prospective_generation_manifest.jsonl",
    ]
    if any(path.exists() for path in sentinels):
        raise FileExistsError("Stage 3B.7-R protocol/screen is already frozen")

    plan = ROOT / "plan/stage3b7r_plan.md"
    heads = ROOT / "outputs/stage3b6/config/frozen_head_candidates.json"
    primary_path = ROOT / "outputs/stage3b7/config/cohort_manifest.jsonl"
    historical_path = ROOT / "outputs/stage3b7/config/validation_manifest.jsonl"
    primary = {int(row["base_problem_id"]) for row in read_jsonl(primary_path)}
    historical = {int(row["base_problem_id"]) for row in read_jsonl(historical_path)}
    diagnostic = {148, 136, 6, 83, 93, 96, 101, 126}
    fresh_screen = {int(base) for base in SPECS}
    validate_disjoint_split(fresh=fresh_screen, primary=primary, historical=historical, diagnostic=diagnostic)

    dataset_rows = load_mathverse_rows(args.dataset_root)
    vision = {
        int(row["problem_index"]): row
        for row in dataset_rows
        if str(row["problem_version"]) == "Vision Dominant"
    }
    prior_attempted = {
        int(row["base_problem_id"])
        for row in read_jsonl(ROOT / "outputs/stage1/discovery/preparation/cohort_attempt_manifest.jsonl")
    }
    prior_screened = set()
    for path in (
        ROOT / "outputs/stage3a/cohort/candidate_screening.jsonl",
        ROOT / "outputs/stage3a/cohort/backup_candidate_screening.jsonl",
        ROOT / "outputs/stage3a/cohort/round3_candidate_screening.jsonl",
    ):
        prior_screened.update(int(row["base_problem_id"]) for row in read_jsonl(path))
    prior = prior_attempted | prior_screened | primary | historical
    eligible_screened = [base for base in range(156, 253) if base in vision and base not in prior]
    if not fresh_screen <= set(eligible_screened):
        raise RuntimeError("Prospective screen contains a previously used or unavailable base")

    frozen_at = datetime.now(timezone.utc).isoformat()
    screening = []
    exclusions = []
    generation = []
    for base in eligible_screened:
        row = vision[base]
        selected = str(base) in SPECS
        item = {
            "base_problem_id": str(base),
            "example_id": str(row["sample_index"]),
            "variant": "Vision Dominant",
            "screening_range": [156, 252],
            "selected_for_prospective_generation": selected,
            "selection_used_attention": False,
            "selection_used_generation_outcome": False,
            "selection_used_stage3b7r_causal_outcome": False,
            "question": row["question"],
            "ground_truth_answer": row["answer"],
            "image_reference": row["image"],
            "frozen_at": frozen_at,
        }
        if selected:
            fact_o, fact_c, answer_c, validity = SPECS[str(base)]
            item.update(
                {
                    "screening_decision": "prospective_generation_batch_1",
                    "original_fact": fact_o,
                    "counterfactual_fact": fact_c,
                    "counterfactual_expected_answer": answer_c,
                    "semantic_validity_basis": validity,
                    "edit_tier": "tier1_local_numeric_label",
                }
            )
            generation.append(
                {
                    "base_problem_id": str(base),
                    "example_id": str(row["sample_index"]),
                    "variant": "Vision Dominant",
                    "selection_reason": "outcome-blind isolated numeric-label edit with a fixed-choice-valid counterfactual",
                }
            )
        else:
            reason = "not selected in bounded batch 1: no prospectively specified single-label edit-to-answer mapping"
            item.update({"screening_decision": "not_selected_batch_1", "reason": reason})
            exclusions.append(
                {
                    "base_problem_id": str(base),
                    "example_id": str(row["sample_index"]),
                    "stage": "prospective_visual_screen",
                    "reason": reason,
                    "causal_scores_inspected": False,
                    "frozen_at": frozen_at,
                }
            )
        screening.append(item)

    target_a = {
        "target_id": "target_a",
        "cell_id": "Ed__W4",
        "coordinate": "Ed",
        "window": "W4",
        "fine_window": "F28_29",
        "layer_index": 29,
        "unit_id": "Top_4",
        "heads": [11, 6, 15, 12],
        "selection_source": "Stage 3B.6 frozen Top_4; passed historical Stage 3B.7 validation but requires fresh replication",
    }
    target_br = {
        "target_id": "target_b_r",
        "cell_id": "Ed_minus_1__W4",
        "coordinate": "Ed_minus_1",
        "window": "W4",
        "fine_window": "F28_29",
        "layer_index": 28,
        "unit_id": "Top_4",
        "heads": [16, 0, 3, 6],
        "selection_source": "exact Stage 3B.6 frozen Top_4; no Stage 3B.7-R head search",
    }
    targets = [target_a, target_br]
    config = {
        "frozen_at": frozen_at,
        "source_plan": str(plan.relative_to(ROOT)),
        "source_plan_sha256": sha256(plan),
        "source_stage3b6_heads": str(heads.relative_to(ROOT)),
        "source_stage3b6_heads_sha256": sha256(heads),
        "historical_stage3b7_failure_immutable": True,
        "model": "Qwen3-VL-4B-Thinking",
        "model_checkpoint": "/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e",
        "locked_generation_protocol": {
            "do_sample": True,
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "repetition_penalty": 1.0,
            "presence_penalty": 0.0,
            "max_new_tokens": 40960,
            "seed": 1234,
            "gpu_class": "NVIDIA RTX A5000",
        },
        "execution": {"tmux_session": "8", "slurm_job_id": "106936", "gpus": 2, "new_slurm_submission": False},
        "targets": targets,
        "conditions": ["O", "O_sham", "C", "C_sham"],
        "validation": {
            "target_size": [12, 16],
            "minimum": 12,
            "candidate_batch_size": len(generation),
            "final_selection_rule": "ascending base_problem_id among completed-correct, manually edit-valid, strict-E_d-valid cases; retain first 16",
            "bootstrap_iterations": 10000,
            "bootstrap_seed": 1234,
            "semantic_gate": {
                "target_median": ">0",
                "target_median_bootstrap_95_ci_low": ">0",
                "bidirectional_fraction": ">=0.75",
                "sham_margin_median": ">0",
                "sham_margin_bootstrap_95_ci_low": ">0",
                "irrelevant_margin_median": ">0",
                "irrelevant_margin_bootstrap_95_ci_low": ">0",
                "old_sham_to_semantic_ratio": "secondary_only",
            },
            "mechanical_gate": {
                "self_swap_exact": True,
                "non_target_heads_recipient_native": True,
                "source_position_isolation_exact": True,
                "bidirectional_swap_mechanics": True,
                "deterministic_repetition_exact": True,
                "finite_scores_only": True,
                "all_visual_tendency": "median positive and bidirectional fraction >=0.75",
                "gqa_kv_mechanics": True,
            },
            "target_specific_eligibility": True,
            "both_targets_fail_stop_before_primary": True,
            "replacement_cascade_prohibited": True,
        },
        "phase_a": {
            "arms": ["all_visual", "target_roi", "visual_complement", "irrelevant_roi", "target_ring"],
            "primary_holm_family": "all_visual, target_roi, visual_complement, and irrelevant_roi effects for each validation-eligible target",
            "robust_effect": "median>0; bootstrap 95% CI low>0; Holm-adjusted one-sided p<0.05; bidirectional fraction>=0.75",
            "paired_control_margin": "median>0 and bootstrap 95% CI low>0",
            "meaningful_target_or_ring_portion": "median PRR>=0.50",
            "target_greater_than_irrelevant_fraction": ">=0.75",
            "spatial_classes": {
                "ROI-Local": "target robust; target PRR>=0.75; complement PRR<0.50; irrelevant PRR<0.25",
                "ROI-Local-Plus-Context": "target robust; target PRR>=0.25; ring PRR>=0.75; ring-target PRR>=0.20",
                "Visual-Distributed": "all-V robust and (complement PRR>=0.50 or max(target,ring) PRR<0.50)",
                "ROI-Inconclusive": "primary ROI qualification gate fails",
            },
        },
        "phase_b": {
            "gated_by_phase_a": True,
            "arms": ["K", "V", "KV"],
            "robust_effect": "median>0; bootstrap 95% CI low>0; Holm-adjusted one-sided p<0.05; bidirectional fraction>=0.75; paired sham/irrelevant margins robustly positive",
            "kv_reproduces_phase_a_tolerance": 1e-6,
            "class_thresholds": {"approaches": ">=0.75", "small": "<0.50", "interaction_each": ">=0.25", "joint_best_ci_low": ">0"},
        },
        "all_visual_reproduction_tolerance": 1e-6,
        "attention_secondary_only": True,
        "prohibited": [
            "vision_encoder_feature_localization",
            "query_or_key_subspace_analysis",
            "value_subspace_analysis",
            "mlp_feature_or_neuron_analysis",
            "Q_or_R_lifecycle_analysis",
            "multi_evidence_refresh",
            "failure_analysis",
        ],
    }

    write_json(OUT / "config/stage3b7r_config.json", config)
    write_json(OUT / "config/target_definitions.json", {"frozen_at": frozen_at, "targets": targets})
    write_json(
        OUT / "config/validation_primary_split.json",
        {
            "frozen_at": frozen_at,
            "prospective_generation_bases": sorted(fresh_screen),
            "fresh_validation_bases": None,
            "fresh_validation_status": "pending generation/edit/E_d/ROI audit",
            "primary_bases": sorted(primary),
            "historical_validation_bases": sorted(historical),
            "target_selection_diagnostic_bases": sorted(diagnostic),
            "all_disjoint": True,
        },
    )
    write_json(
        OUT / "config/primary_family.json",
        {
            "frozen_at": frozen_at,
            "targets": targets,
            "phase_a_primary_arms": ["all_visual", "target_roi", "visual_complement", "irrelevant_roi"],
            "phase_a_secondary_arms": ["target_ring"],
            "phase_b_conditional_arms": ["K", "V", "KV"],
            "statistical_unit": "base_problem_id",
            "attention_used_for_selection": False,
        },
    )
    write_jsonl(OUT / "validation_cohort/candidate_screening.jsonl", screening)
    write_jsonl(OUT / "validation_cohort/exclusion_log.jsonl", exclusions)
    write_jsonl(OUT / "validation_cohort/prospective_generation_manifest.jsonl", generation)
    write_text(
        OUT / "history/immutable_stage3b7_failure.md",
        "# Immutable Stage 3B.7 Failure\n\n"
        "Stage 3B.7 stopped before primary scoring. `E_d/W4/Top_4` passed its historical validation, "
        "but `E_d-1/W4/Top_2` failed the frozen sham/semantic gate: median 0.269893 versus required `<0.25`. "
        "All mechanical checks passed. Stage 3B.7-R is a new prospective redesign and does not alter or reinterpret that failure.\n",
    )
    print(json.dumps({"screened": len(screening), "selected": len(generation), "bases": sorted(fresh_screen)}, indent=2))


if __name__ == "__main__":
    main()
