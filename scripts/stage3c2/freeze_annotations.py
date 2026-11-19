#!/usr/bin/env python3
"""Freeze the attention-blind Stage 3C.2 dissociation cohort and annotations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c2"
A_OFFSETS = (-16, -8, -4, -2, -1, 0)
B_OFFSETS = (-16, -8, -4, -2, -1, 0)

# These mappings were manually traced on the token-grid overlays in
# outputs/stage3c2/annotations/grid_guides before Stage 3C.2 attention extraction.
# M is a visibly distinct entity that is explicitly active in the reasoning context.
MENTION_ROIS: dict[str, dict] = {
    "119": {"entity": "sector cardboard body", "local": [23, 24, 25, 35, 36, 37, 46, 47, 56, 57]},
    "140": {"entity": "ground segment NM", "local": [1, 12, 23, 34, 44, 45]},
    "155": {"entity": "flagpole AC", "local": [19, 20, 30, 41, 52, 63, 74]},
    "753": {"entity": "cylinder radius label 3", "local": [2, 3, 17, 18, 19]},
    "141": {"entity": "building", "local": [19, 20, 30, 31, 41, 42, 52, 53]},
    "147": {"entity": "ground line through E-F-B-C", "local": [50, 51, 52, 53, 54, 55, 56, 57, 58]},
    "751": {"entity": "circular base of the tube", "local": [16, 17, 32, 47, 62, 77]},
    "2": {"entity": "queried angle 2", "local": [49, 50, 51]},
    "9": {"entity": "equal sides AC and BC", "local": [17, 18, 29, 30, 40, 41, 42, 52, 53, 54, 64, 65, 74, 75, 81, 82]},
    "16": {"entity": "queried angle OAB", "local": [36, 37, 38, 45, 46]},
    "22": {"entity": "rhombus boundary BC", "local": [4, 5, 6, 7, 8, 9, 10, 15, 16, 17, 18, 19, 20, 21]},
    "24": {"entity": "queried angle 2", "local": [46, 47, 55, 56, 57]},
    "31": {"entity": "segment BC", "local": [18, 29, 40, 50]},
    "38": {"entity": "queried angle BAC", "local": [10, 11, 18, 19, 26, 27]},
    "60": {"entity": "queried angle 1", "local": [16, 25, 26]},
    "67": {"entity": "queried angle AEC", "local": [35, 36, 45, 46, 55, 56]},
    "69": {"entity": "parallel line b", "local": [40, 41, 42, 43, 44, 45, 46]},
    "74": {"entity": "segment FC", "local": [8, 19, 29, 30, 40, 51]},
    "75": {"entity": "parallel line b", "local": [40, 41, 42, 43, 44, 45, 46, 47, 48]},
    "76": {"entity": "right-angle marker at B", "local": [43, 44, 53, 54]},
    "78": {"entity": "queried angle AED at E", "local": [49, 50, 59, 60]},
    "80": {"entity": "circular base of the cylinder", "local": [3, 4, 5, 11, 12, 13, 14, 15]},
    "98": {"entity": "queried angle OBC", "local": [45, 46, 54, 55]},
    "100": {"entity": "segment CE", "local": [48, 49, 55, 56]},
    "103": {"entity": "queried angle AOC", "local": [30, 31, 39, 40, 41]},
    "106": {"entity": "right half OB of diameter AB", "local": [40, 41, 42, 43]},
    "107": {"entity": "queried angle ACD at C", "local": [3, 4, 12, 13, 21, 22]},
    "109": {"entity": "queried angle beta", "local": [34, 35, 43, 44]},
    "113": {"entity": "arc DA", "local": [3, 11, 12, 19, 27, 36, 45, 54, 55, 64, 65]},
    "120": {"entity": "bottom circular base of the cone", "local": [42, 43, 44, 45, 46, 52, 53, 54, 55, 56]},
    "128": {"entity": "segments OA and OB and their 6 cm label", "local": [4, 5, 12, 13, 14]},
}

# Earliest offset from E_d where the current clause explicitly identifies T.
# None means retrieval demand is present but the frozen lead remains generic.
TARGET_EXPLICIT_START = {
    "119": -2, "140": -4, "155": -4, "753": None, "141": -4,
    "147": -4, "751": -4, "2": -2, "9": -4, "16": -2,
    "22": -2, "24": -2, "31": -2, "38": -4, "60": -2,
    "67": -2, "69": -2, "74": -2, "75": -2, "76": -2,
    "78": -2, "80": -2, "98": -4, "100": -4, "103": -2,
    "106": -4, "107": -4, "109": -4, "113": -2, "120": -2,
    "128": -4,
}

EXCLUSIONS = {
    "3": "29x36 visual grid made a compact, reliable distinct mention ROI impractical for manual token mapping",
    "72": "the edited perimeter formula and queried triangle are not cleanly separable visual entities",
    "79": "the edited perimeter formula and queried triangle are not cleanly separable visual entities",
    "118": "too little generated history before E_d to establish a distinct active mention entity",
    "125": "the depicted second sector is an ambiguous proxy for the queried bottom circle",
    "154": "dense 19x16 ladder diagram made a compact distinct mention ROI ambiguous",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def semantic_state(base: str, offset_from_ed: int) -> tuple[str, str]:
    explicit = TARGET_EXPLICIT_START[base]
    retrieval_start = -4
    if explicit is not None and offset_from_ed >= explicit:
        return "A3", "the current clause explicitly names the causal target entity and its value is immediately required"
    if offset_from_ed >= retrieval_start:
        return "A2", "the immediate clause is setting up the causal fact retrieval while lexical reference is not yet the target identity"
    return "A1", "the distinct mention entity is explicit in the active reasoning context and the target fact is not yet the immediate subgoal"


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    candidates = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "cohort/candidate_manifest.jsonl")}
    primary = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b6/config/primary_manifest.jsonl")}
    events = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")}
    mappings = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")}
    review = read_jsonl(OUT / "annotations/semantic_checkpoint_review.jsonl")
    review_by_key = {(str(row["base_problem_id"]), row["target_id"], int(row["generated_index"])): row for row in review}

    mention_rows, required_rows, irrelevant_rows = [], [], []
    state_rows, pair_rows, manifest_rows = [], [], []
    for base, mention in MENTION_ROIS.items():
        candidate, item, event, mapping = candidates[base], primary[base], events[base], mappings[base]
        visual_absolute = [int(value) for value in mapping["visual_absolute_positions"]]
        local = sorted({int(value) for value in mention["local"]})
        target_local = sorted(map(int, mapping["target_local_positions"]))
        irrelevant_local = sorted(map(int, mapping["irrelevant_local_positions"]))
        if max(local) >= len(visual_absolute):
            raise ValueError(f"Mention token outside visual grid for {base}")
        if set(local) & set(target_local) or set(local) & set(irrelevant_local):
            raise ValueError(f"M/T/I overlap for {base}")
        mention_absolute = [visual_absolute[index] for index in local]
        target_absolute = [visual_absolute[index] for index in target_local]
        irrelevant_absolute = [visual_absolute[index] for index in irrelevant_local]
        mention_rows.append({
            "base_problem_id": base,
            "example_id": item["example_id"],
            "mention_entity": mention["entity"],
            "mention_local_visual_positions": local,
            "mention_absolute_source_positions": mention_absolute,
            "grid_guide": candidate["guide"].replace("cohort/review_guides", "annotations/grid_guides"),
            "manual_semantic_link_status": "pass",
            "manual_roi_mapping_status": "pass",
            "M_not_equal_T": set(local).isdisjoint(target_local),
            "M_disjoint_I": set(local).isdisjoint(irrelevant_local),
            "annotation_used_attention": False,
            "frozen_at": now,
        })
        required_rows.append({
            "base_problem_id": base,
            "example_id": item["example_id"],
            "target_evidence": item["original_fact"],
            "target_roi_xyxy": item["target_evidence_roi_xyxy"],
            "target_local_visual_positions": target_local,
            "target_absolute_source_positions": target_absolute,
            "causal_definition": "frozen Stage 3A/Stage 3B.7-R counterfactual-edit ROI",
            "mapping_used_attention": False,
            "frozen_at": now,
        })
        irrelevant_rows.append({
            "base_problem_id": base,
            "example_id": item["example_id"],
            "irrelevant_local_visual_positions": irrelevant_local,
            "irrelevant_absolute_source_positions": irrelevant_absolute,
            "token_count": len(irrelevant_local),
            "source": "frozen Stage 3B.7 matched irrelevant ROI",
            "disjoint_from_M_and_T": set(irrelevant_local).isdisjoint(local + target_local),
            "mapping_used_attention": False,
            "frozen_at": now,
        })
        ed = int(event["ed_generated_index"])
        valid_by_target: dict[str, list[dict]] = {"target_a": [], "target_b": []}
        for target_id, center, offsets in (("target_a", ed, A_OFFSETS), ("target_b", ed - 1, B_OFFSETS)):
            for offset in offsets:
                generated_index = center + offset
                if generated_index < 1:
                    continue
                offset_from_ed = generated_index - ed
                state, rationale = semantic_state(base, offset_from_ed)
                review_row = review_by_key[(base, target_id, generated_index)]
                row = {
                    "base_problem_id": base,
                    "example_id": item["example_id"],
                    "target_id": target_id,
                    "offset_from_target": offset,
                    "offset_from_E_d": offset_from_ed,
                    "generated_index": generated_index,
                    "active_token_id": review_row["active_token_id"],
                    "active_token": review_row["active_token"],
                    "text_tail": review_row["text_tail"],
                    "semantic_state": state,
                    "mention_entity_active": state == "A1",
                    "retrieval_demand_present": state in {"A2", "A3"},
                    "target_entity_explicit": state == "A3",
                    "rationale": rationale,
                    "manual_audit_status": "pass",
                    "annotation_used_attention": False,
                    "frozen_at": now,
                }
                state_rows.append(row)
                valid_by_target[target_id].append(row)
        for target_id, rows in valid_by_target.items():
            mention_only = next(row for row in rows if row["semantic_state"] == "A1")
            retrieval = [row for row in rows if row["semantic_state"] in {"A2", "A3"}][-1]
            pair_rows.append({
                "base_problem_id": base,
                "target_id": target_id,
                "mention_only_generated_index": mention_only["generated_index"],
                "mention_only_offset_from_target": mention_only["offset_from_target"],
                "retrieval_generated_index": retrieval["generated_index"],
                "retrieval_offset_from_target": retrieval["offset_from_target"],
                "retrieval_state": retrieval["semantic_state"],
                "lexical_control": "within-problem semantic match; exact lexical identity not required",
                "annotation_used_attention": False,
                "frozen_at": now,
            })
        manifest_rows.append({
            "base_problem_id": base,
            "example_id": item["example_id"],
            "variant": item["variant"],
            "evidence_type": item["edit_tier"],
            "ed_generated_index": ed,
            "conditions": ["O", "O_sham", "C", "C_sham"],
            "mention_entity": mention["entity"],
            "M_not_equal_T": True,
            "at_least_three_temporal_checkpoints": all(len(rows) >= 3 for rows in valid_by_target.values()),
            "causal_target_independently_defined": True,
            "manual_semantic_relation_valid": True,
            "exact_token_roi_mapping": True,
            "selection_used_attention": False,
            "annotation_used_attention": False,
            "primary_independent_unit": "base_problem_id",
            "frozen_at": now,
        })

    if len(manifest_rows) < 24 or len({row["base_problem_id"] for row in manifest_rows}) != len(manifest_rows):
        raise RuntimeError("Primary cohort size/uniqueness gate failed")

    excluded_rows = [{
        "base_problem_id": base,
        "example_id": candidates[base]["example_id"],
        "decision": "exclude",
        "reason": reason,
        "selection_used_attention": False,
        "reviewed_at": now,
    } for base, reason in EXCLUSIONS.items()]
    write_jsonl(OUT / "cohort/primary_dissociation_manifest.jsonl", manifest_rows)
    write_jsonl(OUT / "cohort/exclusions.jsonl", excluded_rows)
    write_jsonl(OUT / "annotations/mention_roi_annotations.jsonl", mention_rows)
    write_jsonl(OUT / "annotations/required_roi_annotations.jsonl", required_rows)
    write_jsonl(OUT / "annotations/irrelevant_roi_annotations.jsonl", irrelevant_rows)
    write_jsonl(OUT / "annotations/semantic_state_labels.jsonl", state_rows)
    write_jsonl(OUT / "annotations/state_pair_annotations.jsonl", pair_rows)

    frozen_targets = json.loads((ROOT / "outputs/stage3c1/config/frozen_targets.json").read_text())
    controls = json.loads((ROOT / "outputs/stage3c1/config/control_heads.json").read_text())
    write_json(OUT / "config/frozen_targets.json", frozen_targets)
    write_json(OUT / "config/temporal_grid.json", {
        "target_a": {"center": "E_d", "offsets": list(A_OFFSETS)},
        "target_b": {"center": "E_d-1", "offsets": list(B_OFFSETS)},
        "missing_history_rule": "omit checkpoints with generated_index < 1",
        "frozen_before_attention_analysis": True,
    })
    write_json(OUT / "config/sink_definitions.json", {
        "primary": {"name": "first_prompt_token", "absolute_positions": [0], "expected_token": "<|im_start|>"},
        "secondary": ["assistant/control markers", "BOS-like special tokens", "newline/control positions", "image-boundary neighbors", "active query token"],
        "status": "candidate sink; descriptive only",
        "source": "prospectively frozen from Stage 3C.1 before Stage 3C.2 measurement",
    })
    write_json(OUT / "config/primary_contrasts.json", {
        "family": [
            "T vs M at retrieval",
            "retrieval-needed vs mention-only for QK_T",
            "retrieval-needed vs mention-only for A_T",
            "retrieval-needed vs mention-only for alphaV_T",
            "sink change during retrieval",
            "T-vs-M temporal crossover",
            "causal-vs-noncausal head enrichment",
        ],
        "multiple_testing": "Holm correction across the seven frozen contrasts",
        "primary_unit": "base_problem_id",
        "frozen_before_attention_analysis": True,
    })
    config = {
        "created_at": now,
        "source_plan": "plan/stage3c2_plan.md",
        "source_plan_sha256": sha256(ROOT / "plan/stage3c2_plan.md"),
        "model": "Qwen3-VL-4B-Thinking",
        "model_checkpoint": "/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e",
        "dataset_root": "/data/dataset/MathVerse",
        "conditions": ["O", "O_sham", "C", "C_sham"],
        "primary_base_count": len(manifest_rows),
        "seed": 1234,
        "capture_heads_by_layer": {"28": [0, 1, 2, 3, 4, 5, 6, 16], "29": [0, 1, 2, 3, 6, 11, 12, 15]},
        "architecture_expected": {"language_layers": 36, "logical_query_heads": 32, "kv_heads": 8, "query_heads_per_kv_group": 4, "head_dimension": 128},
        "causal_heads": {"target_a": [11, 6, 15, 12], "target_b": [16, 0, 3, 6]},
        "noncausal_heads": {"target_a": controls["target_a_layer29"], "target_b": controls["target_b_layer28"]},
        "source_mass_tolerance": 0.005,
        "instrumentation_logit_tolerance": 1e-5,
        "deterministic_repeat_tolerance": 0.0,
        "reconstruction_tolerance": 0.0,
        "selection_used_attention": False,
        "measurement_is_passive": True,
        "attention_is_descriptive_not_causal": True,
        "gpu": {"required_class": "A5000", "gpus": 2, "slurm_job_id": "106936", "tmux_session": "8"},
    }
    write_json(OUT / "config/stage3c2_config.json", config)
    print(json.dumps({"primary_bases": len(manifest_rows), "excluded": len(excluded_rows), "semantic_rows": len(state_rows), "state_pairs": len(pair_rows)}, indent=2))


if __name__ == "__main__":
    main()
