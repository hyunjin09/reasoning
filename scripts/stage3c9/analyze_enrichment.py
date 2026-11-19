#!/usr/bin/env python3
"""Run post-causal checkpoint type/role enrichment with structure controls."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3c8.analysis import inferential_summary
from visual_reasoning.stage3c8.annotations import annotate_token_sequence
from visual_reasoning.stage3c9.analysis import enrichment_match_key


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def lexical_type(rows: list[dict[str, Any]]) -> str:
    observed = {str(row["lexical_semantic_class"]) for row in rows}
    priority = (
        "VISUAL_ENTITY", "NUMERIC_LITERAL", "RELATION_OPERATOR", "MATH_OPERATOR",
        "DISCOURSE_MARKER", "PUNCTUATION", "FUNCTION_WORD", "SPECIAL_TOKEN", "OTHER_CONTENT",
    )
    return next((name for name in priority if name in observed), "OTHER_CONTENT")


def reasoning_role(event_role: str, lexical: str) -> str:
    role = str(event_role)
    if role in {"TARGET_ENTITY_REFERENCE", "VISUAL_FACT_REFERENCE", "ENTITY_SWITCH"}:
        return "TARGET_ENTITY_MENTION"
    if role == "INTERMEDIATE_RESULT":
        return "INTERMEDIATE_RESULT"
    if role in {"SUBGOAL_START", "SUBGOAL_END"}:
        return "SUBGOAL_OPERATOR"
    if role == "DISCOURSE_TRANSITION":
        return "DISCOURSE_TRANSITION"
    if role in {"RESULT_COMMIT", "FINAL_INTEGRATION"}:
        return "RESULT_COMMIT"
    if lexical == "PUNCTUATION":
        return "BOUNDARY"
    return "OTHER"


def main() -> None:
    manifest = read_jsonl(OUT / "cohort/primary_manifest.jsonl")
    classes = {
        str(row["base_problem_id"]): row
        for row in read_json(OUT / "phase_b_checkpoint/checkpoint_classification.json")["bases"]
    }
    event_rows = []
    for item in manifest:
        base = str(item["base_problem_id"])
        tokens = read_jsonl(ROOT / item["tokens_path"])
        final_index = int(item["final_use_readout"]["token_index"])
        class_events = {int(row["event_id"]): row for row in classes[base]["events"]}
        target_terms = set(re.findall(r"[A-Za-z]+", str(item["target_evidence"]).lower()))
        for event in item["events"]:
            start, end = int(event["span_start_token"]), int(event["span_end_token"])
            ids = [int(row["token_id"]) for row in tokens[start:end]]
            texts = [str(row["decoded_token"]) for row in tokens[start:end]]
            annotated, _ = annotate_token_sequence(
                token_ids=ids,
                token_texts=texts,
                stream="PREVIOUS_REASONING",
                visual_entities=target_terms,
                target_entities=target_terms,
                absolute_offset=start,
            )
            primary_type = lexical_type(annotated)
            role = reasoning_role(str(event["event_role"]), primary_type)
            local_start, local_end = max(0, start - 8), min(len(tokens), end + 8)
            local_text = "".join(str(row["decoded_token"]) for row in tokens[local_start:local_end])
            density = len(re.findall(r"[A-Za-z0-9]+", local_text)) / max(local_end - local_start, 1)
            classification = class_events[int(event["event_id"])]["classification"]
            event_rows.append({
                "base_problem_id": base,
                "event_id": int(event["event_id"]),
                "classification": classification,
                "is_checkpoint": classification in {"C2", "C3"},
                "lexical_type": primary_type,
                "reasoning_role": role,
                "constituent_lexical_types": [row["lexical_semantic_class"] for row in annotated],
                "distance_to_local_use_readout": int(event["local_use_readout"]["token_index"]) - end,
                "normalized_reasoning_progress": start / max(final_index, 1),
                "span_length": end - start,
                "local_token_density": density,
                "boundary_position": bool(texts and re.fullmatch(r"[^\w\s]+", texts[-1].strip())),
                "annotation_used_attention": False,
            })
    by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in event_rows:
        by_base[row["base_problem_id"]].append(row)
    controls = []
    for base, rows in by_base.items():
        focal = [row for row in rows if row["is_checkpoint"]]
        candidates = [row for row in rows if not row["is_checkpoint"]]
        for row in focal:
            if not candidates:
                continue
            control = min(candidates, key=lambda item: enrichment_match_key(row, item))
            controls.append({
                "base_problem_id": base,
                "checkpoint_event_id": int(row["event_id"]),
                "control_event_id": int(control["event_id"]),
                "checkpoint_lexical_type": row["lexical_type"],
                "control_lexical_type": control["lexical_type"],
                "checkpoint_reasoning_role": row["reasoning_role"],
                "control_reasoning_role": control["reasoning_role"],
                "progress_difference": float(row["normalized_reasoning_progress"] - control["normalized_reasoning_progress"]),
                "span_length_difference": int(row["span_length"] - control["span_length"]),
                "density_difference": float(row["local_token_density"] - control["local_token_density"]),
                "boundary_match": bool(row["boundary_position"] == control["boundary_position"]),
                "readout_distance_difference": int(row["distance_to_local_use_readout"] - control["distance_to_local_use_readout"]),
                "selection_used_attention": False,
            })
    lexical_labels = sorted({row["lexical_type"] for row in event_rows})
    role_labels = sorted({row["reasoning_role"] for row in event_rows})
    lexical_stats, role_stats = {}, {}
    for label in lexical_labels:
        values: dict[str, list[float]] = defaultdict(list)
        for row in event_rows:
            values[row["base_problem_id"]].append(float(row["is_checkpoint"] and row["lexical_type"] == label))
        lexical_stats[label] = inferential_summary({base: float(np.mean(items)) for base, items in values.items()})
    for label in role_labels:
        values = defaultdict(list)
        for row in event_rows:
            values[row["base_problem_id"]].append(float(row["is_checkpoint"] and row["reasoning_role"] == label))
        role_stats[label] = inferential_summary({base: float(np.mean(items)) for base, items in values.items()})
    matched_lexical, matched_roles = {}, {}
    for label in lexical_labels:
        values = defaultdict(list)
        for row in controls:
            values[row["base_problem_id"]].append(
                float(row["checkpoint_lexical_type"] == label)
                - float(row["control_lexical_type"] == label)
            )
        matched_lexical[label] = inferential_summary({base: float(np.mean(items)) for base, items in values.items()})
    for label in role_labels:
        values = defaultdict(list)
        for row in controls:
            values[row["base_problem_id"]].append(
                float(row["checkpoint_reasoning_role"] == label)
                - float(row["control_reasoning_role"] == label)
            )
        matched_roles[label] = inferential_summary({base: float(np.mean(items)) for base, items in values.items()})
    write_jsonl(OUT / "phase_e_enrichment/matched_enrichment_controls.jsonl", controls)
    write_json(OUT / "phase_e_enrichment/checkpoint_type_enrichment.json", {
        "event_rows": event_rows,
        "raw_checkpoint_type_counts": dict(Counter(row["lexical_type"] for row in event_rows if row["is_checkpoint"])),
        "raw_noncheckpoint_type_counts": dict(Counter(row["lexical_type"] for row in event_rows if not row["is_checkpoint"])),
        "base_level_descriptive_summaries": lexical_stats,
        "matched_control_inference": matched_lexical,
        "matched_effect_definition": "within-pair checkpoint label indicator minus matched non-checkpoint label indicator, averaged within base",
        "matched_control_count": len(controls),
        "raw_counts_are_not_enrichment_claims": True,
    })
    write_json(OUT / "phase_e_enrichment/reasoning_role_enrichment.json", {
        "raw_checkpoint_role_counts": dict(Counter(row["reasoning_role"] for row in event_rows if row["is_checkpoint"])),
        "raw_noncheckpoint_role_counts": dict(Counter(row["reasoning_role"] for row in event_rows if not row["is_checkpoint"])),
        "base_level_descriptive_summaries": role_stats,
        "matched_control_inference": matched_roles,
        "matched_effect_definition": "within-pair checkpoint role indicator minus matched non-checkpoint role indicator, averaged within base",
        "matched_control_count": len(controls),
        "raw_counts_are_not_enrichment_claims": True,
    })
    print(json.dumps({"events": len(event_rows), "checkpoints": sum(row["is_checkpoint"] for row in event_rows), "matched_controls": len(controls)}, indent=2))


if __name__ == "__main__":
    main()
