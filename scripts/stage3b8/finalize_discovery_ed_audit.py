#!/usr/bin/env python3
"""Freeze score- and attention-blind Stage 3B.8 discovery E_d decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from transformers import AutoTokenizer

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8/discovery_cohort"
CHECKPOINT = Path("/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def token_hash(token_ids: list[int]) -> str:
    payload = json.dumps([int(value) for value in token_ids], separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", type=Path, required=True)
    args = parser.parse_args()
    target = OUT / "annotations/discriminative_event_annotations.jsonl"
    if target.exists():
        raise FileExistsError(f"Frozen discovery annotations already exist: {target}")
    drafts = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "ed_audit_draft/discriminative_event_draft.jsonl")}
    completed = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "completed_correct_pending_strict_ed.jsonl")}
    payload = read_json(args.decisions)
    if payload.get("causal_scores_inspected") is not False or payload.get("attention_used") is not False or payload.get("subspace_fit_inspected") is not False:
        raise RuntimeError("Discovery E_d decisions must be score-, fit-, and attention-blind")
    decisions = {str(row["base_problem_id"]): row for row in payload["decisions"]}
    if set(decisions) != set(drafts):
        raise RuntimeError("Manual decisions must cover every completed-correct draft")
    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT, local_files_only=True)
    annotations, manifest, audits, exclusions = [], [], [], []
    for base in sorted(drafts, key=int):
        draft, decision, completed_row = drafts[base], decisions[base], completed[base]
        status = str(decision["decision"])
        if status not in {"ACCEPT", "REJECT"}:
            raise RuntimeError(f"Invalid E_d decision for base {base}: {status}")
        audits.append({**draft, **decision, "frozen_at": datetime.now(timezone.utc).isoformat(), "causal_scores_inspected": False, "attention_used": False, "subspace_fit_inspected": False})
        if status == "REJECT":
            exclusions.append({"base_problem_id": base, "stage": "strict_E_d_manual_audit", "reason": decision["reason"], "causal_scores_inspected": False, "attention_used": False, "subspace_fit_inspected": False})
            continue
        e0, e1 = int(decision["e0_start_token"]), int(decision["e1_completion_token"])
        example_dir = ROOT / completed_row["artifact_dir"]
        generated_ids = [int(value) for value in read_json(example_dir / "generation.json")["generated_token_ids"]]
        if not 0 <= e0 < e1 <= len(generated_ids):
            raise RuntimeError(f"Invalid E0/E1 interval for base {base}")
        common = [int(value) for value in draft["common_prefix_token_ids"]]
        history = generated_ids[:e0] + common
        ed = e0 + len(common)
        annotation = {
            "base_problem_id": base,
            "example_id": str(completed_row["example_id"]),
            "evidence_type": "localized_numeric_label",
            "edit_version": completed_row["edit_version"],
            "edit_metadata": completed_row["edit_metadata"],
            "candidate_original": draft["candidate_original"],
            "candidate_counterfactual": draft["candidate_counterfactual"],
            "original_candidate_token_ids": [int(value) for value in draft["original_candidate_token_ids"]],
            "counterfactual_candidate_token_ids": [int(value) for value in draft["counterfactual_candidate_token_ids"]],
            "e0_start_token": e0,
            "e1_completion_token": e1,
            "common_prefix_token_count": len(common),
            "common_prefix_token_ids": common,
            "common_prefix_text": draft["common_prefix_text"],
            "ed_generated_index": ed,
            "original_divergent_suffix_ids": [int(value) for value in draft["original_divergent_suffix_ids"]],
            "counterfactual_divergent_suffix_ids": [int(value) for value in draft["counterfactual_divergent_suffix_ids"]],
            "original_divergent_suffix_text": draft["original_divergent_suffix_text"],
            "counterfactual_divergent_suffix_text": draft["counterfactual_divergent_suffix_text"],
            "history_before_ed_token_ids": history,
            "history_before_ed_text": tokenizer.decode(history, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "history_before_ed_sha256": token_hash(history),
            "baseline_e0_to_e1_text": tokenizer.decode(generated_ids[e0:e1], skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "baseline_trace_common_prefix_match_count": int(decision["baseline_trace_common_prefix_match_count"]),
            "baseline_trace_common_prefix_exact": bool(decision["baseline_trace_common_prefix_exact"]),
            "mapping_rule": "E_d is E0 plus the token LCP of the two frozen evidence continuations; history is natural baseline y_<E0 plus the shared teacher-forced evidence lead.",
            "semantic_decision_meaningful": True,
            "pre_ed_discriminative_content_absent": True,
            "manual_audit_status": "pass",
            "manual_audit_note": decision["reason"],
            "manual_review": {"reviewed": True, "reviewed_at": payload["reviewed_at"], "reviewer": payload["reviewer"], "used_causal_scores": False, "used_attention": False, "used_subspace_fit": False},
        }
        annotations.append(annotation)
        manifest.append({**completed_row, "candidate_original": draft["candidate_original"], "candidate_counterfactual": draft["candidate_counterfactual"], "event": {"e0_start_token": e0, "e1_completion_token": e1, "ed_generated_index": ed}, "history_before_ed_sha256": annotation["history_before_ed_sha256"], "strict_ed_audit": {"decision": "ACCEPT", "pre_ed_discriminative_content_absent": True, "semantic_decision_meaningful": True, "causal_scores_inspected": False, "attention_used": False, "subspace_fit_inspected": False}})
    if not 16 <= len(annotations) <= 20:
        raise RuntimeError(f"Strict E_d audit retained {len(annotations)} bases; 16--20 required")
    ensure_directory(target.parent)
    write_jsonl(target, annotations)
    write_jsonl(OUT / "discovery_manifest.jsonl", manifest)
    write_jsonl(OUT / "strict_ed_audit.jsonl", audits)
    write_jsonl(OUT / "strict_ed_exclusions.jsonl", exclusions)
    write_json(OUT / "strict_ed_freeze_summary.json", {"completed_correct_screened": len(drafts), "accepted": len(annotations), "rejected": len(exclusions), "accepted_base_problem_ids": [row["base_problem_id"] for row in annotations], "causal_scores_inspected": False, "attention_used": False, "subspace_fit_inspected": False})
    print(json.dumps({"accepted": len(annotations), "rejected": len(exclusions)}, indent=2))


if __name__ == "__main__":
    main()
