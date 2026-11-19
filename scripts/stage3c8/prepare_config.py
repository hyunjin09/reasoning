#!/usr/bin/env python3
"""Freeze Stage 3C.8 configs, cohorts, and prospective generation shards."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3c8.protocol import select_fresh_screen


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"
DATASET = Path("/data/dataset/MathVerse")
PLAN = ROOT / "plan/stage3c8_plan.md"
SCREEN_BUDGET = 240
SEED = 1_234


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def conservative_exclusions() -> tuple[set[str], list[dict[str, Any]]]:
    sources = [
        ROOT / "outputs/stage1/discovery/preparation/cohort_attempt_manifest.jsonl",
        ROOT / "outputs/stage3a/cohort/candidate_screening.jsonl",
        ROOT / "outputs/stage3b9/prospective_generation/raw_outcome_manifest.jsonl",
        ROOT / "outputs/stage3c7/cohort/validation_manifest.jsonl",
        ROOT / "outputs/stage3c7/cohort/primary_manifest.jsonl",
    ]
    excluded: set[str] = set()
    evidence = []
    for path in sources:
        rows = read_jsonl(path)
        ids = {str(row["base_problem_id"]) for row in rows}
        excluded.update(ids)
        evidence.append({"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "unique_bases": len(ids)})
    return excluded, evidence


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError("Stage 3C.8 config freeze is create-once; outputs/stage3c8 is already non-empty")
    for name in (
        "config", "cohort", "annotations", "audit", "prospective_generation/raw",
        "phase_a_tpre", "phase_b_recent", "phase_c_prompt", "phase_d_anchor",
        "analysis/figures", "summaries",
    ):
        ensure_directory(OUT / name)

    frozen_at = datetime.now(timezone.utc).isoformat()
    stage3c7 = read_json(ROOT / "outputs/stage3c7/config/stage3c7_config.json")
    excluded, exclusion_evidence = conservative_exclusions()
    dataset_rows = load_mathverse_rows(DATASET)
    screen = select_fresh_screen(dataset_rows, excluded_base_ids=excluded, budget=SCREEN_BUDGET)
    for row in screen:
        source = resolve_image_path(DATASET, row["image_id"])
        if not source.is_file():
            raise FileNotFoundError(source)
        row["source_image"] = str(source)
        row["source_image_sha256"] = sha256(source)
        row["frozen_at"] = frozen_at

    validation = read_jsonl(ROOT / "outputs/stage3c7/cohort/validation_manifest.jsonl")
    extra = next(row for row in read_jsonl(ROOT / "outputs/stage3a/cohort/primary_manifest.jsonl") if str(row["base_problem_id"]) == "3")
    validation = [{**row, "cohort_role": "mechanical_validation", "stage3c8_reused_without_reselection": True} for row in [*validation, extra]]
    historical = [
        {**row, "cohort_role": "historical_anchor", "stage3c8_reused_without_reselection": True}
        for row in read_jsonl(ROOT / "outputs/stage3c7/cohort/primary_manifest.jsonl")
    ]
    validation_ids = {str(row["base_problem_id"]) for row in validation}
    historical_ids = {str(row["base_problem_id"]) for row in historical}
    fresh_ids = {str(row["base_problem_id"]) for row in screen}
    if validation_ids & historical_ids or validation_ids & fresh_ids or historical_ids & fresh_ids:
        raise RuntimeError("Stage 3C.8 cohort sets are not disjoint")

    write_jsonl(OUT / "cohort/validation_manifest.jsonl", validation)
    write_jsonl(OUT / "cohort/historical_anchor_manifest.jsonl", historical)
    write_jsonl(OUT / "cohort/prospective_screen_manifest.jsonl", screen)
    write_jsonl(OUT / "cohort/fresh_atlas_manifest.jsonl", [])
    write_jsonl(OUT / "cohort/exclusions.jsonl", [])
    for shard_index in range(2):
        write_jsonl(OUT / f"cohort/generation_shard_{shard_index:02d}.jsonl", screen[shard_index::2])

    taxonomy = {
        "frozen_at": frozen_at,
        "stream": ["PROMPT_QUESTION", "SPECIAL_CONTROL", "PREVIOUS_REASONING"],
        "lexical_semantic_class": [
            "VISUAL_ENTITY", "INTERROGATIVE", "RELATION_OPERATOR", "MATH_OPERATOR",
            "NUMERIC_LITERAL", "FUNCTION_WORD", "DISCOURSE_MARKER", "PUNCTUATION",
            "SPECIAL_TOKEN", "OTHER_CONTENT",
        ],
        "visual_alignment": ["TARGET_ALIGNED", "MENTION_ALIGNED", "OTHER_VISUAL_ENTITY", "NO_DIRECT_VISUAL_ALIGNMENT"],
        "structural_role": ["QUESTION_INITIAL", "QUESTION_FINAL", "CLAUSE_FINAL", "SENTENCE_FINAL", "SPAN_FINAL", "NONE"],
        "reasoning_role": [
            "TARGET_ENTITY_MENTION", "NON_TARGET_ENTITY_MENTION", "INTERMEDIATE_RESULT",
            "SUBGOAL_OPERATOR", "DISCOURSE_TRANSITION", "BOUNDARY", "OTHER",
        ],
        "annotation_used_attention": False,
        "causal_outcomes_available_at_freeze": False,
    }
    span_rules = {
        "frozen_at": frozen_at,
        "grouping": "contiguous tokenizer pieces forming one whitespace-delimited lexical unit; punctuation is a separate span",
        "position_interval": "inclusive start, exclusive end",
        "split_token_analysis": "jointly patch every constituent cache position; report separately from position-level rescue",
        "structural_boundary": "assigned from decoded punctuation and frozen sentence/clause delimiters",
        "visual_entity_source": "manual image/entity annotation, never attention",
    }
    family = {
        "frozen_at": frozen_at,
        "primary_unit": "base_problem_id",
        "minimum_class_observations": 12,
        "robust_positive": {"holm_p_lt": 0.05, "bootstrap_mean_ci_lower_gt": 0.0, "positive_fraction_gte": 0.75},
        "phase_a": {"layers": list(range(16, 36)), "modes": ["K", "V", "KV"], "coordinates": ["a_like", "b_like"]},
        "phase_b": {"window": list(range(-16, 1)), "all_layers": list(range(36)), "fixed_kv_distances": [1, 2, 4, 8, 16]},
        "phase_c": {"cutoff": "all generated queries to all visual prompt positions", "primary_mode": "KV", "bidirectional": True},
        "phase_d_gate": "Phase-A robust any coordinate OR Phase-B median all-recent RR>=0.50 plus robust local/group effect",
        "phase_d_route_gate": "N>=12 within a predeclared landmark category and robust future-use rescue",
        "attention_role": "unused for selection, annotation, intervention, ranking, or gating",
    }
    cohort_plan = {
        "frozen_at": frozen_at,
        "validation": {"target": 8, "ids": sorted(validation_ids, key=int)},
        "historical_anchor": {"count": 24, "ids": [str(row["base_problem_id"]) for row in historical]},
        "fresh": {"target": 64, "minimum": 56, "screening_budget": SCREEN_BUDGET, "selection_order": "GeoQA, GEOS, Geometry3K; ascending base within source"},
        "prospective_screen_ids": [row["base_problem_id"] for row in screen],
        "conservative_exclusion_count": len(excluded),
        "conservative_exclusion_evidence": exclusion_evidence,
        "selection_used_attention": False,
        "selection_used_generation_outcome": False,
        "selection_used_carrier_outcome": False,
    }
    config = {
        "frozen_at": frozen_at,
        "source_plan": str(PLAN.relative_to(ROOT)),
        "source_plan_sha256": sha256(PLAN),
        "implementation_plan": "workspace/stage3c8_implementation_plan.md",
        "implementation_plan_sha256": sha256(ROOT / "workspace/stage3c8_implementation_plan.md"),
        "model": stage3c7["model"],
        "model_checkpoint": stage3c7["model_checkpoint"],
        "dataset_root": str(DATASET),
        "locked_generation_protocol": {"name": "official", "do_sample": True, "temperature": 0.6, "top_p": 0.95, "top_k": 20, "presence_penalty": 0.0, "max_new_tokens": 40960, "seed": SEED},
        "runtime": {"gpu_class": "A5000", "attention_implementation": "eager", "seed": SEED},
        "architecture": stage3c7["architecture_expected"],
        "config_files": {
            "cohort_plan": "outputs/stage3c8/config/cohort_plan.json",
            "token_taxonomy": "outputs/stage3c8/config/token_taxonomy.json",
            "span_rules": "outputs/stage3c8/config/span_rules.json",
            "primary_family": "outputs/stage3c8/config/primary_family.json",
        },
        "prohibited_follow_on": ["sink_intervention", "unconstrained_history_search", "residual_feature_learning", "stage4", "multi_evidence_refresh", "failure_analysis"],
    }
    write_json(OUT / "config/cohort_plan.json", cohort_plan)
    write_json(OUT / "config/token_taxonomy.json", taxonomy)
    write_json(OUT / "config/span_rules.json", span_rules)
    write_json(OUT / "config/primary_family.json", family)
    write_json(OUT / "config/stage3c8_config.json", config)
    write_json(OUT / "cohort/sample_accounting.json", {
        "frozen_at": frozen_at, "screened": SCREEN_BUDGET, "edit_valid": 0,
        "completed_correct": 0, "strict_E_d_valid": 0, "ROI_valid": 0,
        "prompt_token_annotation_valid": 0, "recent_window_valid": 0, "retained": 0,
        "status": "baseline_generation_pending",
    })
    print(json.dumps({"validation": len(validation), "historical": len(historical), "screen": len(screen), "screen_source_counts": {source: sum(row["source"] == source for row in screen) for source in ("GeoQA", "GEOS", "Geometry3K")}}, indent=2))


if __name__ == "__main__":
    main()
