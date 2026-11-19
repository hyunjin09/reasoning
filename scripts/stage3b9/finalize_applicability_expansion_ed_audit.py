#!/usr/bin/env python3
"""Freeze expansion E_d decisions and append selected bases to Phase A."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from transformers import AutoTokenizer

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
CHECKPOINT = Path("/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def token_hash(token_ids: list[int]) -> str:
    return hashlib.sha256(json.dumps([int(value) for value in token_ids], separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", type=Path, required=True)
    args = parser.parse_args()
    annotation_target = OUT / "evidence_audit/annotations_v2.jsonl"
    if annotation_target.exists():
        raise FileExistsError(f"Expanded annotations already exist: {annotation_target}")
    drafts = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "evidence_audit/applicability_expansion_draft/ed_audit_draft.jsonl")}
    completed = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "prospective_generation/applicability_expansion_completed_correct.jsonl")}
    if set(drafts) != set(completed):
        raise RuntimeError("Expansion drafts must exactly cover completed-correct examples")
    payload = read_json(args.decisions)
    if any(payload.get(key) is not False for key in ("causal_scores_inspected", "attention_used", "subspace_fit_inspected")):
        raise RuntimeError("Expansion decisions must remain score-, attention-, and fit-blind")
    decisions = {str(row["base_problem_id"]): row for row in payload["decisions"]}
    if set(decisions) != set(drafts):
        raise RuntimeError("Expansion decisions must cover every draft")
    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT, local_files_only=True)
    roi_bases = {str(row["base_problem_id"]) for row in read_jsonl(OUT / "roi_validation_applicability_expansion_v2/roi_token_mapping.jsonl")}
    frozen_at = datetime.now(timezone.utc).isoformat()
    audits, annotations, accepted, exclusions = [], [], [], []
    for base in sorted(drafts, key=int):
        draft, decision, row = drafts[base], decisions[base], completed[base]
        audits.append({**draft, **decision, "frozen_at": frozen_at, "causal_scores_inspected": False, "attention_used": False, "subspace_fit_inspected": False})
        if decision["decision"] == "REJECT":
            exclusions.append({"base_problem_id": base, "stage": "expansion_strict_E_d_manual_audit", "reason": decision["reason"],
                               "causal_scores_inspected": False, "attention_used": False, "subspace_fit_inspected": False})
            continue
        if decision["decision"] != "ACCEPT" or base not in roi_bases:
            raise RuntimeError(f"Invalid expansion decision/ROI for base {base}")
        if decision.get("pre_e0_discriminative_content_absent") is not True or decision.get("semantic_decision_meaningful") is not True:
            raise RuntimeError(f"Accepted expansion decision lacks validity flags for base {base}")
        e0, e1 = int(decision["e0_start_token"]), int(decision["e1_completion_token"])
        generation = read_json(ROOT / row["artifact_dir"] / "generation.json")
        generated_ids = [int(value) for value in generation["generated_token_ids"]]
        if not 0 <= e0 < e1 <= len(generated_ids):
            raise RuntimeError(f"Invalid expansion E0/E1 for base {base}")
        candidate = dict(draft["candidate_pairs"][0])
        common = [int(value) for value in candidate["common_prefix_token_ids"]]
        history = generated_ids[:e0] + common
        ed = e0 + len(common)
        natural = generated_ids[e0:e0 + len(common)]
        match = 0
        for left, right in zip(natural, common):
            if int(left) != int(right):
                break
            match += 1
        candidate.update({
            "e0_start_token": e0, "e1_completion_token": e1, "ed_generated_index": ed,
            "history_before_ed_token_ids": history,
            "history_before_ed_text": tokenizer.decode(history, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "history_before_ed_sha256": token_hash(history), "baseline_trace_common_prefix_match_count": match,
            "baseline_trace_common_prefix_exact": match == len(common),
            "mapping_rule": "E_d is E0 plus the token LCP of the frozen evidence pair; history is natural baseline y_<E0 plus the shared teacher-forced evidence lead.",
        })
        annotation = {
            "base_problem_id": base, "example_id": str(row["example_id"]), "phase": "phase_a",
            "evidence_type": "localized_numeric_label", "edit_version": row["edit_version"], "edit_metadata": row["edit_metadata"],
            "e0_start_token": e0, "e1_completion_token": e1,
            "baseline_e0_to_e1_text": tokenizer.decode(generated_ids[e0:e1], skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "candidate_pairs": [candidate], "semantic_decision_meaningful": True,
            "pre_e0_discriminative_content_absent": True, "manual_audit_status": "pass", "manual_audit_note": decision["reason"],
            "manual_review": {"reviewed": True, "reviewed_at": payload["reviewed_at"], "reviewer": payload["reviewer"],
                              "used_causal_scores": False, "used_attention": False, "used_subspace_fit": False},
        }
        for key in ("candidate_original", "candidate_counterfactual", "original_candidate_token_ids", "counterfactual_candidate_token_ids",
                    "common_prefix_token_ids", "common_prefix_text", "original_divergent_suffix_ids", "counterfactual_divergent_suffix_ids",
                    "original_divergent_suffix_text", "counterfactual_divergent_suffix_text", "ed_generated_index", "history_before_ed_token_ids",
                    "history_before_ed_text", "history_before_ed_sha256", "baseline_trace_common_prefix_match_count", "baseline_trace_common_prefix_exact", "mapping_rule"):
            annotation[key] = candidate[key]
        annotations.append(annotation)
        accepted.append({**row, "event": {"e0_start_token": e0, "e1_completion_token": e1, "ed_generated_index": ed},
                         "strict_ed_audit": {"decision": "ACCEPT", "pre_e0_discriminative_content_absent": True,
                                             "semantic_decision_meaningful": True, "causal_scores_inspected": False,
                                             "attention_used": False, "subspace_fit_inspected": False}})
    old_annotations = read_jsonl(OUT / "evidence_audit/annotations.jsonl")
    old_manifest = read_jsonl(OUT / "phase_a_shared/pre_applicability_manifest.jsonl")
    capacity = max(0, 32 - len(old_manifest))
    selected = accepted[:capacity]
    reserve = accepted[capacity:]
    combined_annotations = sorted([*old_annotations, *annotations], key=lambda row: (row["phase"], int(row["base_problem_id"])))
    expanded_manifest = [*old_manifest, *selected]
    if len({str(row["base_problem_id"]) for row in expanded_manifest}) != len(expanded_manifest) or len(expanded_manifest) > 32:
        raise RuntimeError("Expanded Phase-A manifest violates identity or maximum-size rules")
    ensure_directory(annotation_target.parent)
    write_jsonl(annotation_target, combined_annotations)
    write_jsonl(OUT / "evidence_audit/applicability_expansion_strict_ed_audit.jsonl", audits)
    write_jsonl(OUT / "evidence_audit/applicability_expansion_exclusions.jsonl", exclusions)
    write_jsonl(OUT / "evidence_audit/applicability_expansion_accepted_reserve.jsonl", reserve)
    write_jsonl(OUT / "phase_a_shared/pre_applicability_manifest_v2.jsonl", expanded_manifest)
    shard_dir = OUT / "config/phase_a_applicability_expansion_scoring_shards"
    ensure_directory(shard_dir)
    write_jsonl(shard_dir / "shard_00.jsonl", selected[::2])
    write_jsonl(shard_dir / "shard_01.jsonl", selected[1::2])
    write_json(OUT / "evidence_audit/applicability_expansion_freeze.json", {
        "frozen_at": frozen_at, "completed_correct_screened": len(drafts), "accepted": len(accepted), "rejected": len(exclusions),
        "selected_for_full_v_scoring": len(selected), "accepted_reserve": len(reserve),
        "selection_rule": "ascending base_problem_id up to Phase-A maximum N=32; no new-base Value, projected-rank, fit, or attention outcome",
        "expanded_pre_applicability_count": len(expanded_manifest),
        "selected_base_problem_ids": [str(row["base_problem_id"]) for row in selected],
        "causal_scores_inspected": False, "attention_used": False, "subspace_fit_inspected": False,
    })
    print(json.dumps({"screened": len(drafts), "accepted": len(accepted), "rejected": len(exclusions),
                      "selected": len(selected), "expanded_pre_applicability": len(expanded_manifest)}, indent=2))


if __name__ == "__main__":
    main()
