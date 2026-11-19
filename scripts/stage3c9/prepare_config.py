#!/usr/bin/env python3
"""Create-once Stage 3C.9 configuration and prospective screen manifests."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3c8.fresh import infer_missing_numeric_facts
from visual_reasoning.stage3c9.protocol import select_prospective_screen


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"
PLAN = ROOT / "plan/stage3c9_plan.md"
IMPLEMENTATION_PLAN = ROOT / "workspace/stage3c9_implementation_plan.md"
INITIAL_BUDGET = 600
TOTAL_BUDGET = 1_000
SHARDS = 4
SEED = 1_234


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def question(row: dict[str, Any]) -> str:
    return str(row.get("question_for_eval") or row.get("query") or "")


def add_static_evidence_counts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_base: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_base.setdefault(str(row["problem_index"]), {})[str(row["problem_version"])] = row
    counts: dict[str, int] = {}
    for base, variants in by_base.items():
        text = variants.get("Text Dominant")
        vision = variants.get("Vision Dominant")
        counts[base] = len(infer_missing_numeric_facts(question(text), question(vision))) if text and vision else 0
    enriched = []
    for row in rows:
        item = dict(row)
        item["stage3c9_static_numeric_candidate_count"] = counts[str(row["problem_index"])]
        enriched.append(item)
    return enriched


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError("Stage 3C.9 configuration is create-once; outputs/stage3c9 is non-empty")
    for name in (
        "config", "cohort", "annotations", "audit", "prospective_generation/raw",
        "phase_a_source", "phase_b_checkpoint", "phase_c_lifetime", "phase_d_routes",
        "phase_e_enrichment", "secondary", "analysis/figures", "summaries",
    ):
        ensure_directory(OUT / name)

    stage3c8 = json.loads((ROOT / "outputs/stage3c8/config/stage3c8_config.json").read_text(encoding="utf-8"))
    dataset_root = Path(stage3c8["dataset_root"])
    frozen_at = datetime.now(timezone.utc).isoformat()
    rows = add_static_evidence_counts(load_mathverse_rows(dataset_root))
    screen = select_prospective_screen(rows, total_budget=TOTAL_BUDGET, initial_budget=INITIAL_BUDGET)
    row_by_example = {str(row["sample_index"]): row for row in rows}
    for item in screen:
        row = row_by_example[item["example_id"]]
        image = resolve_image_path(dataset_root, str(row["image"]))
        item.update({
            "source_image": str(image.resolve()),
            "source_image_sha256": sha256(image),
            "frozen_at": frozen_at,
        })

    taxonomy = {
        "event_role": [
            "TARGET_ENTITY_REFERENCE", "VISUAL_FACT_REFERENCE", "INTERMEDIATE_RESULT",
            "SUBGOAL_START", "SUBGOAL_END", "DISCOURSE_TRANSITION", "ENTITY_SWITCH",
            "RESULT_COMMIT", "FINAL_INTEGRATION", "OTHER",
        ],
        "evidence_relation": [
            "SAME_TARGET_EVIDENCE", "NEW_VISUAL_ENTITY", "NEW_VISUAL_FACT",
            "COMBINATION_OF_PRIOR_FACTS", "NO_EXPLICIT_VISUAL_REFERENCE",
        ],
        "temporal_location": ["EARLY", "MIDDLE", "LATE"],
        "lexical_type": [
            "VISUAL_ENTITY", "INTERROGATIVE", "RELATION_OPERATOR", "MATH_OPERATOR",
            "NUMERIC_LITERAL", "FUNCTION_WORD", "DISCOURSE_MARKER", "PUNCTUATION",
            "SPECIAL_TOKEN", "OTHER_CONTENT",
        ],
        "reasoning_role": [
            "TARGET_ENTITY_MENTION", "INTERMEDIATE_RESULT", "SUBGOAL_OPERATOR",
            "DISCOURSE_TRANSITION", "BOUNDARY", "RESULT_COMMIT", "OTHER",
        ],
        "span_length_tokenizer_positions": [1, 8],
        "selection_basis": "semantic text and reasoning structure only",
        "attention_used": False,
    }
    cohort_rules = {
        "target_primary_unique_bases": 48,
        "minimum_primary_unique_bases": 40,
        "validation_unique_bases": 8,
        "initial_trajectory_budget": INITIAL_BUDGET,
        "maximum_trajectory_budget": TOTAL_BUDGET,
        "primary_statistical_unit": "base_problem_id",
        "first_eligible_trajectory_per_base": True,
        "frozen_event_subset_per_fact": "exactly three events: first, midpoint-nearest, and last by annotation order",
        "inclusion": [
            "correct completed Qwen3-VL-4B-Thinking trajectory",
            "at least 160 generated reasoning tokens before final discriminative evidence-use coordinate",
            "at least 3 independently annotated reasoning/subgoal segments",
            "at least 3 candidate evidence-use/integration events",
            "at least 2 candidate events separated by at least 24 reasoning tokens",
            "every local-use readout is 1 to 32 tokenizer positions after its checkpoint-span end",
            "valid localized target visual evidence and ROI T",
            "valid O/O_sham/C/C_sham semantic quartet",
            "exact prompt/image token layout across semantic conditions",
            "at least one event before final 25 percent of reasoning",
            "no attention-based inclusion",
        ],
        "screen_order": "static numeric-edit feasibility, descending Vision-Dominant question word count, source, base ID; all Vision Dominant before Vision Intensive retries",
        "selection_used_attention": False,
        "selection_used_prior_generation_outcome": False,
        "selection_used_carrier_outcome": False,
    }
    source_windows = {
        "W8": {"relative_query_positions": [-8, -1], "layers": list(range(36)), "logical_heads": list(range(32)), "source": "target ROI T"},
        "W16": {"relative_query_positions": [-16, -1], "layers": list(range(36)), "logical_heads": list(range(32)), "source": "target ROI T"},
        "window_choice_is_not_effect_selected": True,
    }
    route_rules = {
        "gate_minimum_bases_with_two_confirmed_separated_checkpoints": 16,
        "pair_selection": "first eligible pair per base by frozen annotation order",
        "separation_minimum_reasoning_tokens": 24,
        "direct": "target ROI suppression over W8 immediately before checkpoint B",
        "prior_checkpoint": "replace checkpoint A K+V span with matching W8-source-deficient cache",
        "short_history": "replace checkpoint A through next 8 reasoning-token cache positions",
        "joint": "direct W8 plus short prior-history replacement",
        "visual_cache_donor_patch": False,
        "attention_used": False,
    }
    primary_family = {
        "local_use_primary": True,
        "final_use_secondary": True,
        "condition_aggregation": "score O and C separately, sign-align, then average within event and base",
        "event_source_sensitive": {
            "minimum_mean_loss_nats_per_candidate_token": 0.05,
            "require_nonnegative_each_semantic_direction": True,
            "require_mean_loss_exceed_matched_sham_absolute_effect": True,
            "either_W8_or_W16_may_qualify_but_both_are_reported": True,
        },
        "event_functional_checkpoint_C2": {
            "requires_source_sensitive_same_window": True,
            "minimum_mean_rescue_gain_nats_per_candidate_token": 0.05,
            "minimum_median_unclipped_rescue_ratio": 0.25,
            "require_positive_each_semantic_direction": True,
            "require_event_span_gain_exceed_predeclared_neighbor_gain": True,
        },
        "persistent_checkpoint_C3": "C2 plus positive meaningful rescue at a 65+ token or final E_d readout",
        "repeated_checkpoint": "at least two nonoverlapping C2/C3 checkpoints separated by at least 24 reasoning tokens",
        "dataset_robust_positive": {
            "wilcoxon_two_sided_holm_p_lt": 0.05,
            "bootstrap_mean_ci95_lower_gt": 0.0,
            "positive_base_fraction_gte": 0.75,
        },
        "rescue_ratios": "unclipped_descriptive_not_unique_fraction",
    }
    config = {
        "frozen_at": frozen_at,
        "source_plan": str(PLAN.relative_to(ROOT)),
        "source_plan_sha256": sha256(PLAN),
        "implementation_plan": str(IMPLEMENTATION_PLAN.relative_to(ROOT)),
        "implementation_plan_sha256": sha256(IMPLEMENTATION_PLAN),
        "model": stage3c8["model"],
        "model_checkpoint": stage3c8["model_checkpoint"],
        "dataset_root": str(dataset_root),
        "locked_generation_protocol": stage3c8["locked_generation_protocol"],
        "runtime": {
            "gpu_class": "A6000",
            "attention_implementation": "eager",
            "seed": SEED,
            "allocated_gpus": 4,
            "slurm_allocation": "108085",
            "tmux_session": "9",
            "canonical_scoring": {
                "path": "P2_fixed_streaming_cached",
                "chunk_size": 2048,
                "release_allocator_cache_between_chunks": True,
                "per_example_chunk_switching": False,
                "calibration_acceptance": "outputs/a6000_calibration_v2/summaries/a6000_calibration_v2_acceptance.json",
                "same_path_tolerance": 1e-6,
            },
            "clean_restart": {
                "trajectory_start": 0,
                "a5000_outcomes_reused": False,
                "a5000_provenance_root": "outputs/stage3c9_a5000_provenance",
            },
        },
        "architecture": stage3c8["architecture"],
        "screening": {"initial_budget": INITIAL_BUDGET, "maximum_budget": TOTAL_BUDGET, "shards": SHARDS},
        "prohibited_follow_on": ["sink_causality", "residual_feature_learning", "unconstrained_history_search", "stage4", "multi_evidence_refresh", "failure_analysis"],
    }

    write_json(OUT / "config/stage3c9_config.json", config)
    write_json(OUT / "config/cohort_rules.json", cohort_rules)
    write_json(OUT / "config/event_taxonomy.json", taxonomy)
    write_json(OUT / "config/source_windows.json", source_windows)
    write_json(OUT / "config/route_rules.json", route_rules)
    write_json(OUT / "config/primary_family.json", primary_family)
    write_jsonl(OUT / "cohort/prospective_screen_manifest.jsonl", screen)
    initial = screen[:INITIAL_BUDGET]
    reserve = screen[INITIAL_BUDGET:]
    for shard in range(SHARDS):
        write_jsonl(OUT / f"cohort/initial_generation_shard_{shard:02d}.jsonl", [row for row in initial if row["screen_order"] % SHARDS == shard])
    write_jsonl(OUT / "cohort/reserve_generation_manifest.jsonl", reserve)
    write_json(OUT / "cohort/screening_accounting.json", {
        "frozen_at": frozen_at,
        "attempted": 0,
        "completed": 0,
        "correct": 0,
        "long_enough": 0,
        "multi_segment": 0,
        "multi_event": 0,
        "edit_valid": 0,
        "ROI_valid": 0,
        "retained": 0,
        "initial_budget": INITIAL_BUDGET,
        "maximum_budget": TOTAL_BUDGET,
        "status": "initial_generation_pending",
    })
    print(json.dumps({
        "screen": len(screen),
        "initial": len(initial),
        "reserve": len(reserve),
        "initial_unique_bases": len({row["base_problem_id"] for row in initial}),
        "initial_static_numeric_candidates": sum(row["static_numeric_candidate_count"] > 0 for row in initial),
        "initial_sources": dict(Counter(row["source"] for row in initial)),
        "shard_sizes": [sum(row["screen_order"] % SHARDS == shard for row in initial) for shard in range(SHARDS)],
    }, indent=2))


if __name__ == "__main__":
    main()
