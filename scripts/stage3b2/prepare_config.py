#!/usr/bin/env python3
"""Freeze the Stage 3B.2 cohort, switch schedules, controls, and analysis rules."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3b2.checkpoints import (
    ED_RELATIVE_OFFSETS,
    NORMALIZED_PROGRESS,
    build_switch_schedule,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/stage3a/cohort/primary_manifest.jsonl"
ANNOTATIONS = ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl"
OUTPUT = ROOT / "outputs/stage3b2"
SMOKE_BASES = ("118", "148", "113")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    cohort = read_jsonl(SOURCE)
    annotations = read_jsonl(ANNOTATIONS)
    by_base = {str(row["base_problem_id"]): row for row in annotations}
    bases = [str(row["base_problem_id"]) for row in cohort]
    if len(cohort) != 49 or len(set(bases)) != 49 or set(bases) != set(by_base):
        raise RuntimeError("Stage 3B.2 must preserve the exact 49-base Stage 3A cohort")
    if any(row["manual_audit_status"] != "pass" for row in annotations):
        raise RuntimeError("Every E_d annotation must pass manual audit before schedule freeze")

    schedules = []
    for item in cohort:
        base = str(item["base_problem_id"])
        annotation = by_base[base]
        checkpoints = build_switch_schedule(int(annotation["ed_generated_index"]))
        schedules.append(
            {
                "base_problem_id": base,
                "example_id": str(item["example_id"]),
                "prefix_sha256": item["prefix_sha256"],
                "e0_start_token": int(annotation["e0_start_token"]),
                "ed_generated_index": int(annotation["ed_generated_index"]),
                "history_before_ed_token_count": len(annotation["history_before_ed_token_ids"]),
                "checkpoint_count": len(checkpoints),
                "checkpoints": checkpoints,
            }
        )
    total = sum(row["checkpoint_count"] for row in schedules)
    smoke = [row for base in SMOKE_BASES for row in cohort if str(row["base_problem_id"]) == base]
    if len(smoke) != 3 or any(row["edit_tier"] != "tier1_local_numeric_label" for row in smoke):
        raise RuntimeError("Smoke must contain three numeric-label bases")

    for directory in (
        "config/shards",
        "smoke",
        "scoring",
        "analysis/figures",
        "summaries",
        "raw/smoke",
        "raw/shards",
    ):
        ensure_directory(OUTPUT / directory)
    write_jsonl(OUTPUT / "config/cohort_manifest.jsonl", cohort)
    write_jsonl(OUTPUT / "config/smoke_manifest.jsonl", smoke)
    write_jsonl(OUTPUT / "config/switch_checkpoint_schedule.jsonl", schedules)
    write_json(
        OUTPUT / "config/stage3b2_config.json",
        {
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "source_manifest": str(SOURCE.relative_to(ROOT)),
            "annotation_manifest": str(ANNOTATIONS.relative_to(ROOT)),
            "primary_unit": "base_problem_id",
            "base_problem_count": 49,
            "evidence_strata": {"tier1_local_numeric_label": 45, "tier3_structural_visual_edit": 4},
            "selection_used_attention": False,
            "model_protocol": "Qwen3-VL-4B-Thinking locked Stage 1 protocol; raw teacher-forced scoring",
            "seed": 1234,
            "ed_definition": "E0 plus the token longest-common-prefix length of the frozen Stage 3A original/counterfactual evidence continuations",
            "readout": "length-normalized log probability of each complete divergent suffix under the shared pre-E_d context",
            "switch_semantics": {
                "switch_generated_index_k": "the query at absolute position prompt_length + k - 1, which predicts y_k, and every later query use donor visual K/V",
                "generation_start": "k=0 includes the final prompt query that predicts y_0",
                "Ed": "the query predicting the first divergent evidence token uses donor visual K/V",
                "recipient_fixed": ["token identities", "prompt/question K/V", "all non-visual K/V", "reasoning history before each switched query"],
                "donor": "post-RoPE visual-position K and projected V from a matching-shape full-sequence eager source run",
                "layers": 36,
                "visual_scope": "all visual prompt positions",
            },
            "controls": ["no_switch_OO_CC", "self_OO_CC", "O_to_C", "C_to_O", "O_to_sham"],
            "checkpoint_coordinates": {
                "ed_relative_offsets": list(ED_RELATIVE_OFFSETS),
                "include_ed": True,
                "normalized_progress": list(NORMALIZED_PROGRESS),
                "normalized_mapping": "floor(requested_progress * E_d)",
                "deduplication": "score each exact switch index once and retain all labels",
                "unique_problem_checkpoint_pairs": total,
            },
            "primary_metrics": {
                "S_O_to_C": "D_OO - D_OC",
                "S_C_to_O": "D_CO - D_CC",
                "BRI": "mean(S_O_to_C, S_C_to_O)",
                "sham": "D_OO - D_OS",
                "normalized_BRI_secondary": "BRI / (D_OO - D_CC), with no clipping and only a positive finite denominator",
            },
            "timing_category_rules": {
                "R1_persistent_late_retrieval": "bidirectionally source-consistent and normalized BRI >=0.50 at E_d-1 or E_d",
                "R2_early_retrieval_commitment": "maximum normalized BRI >=0.50 at or before E_d-16, but maximum at E_d-1/E_d <0.25",
                "R4_weak_identity_specific_retrieval": "maximum absolute normalized BRI <0.25",
                "R5_complex_nonmonotonic": "at least two sign changes or maximum adjacent normalized-BRI change >0.50",
                "R3_gradual_source_influence": "all remaining curves",
            },
            "decision_rules": {
                "GO_layerwise_transfer": "at E_d-1 or E_d: bootstrap CI for median BRI excludes zero, >=70% are bidirectionally source-consistent, median normalized BRI >=0.50, median absolute sham is <20% of median absolute O-to-C, and self switches are transparent",
                "GO_earlier_commitment": "late GO fails, but at or before E_d-16 the same consistency/CI/sham criteria hold with median normalized BRI >=0.50 and late median normalized BRI <0.25",
                "REDIRECT_generic_distributed": "neither GO rule holds, or sham is comparable to target switching",
            },
            "bootstrap": {"resamples": 10_000, "seed": 1234, "unit": "base_problem_id"},
            "rollout_checkpoints": ["Ed_minus_16", "Ed_minus_4", "Ed"],
            "rollout_max_new_tokens": 64,
            "attention_role": "secondary exact-event comparison only after causal scores are frozen",
            "smoke_base_problem_ids": list(SMOKE_BASES),
            "required_gpu_class": "A5000",
            "prohibited": [
                "layer localization", "Q/R carrier patching", "ROI-specific switching",
                "attention-vs-MLP analysis", "head/path analysis", "multi-evidence refresh",
            ],
            "stage3b3_started": False,
        },
    )
    print(json.dumps({"cohort": len(cohort), "smoke": list(SMOKE_BASES), "checkpoints": total}, indent=2))


if __name__ == "__main__":
    main()
