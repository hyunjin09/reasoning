#!/usr/bin/env python3
"""Finalize a Stage 3B.7 stop caused by the pre-primary validation gate."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    validation = read_json(OUT / "validation/roi_path_validation.json")
    if validation["status"] != "FAIL":
        raise RuntimeError("This finalizer is only for a failed Phase-A validation gate")
    if list((OUT / "scoring/raw").glob("primary_*")):
        raise RuntimeError("Primary Stage 3B.7 outputs exist; refusing failure finalization")
    ensure_directory(OUT / "analysis")
    ensure_directory(OUT / "summaries")
    shutil.copyfile(
        OUT / "config/validation_manifest.jsonl",
        OUT / "validation/validation_manifest.jsonl",
    )
    empty_scoring = (
        "all_visual_path_results.jsonl",
        "target_roi_results.jsonl",
        "visual_complement_results.jsonl",
        "irrelevant_roi_results.jsonl",
        "target_ring_results.jsonl",
        "k_only_results.jsonl",
        "v_only_results.jsonl",
        "kv_results.jsonl",
        "optional_alpha_results.jsonl",
    )
    for filename in empty_scoring:
        write_jsonl(OUT / "scoring" / filename, [])

    diagnostic = {
        "direct_observation": (
            "The frozen disjoint validation gate failed only because the "
            "E_d-1/W4/Top_2 all-visual median sham-to-semantic ratio was "
            "0.269893147759381, above the prospectively frozen <0.25 limit."
        ),
        "confirmed_not_causes": [
            "legacy all-visual implementation mismatch",
            "ROI or token-layout mismatch",
            "source-position leakage",
            "non-target logical-query-head changes",
            "self-swap non-transparency",
            "nonfinite scores",
            "deterministic replication failure",
        ],
        "cheap_diagnostic": {
            "Ed__W4__Top_4": {
                "median_BPR": 0.8364291774380646,
                "bidirectional_fraction": 0.875,
                "median_absolute_sham_effect": 0.07071231221516894,
                "median_sham_to_semantic_ratio": 0.11433686483328587,
            },
            "Ed_minus_1__W4__Top_2": {
                "median_BPR": 0.21382074525331518,
                "bidirectional_fraction": 0.75,
                "median_absolute_sham_effect": 0.059709925471579384,
                "median_sham_to_semantic_ratio": 0.269893147759381,
                "near_zero_semantic_bases": ["83", "101"],
                "interpretation": (
                    "Absolute sham shifts were modest, but semantic restoration was "
                    "near zero on multiple validation bases, making the relative artifact "
                    "control fail. This does not justify changing the frozen ratio threshold."
                ),
            },
        },
        "diagnosis_status": "supported",
        "supported_diagnosis": (
            "One frozen target lacks sufficiently clean sham-relative semantic restoration "
            "on the disjoint validation cohort; the intervention implementation itself passed."
        ),
        "repeat_inference_performed": False,
        "primary_inference_started": False,
        "threshold_changed_after_scores": False,
    }
    write_json(OUT / "validation/validation_failure_diagnostic.json", diagnostic)
    not_run = {
        "status": "NOT_RUN_AFTER_VALIDATION_FAILURE",
        "reason": "The frozen pre-primary Phase-A validation gate failed.",
        "primary_base_count_scored": 0,
        "stage3b7_primary_scores_inspected": False,
    }
    for filename in (
        "roi_path_statistics.json",
        "spatial_localization_analysis.json",
        "kv_decomposition_statistics.json",
        "kv_interaction_analysis.json",
        "attention_secondary_analysis.json",
        "exploratory_w5_analysis.json",
    ):
        write_json(OUT / "analysis" / filename, {**not_run, "artifact": filename})
    write_json(OUT / "validation/kv_decomposition_validation.json", {
        "status": "NOT_RUN_AFTER_PHASE_A_VALIDATION_FAILURE",
        "gate_passed": False,
        "primary_or_validation_phase_b_inference_started": False,
    })

    criteria = [
        (1, "two robust W4 primary targets frozen exactly", "PASS"),
        (2, "W5/head_10 remains exploratory only", "PASS"),
        (3, "exact Stage 3A edit ROI used rather than attention selection", "PASS"),
        (4, "ROI-to-token mappings manually validated", "PASS"),
        (5, "target/complement/matched irrelevant groups frozen before scoring", "PASS"),
        (6, "all-V source effect reproduces Stage 3B.6", "PASS"),
        (7, "ROI source swaps are bidirectional", "PASS_VALIDATION_ONLY"),
        (8, "self and paired sham controls implemented", "FAIL_SHAM_GATE"),
        (9, "source-group isolation mechanically audited", "PASS"),
        (10, "Phase B occurs only if ROI gate passes", "PASS_NOT_RUN"),
        (11, "K/V interventions remain query-head-selective under GQA", "PASS_UNIT_TEST_ONLY_PHASE_B_NOT_RUN"),
        (12, "K+V reproduces target ROI path", "NOT_EVALUATED"),
        (13, "non-target query heads remain recipient-native", "PASS_VALIDATION_AND_UNIT_TEST"),
        (14, "base_problem_id remains statistical unit", "PASS"),
        (15, "raw attention remains secondary only", "PASS_NOT_RUN"),
        (16, "no prohibited later experiment started", "PASS"),
        (17, "explicit GO/REDIRECT recommendation written after primary", "NOT_EVALUATED_PRIMARY_NOT_RUN"),
    ]
    write_json(OUT / "summaries/stage3b7_acceptance.json", {
        "status": "FAIL",
        "stop_stage": "pre-primary Phase-A validation",
        "validation_gate": validation,
        "criteria": [
            {"criterion": number, "description": description, "status": status}
            for number, description, status in criteria
        ],
        "primary_phase_a_started": False,
        "phase_b_started": False,
        "later_stage_experiments_started": [],
    })
    recommendation = (
        "REDESIGN — Strengthen or replace the sham-sensitive E_d-1/W4/Top_2 target "
        "under a newly approved prospective protocol; do not reinterpret the current "
        "threshold or start the primary cohort from this failed gate."
    )
    write_json(OUT / "summaries/next_stage_recommendation.json", {
        "recommendation": recommendation,
        "status": "requires user review and a new approved plan",
        "no_new_experiment_authorized": True,
    })
    (OUT / "summaries/next_stage_recommendation.md").write_text(
        "# Stage 3B.7 Next-Step Recommendation\n\n"
        f"**{recommendation}**\n\n"
        "The other primary target passed this validation control, and all mechanical checks passed. A redesigned protocol could prospectively retain only independently clean targets, replace the relative artifact gate with a justified alternative, or acquire a larger disjoint validation cohort. Choosing among these is a new research action and requires review; none was started.\n",
        encoding="utf-8",
    )
    summary = f"""# Stage 3B.7 — Validation-Gate Result

**Status: FAIL before primary scoring.**

## Completed work

- Froze the exact 37-base primary cohort and disjoint 8-base validation cohort.
- Froze `E_d/W4/Top_4` heads `[11, 6, 15, 12]` and `E_d-1/W4/Top_2` heads `[16, 0]`.
- Constructed and manually validated exact edited-pixel target ROIs, complements, fixed rings, and cardinality-matched irrelevant regions for all 45 bases without using attention.
- Implemented and unit-tested query-head-selective K-only, V-only, and K+V mechanics under grouped-query attention.
- Ran only the disjoint 8-base Phase-A validation set in tmux 8 on two A5000 GPUs.

## Validation outcome

All mechanical and reproducibility checks passed:

- legacy all-V scores: exact;
- token layouts and ROI/source isolation: exact;
- self swaps: exact;
- non-target query heads unchanged;
- deterministic repeats: exact;
- finite scores: all;
- peak allocation: 9.01 GB per shard or lower.

The semantic validation gate failed for one of the two frozen targets:

- `E_d/W4/Top_4`: median BPR `0.8364`, bidirectional fraction `0.875`, median sham/semantic `0.1143` — passes.
- `E_d-1/W4/Top_2`: median BPR `0.2138`, bidirectional fraction `0.750`, median sham/semantic `0.2699` — fails the frozen `<0.25` rule.

The one permitted diagnostic found modest median absolute sham shift (`0.0597`) but near-zero semantic restoration on bases `83` and `101`; this is a real sham-relative validation limitation, not a mechanical implementation failure. The threshold was not changed and inference was not repeated.

## Stop boundary

No one from the 37-base primary cohort was scored in Stage 3B.7. Phase B, optional alpha, W5/head_10, attention triangulation, and all later experiments were not run. Empty required scoring manifests explicitly record this stop rather than masquerading as primary results.

Attention was not used to choose any ROI and no attention-only causal claim is made.

## Recommendation

**{recommendation}**
"""
    (OUT / "summaries/stage3b7_summary.md").write_text(summary, encoding="utf-8")


if __name__ == "__main__":
    main()
