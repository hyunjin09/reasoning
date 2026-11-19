#!/usr/bin/env python3
"""Draft the gated, outcome-independent Stage 3C.8 long-horizon landmarks."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"
RELATIVE_OFFSETS = (128, 64, 32, 16, 8, 4, 2, 1)
BOUNDARY_ROLES = {"CLAUSE_FINAL", "SENTENCE_FINAL", "SPAN_FINAL"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def first(rows: list[dict[str, Any]], predicate) -> dict[str, Any] | None:
    return next((row for row in rows if predicate(row)), None)


def long_roles(row: dict[str, Any], *, previous_boundary: bool) -> list[str]:
    roles = []
    if previous_boundary:
        roles.append("SUBGOAL_START")
    if row["structural_role"] in BOUNDARY_ROLES:
        roles.extend(("SUBGOAL_END", "BOUNDARY"))
    if row["visual_alignment"] in {"TARGET_ALIGNED", "MENTION_ALIGNED"}:
        roles.append("EVIDENCE_REFERENCE")
    if row["reasoning_role"] == "INTERMEDIATE_RESULT":
        roles.extend(("INTERMEDIATE_CONCLUSION", "RESULT_COMMIT"))
    if row["reasoning_role"] == "DISCOURSE_TRANSITION":
        roles.append("DISCOURSE_TRANSITION")
    return roles or ["NONE"]


def main() -> None:
    gate = read_json(OUT / "phase_d_anchor/gate.json")
    draft_manifest = OUT / "phase_d_anchor/long_horizon_manifest_draft.jsonl"
    draft_landmarks = OUT / "phase_d_anchor/landmark_annotations_draft.jsonl"
    cohort_gate_path = OUT / "phase_d_anchor/cohort_gate.json"
    if draft_manifest.exists() or draft_landmarks.exists():
        raise FileExistsError("Phase-D landmark draft already exists")
    if not gate["run"]:
        write_jsonl(draft_manifest, [])
        write_jsonl(draft_landmarks, [])
        write_json(cohort_gate_path, {"run": False, "reason": "phase_a_b_carrier_gate_failed", "eligible": 0})
        return

    fresh = read_jsonl(OUT / "cohort/fresh_atlas_manifest.jsonl")
    annotations = read_jsonl(OUT / "annotations/per_token_annotations.jsonl")
    by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in annotations:
        if row["stream"] == "PREVIOUS_REASONING" and row["coordinate"] == "a_like":
            by_base[str(row["base_problem_id"])].append(row)
    eligible = []
    for item in fresh:
        base = str(item["base_problem_id"])
        ed = int(item["event"]["ed_generated_index"])
        rows = sorted(by_base[base], key=lambda row: int(row["generated_index"]))
        boundaries = [row for row in rows if row["structural_role"] in BOUNDARY_ROLES]
        if ed >= 128 and len(boundaries) >= 2:
            eligible.append((ed, int(item["screen_order"]), item, rows))
    eligible.sort(key=lambda value: (-value[0], value[1]))
    selected = eligible[:32]
    if len(selected) < 28:
        write_jsonl(draft_manifest, [])
        write_jsonl(draft_landmarks, [])
        write_json(cohort_gate_path, {
            "run": False,
            "reason": "fewer_than_28_fresh_bases_with_128_pre_Ed_tokens_and_two_segments",
            "phase_a_b_gate_passed": True,
            "eligible": len(selected),
            "target": 32,
            "minimum": 28,
            "selection_used_attention": False,
            "selection_used_phase_a_b_effects": False,
        })
        return

    frozen_at = datetime.now(timezone.utc).isoformat()
    manifests, landmarks = [], []
    for ed, _, item, rows in selected:
        base = str(item["base_problem_id"])
        prior_rows = [row for row in rows if 5 <= int(row["generated_index"]) < ed]
        positions: dict[int, set[str]] = defaultdict(set)
        for offset in RELATIVE_OFFSETS:
            position = ed - offset
            if position >= 5:
                positions[position].add(f"relative:E_d-{offset}")
        boundaries = [row for row in prior_rows if row["structural_role"] in BOUNDARY_ROLES]
        structural = (
            ("structure:first_subgoal_boundary", first(prior_rows, lambda row: row["structural_role"] in BOUNDARY_ROLES)),
            ("structure:first_target_entity_mention", first(prior_rows, lambda row: row["visual_alignment"] == "TARGET_ALIGNED")),
            ("structure:first_explicit_target_fact_mention", first(prior_rows, lambda row: row["visual_alignment"] in {"TARGET_ALIGNED", "MENTION_ALIGNED"})),
            ("structure:first_intermediate_result", first(prior_rows, lambda row: row["reasoning_role"] == "INTERMEDIATE_RESULT")),
            ("structure:last_subgoal_boundary_before_Ed", boundaries[-1] if boundaries else None),
        )
        target_reference = first(prior_rows, lambda row: row["visual_alignment"] in {"TARGET_ALIGNED", "MENTION_ALIGNED"})
        target_index = int(target_reference["generated_index"]) if target_reference else -1
        discourse_after = first(
            prior_rows,
            lambda row: int(row["generated_index"]) > target_index and row["reasoning_role"] == "DISCOURSE_TRANSITION",
        ) if target_index >= 0 else None
        structural += (("structure:first_discourse_transition_after_target_reference", discourse_after),)
        for label, row in structural:
            if row is not None:
                positions[int(row["generated_index"])].add(label)
        lookup = {int(row["generated_index"]): row for row in prior_rows}
        for position in sorted(positions):
            row = lookup[position]
            previous = lookup.get(position - 1)
            landmarks.append({
                "base_problem_id": base,
                "example_id": str(item["example_id"]),
                "ed_generated_index": ed,
                "landmark_generated_index": position,
                "landmark_types": sorted(positions[position]),
                "normalized_reasoning_position": position / ed,
                "token_id": int(row["token_id"]),
                "token_text": row["decoded_text"],
                "lexical_semantic_class": row["lexical_semantic_class"],
                "visual_alignment": row["visual_alignment"],
                "structural_role": row["structural_role"],
                "reasoning_role": row["reasoning_role"],
                "long_horizon_roles": long_roles(
                    row,
                    previous_boundary=bool(previous and previous["structural_role"] in BOUNDARY_ROLES),
                ),
                "local_suppression_generated_indices": list(range(position - 4, position)),
                "manual_review_status": "pending",
                "selection_used_attention": False,
                "selection_used_phase_a_b_effects": False,
                "phase_d_scores_available_at_draft": False,
            })
        manifests.append({
            **item,
            "phase_d_cohort_role": "fresh_long_horizon",
            "reasoning_tokens_before_ed": ed,
            "landmark_count": len(positions),
            "landmark_selection": "fixed relative offsets plus frozen semantic/structural first/last rules",
            "selection_used_attention": False,
            "selection_used_phase_a_b_effects": False,
            "phase_d_scores_available_at_draft": False,
            "drafted_at": frozen_at,
        })
    write_jsonl(draft_manifest, manifests)
    write_jsonl(draft_landmarks, landmarks)
    write_json(cohort_gate_path, {
        "run": True,
        "phase_a_b_gate_passed": True,
        "eligible": len(eligible),
        "retained": len(manifests),
        "target": 32,
        "minimum": 28,
        "selection_used_attention": False,
        "selection_used_phase_a_b_effects": False,
        "manual_review_status": "pending",
    })
    print(json.dumps({"eligible": len(eligible), "retained": len(manifests), "landmarks": len(landmarks)}, indent=2))


if __name__ == "__main__":
    main()
