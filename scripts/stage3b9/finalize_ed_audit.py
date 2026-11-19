#!/usr/bin/env python3
"""Freeze strict E_d annotations and the Phase-A/Phase-B prospective cohorts."""

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
    payload = json.dumps([int(value) for value in token_ids], separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def prefix_match_count(left: list[int], right: list[int]) -> int:
    count = 0
    for first, second in zip(left, right):
        if int(first) != int(second):
            break
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", type=Path, required=True)
    args = parser.parse_args()
    annotation_target = OUT / "evidence_audit/annotations.jsonl"
    if annotation_target.exists():
        raise FileExistsError(f"Frozen E_d annotations already exist: {annotation_target}")
    drafts = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "evidence_audit/draft_v2/ed_audit_draft.jsonl")}
    completed_rows = [
        *read_jsonl(OUT / "prospective_generation/phase_a_completed_correct_pool.jsonl"),
        *read_jsonl(OUT / "prospective_generation/phase_b_completed_correct_pool.jsonl"),
    ]
    completed = {str(row["base_problem_id"]): row for row in completed_rows}
    if set(drafts) != set(completed):
        raise RuntimeError("E_d drafts must exactly cover every completed-correct candidate")
    payload = read_json(args.decisions)
    if any(payload.get(key) is not False for key in ("causal_scores_inspected", "attention_used", "subspace_fit_inspected")):
        raise RuntimeError("E_d decisions must be causal-score-, attention-, and fit-blind")
    decisions = {str(row["base_problem_id"]): row for row in payload["decisions"]}
    if set(decisions) != set(drafts):
        raise RuntimeError("Manual decisions must cover every E_d draft")
    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT, local_files_only=True)
    rois = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "roi_validation/roi_token_mapping_all_fresh.jsonl")}
    frozen_at = datetime.now(timezone.utc).isoformat()
    annotations, audits, exclusions = [], [], []
    accepted_by_phase = {"phase_a": [], "phase_b": []}
    for base in sorted(drafts, key=int):
        draft, decision, completed_row = drafts[base], decisions[base], completed[base]
        status = str(decision["decision"])
        if status not in {"ACCEPT", "REJECT"}:
            raise RuntimeError(f"Invalid E_d decision for base {base}: {status}")
        audits.append({
            **draft,
            **decision,
            "frozen_at": frozen_at,
            "causal_scores_inspected": False,
            "attention_used": False,
            "subspace_fit_inspected": False,
        })
        if status == "REJECT":
            exclusions.append({
                "base_problem_id": base,
                "phase": draft["phase"],
                "stage": "strict_E_d_manual_audit",
                "reason": decision["reason"],
                "causal_scores_inspected": False,
                "attention_used": False,
                "subspace_fit_inspected": False,
            })
            continue
        e0, e1 = int(decision["e0_start_token"]), int(decision["e1_completion_token"])
        generation = read_json(ROOT / completed_row["artifact_dir"] / "generation.json")
        generated_ids = [int(value) for value in generation["generated_token_ids"]]
        if not 0 <= e0 < e1 <= len(generated_ids):
            raise RuntimeError(f"Invalid E0/E1 interval for base {base}")
        if decision.get("pre_e0_discriminative_content_absent") is not True or decision.get("semantic_decision_meaningful") is not True:
            raise RuntimeError(f"Accepted E_d decision lacks required validity flags for base {base}")
        candidate_pairs = []
        for candidate in draft["candidate_pairs"]:
            common = [int(value) for value in candidate["common_prefix_token_ids"]]
            history = generated_ids[:e0] + common
            ed = e0 + len(common)
            natural = generated_ids[e0:e0 + len(common)]
            match_count = prefix_match_count(natural, common)
            candidate_pairs.append({
                **candidate,
                "e0_start_token": e0,
                "e1_completion_token": e1,
                "ed_generated_index": ed,
                "history_before_ed_token_ids": history,
                "history_before_ed_text": tokenizer.decode(history, skip_special_tokens=False, clean_up_tokenization_spaces=False),
                "history_before_ed_sha256": token_hash(history),
                "baseline_trace_common_prefix_match_count": match_count,
                "baseline_trace_common_prefix_exact": match_count == len(common),
                "mapping_rule": "E_d is E0 plus the token LCP of the frozen evidence pair; history is natural baseline y_<E0 plus the shared teacher-forced evidence lead.",
            })
        annotation = {
            "base_problem_id": base,
            "example_id": str(completed_row["example_id"]),
            "phase": draft["phase"],
            "evidence_type": "localized_numeric_label",
            "edit_version": completed_row["edit_version"],
            "edit_metadata": completed_row["edit_metadata"],
            "e0_start_token": e0,
            "e1_completion_token": e1,
            "baseline_e0_to_e1_text": tokenizer.decode(generated_ids[e0:e1], skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "candidate_pairs": candidate_pairs,
            "semantic_decision_meaningful": True,
            "pre_e0_discriminative_content_absent": True,
            "manual_audit_status": "pass",
            "manual_audit_note": decision["reason"],
            "manual_review": {
                "reviewed": True,
                "reviewed_at": payload["reviewed_at"],
                "reviewer": payload["reviewer"],
                "used_causal_scores": False,
                "used_attention": False,
                "used_subspace_fit": False,
            },
        }
        if draft["phase"] == "phase_a":
            pair = candidate_pairs[0]
            annotation.update({key: pair[key] for key in (
                "candidate_original", "candidate_counterfactual",
                "original_candidate_token_ids", "counterfactual_candidate_token_ids",
                "common_prefix_token_ids", "common_prefix_text",
                "original_divergent_suffix_ids", "counterfactual_divergent_suffix_ids",
                "original_divergent_suffix_text", "counterfactual_divergent_suffix_text",
                "ed_generated_index", "history_before_ed_token_ids", "history_before_ed_text",
                "history_before_ed_sha256", "baseline_trace_common_prefix_match_count",
                "baseline_trace_common_prefix_exact", "mapping_rule",
            )})
        annotations.append(annotation)
        accepted_by_phase[draft["phase"]].append({
            **completed_row,
            "event": {
                "e0_start_token": e0,
                "e1_completion_token": e1,
                "ed_generated_index": candidate_pairs[0]["ed_generated_index"],
            },
            "strict_ed_audit": {
                "decision": "ACCEPT",
                "pre_e0_discriminative_content_absent": True,
                "semantic_decision_meaningful": True,
                "causal_scores_inspected": False,
                "attention_used": False,
                "subspace_fit_inspected": False,
            },
        })
    for phase in accepted_by_phase:
        accepted_by_phase[phase].sort(key=lambda row: int(row["base_problem_id"]))
    counts = {phase: len(rows) for phase, rows in accepted_by_phase.items()}
    if counts["phase_a"] < 24 or counts["phase_b"] < 12:
        ensure_directory(OUT / "evidence_audit")
        write_json(OUT / "evidence_audit/insufficient_summary.json", {
            "completed_correct_audited": len(drafts),
            "accepted_by_phase": counts,
            "minimum": {"phase_a": 24, "phase_b": 12},
            "requires_additional_blind_expansion": True,
        })
        raise RuntimeError(f"Strict E_d cohort is insufficient: {counts}")
    selected_a = accepted_by_phase["phase_a"][:32]
    selected_b = accepted_by_phase["phase_b"][:16]
    selected_bases = {str(row["base_problem_id"]) for row in [*selected_a, *selected_b]}
    if not selected_bases.issubset(rois):
        raise RuntimeError("Selected E_d cohort lacks frozen ROI mappings")
    ensure_directory(annotation_target.parent)
    write_jsonl(annotation_target, annotations)
    write_jsonl(OUT / "evidence_audit/strict_ed_audit.jsonl", audits)
    write_jsonl(OUT / "evidence_audit/exclusions.jsonl", exclusions)
    write_jsonl(OUT / "phase_a_shared/pre_applicability_manifest.jsonl", selected_a)
    write_jsonl(OUT / "phase_b_local/cohort_manifest.jsonl", selected_b)
    value_variants = []
    annotation_by_base = {row["base_problem_id"]: row for row in annotations}
    for row in selected_b:
        base = str(row["base_problem_id"])
        edit = read_json(ROOT / row["edit_metadata"])
        value_variants.append({"base_problem_id": base, "condition": "O", "semantic_value": str(edit["original"]), "role": "original"})
        for index, value in enumerate(edit["alternatives"], start=1):
            pair = next(pair for pair in annotation_by_base[base]["candidate_pairs"] if pair["pair_id"] == f"value_{index}")
            value_variants.append({
                "base_problem_id": base,
                "condition": f"C{index}",
                "semantic_value": str(value),
                "role": "counterfactual",
                "pair_id": f"value_{index}",
                "history_before_ed_sha256": pair["history_before_ed_sha256"],
                "ed_generated_index": pair["ed_generated_index"],
            })
    write_jsonl(OUT / "phase_b_local/value_variant_manifest.jsonl", value_variants)
    for name, rows in (("phase_a_pre_applicability_shards", selected_a), ("phase_b_shards", selected_b)):
        shard_dir = OUT / f"config/{name}"
        ensure_directory(shard_dir)
        write_jsonl(shard_dir / "shard_00.jsonl", rows[::2])
        write_jsonl(shard_dir / "shard_01.jsonl", rows[1::2])
    reserve = [row for phase in accepted_by_phase.values() for row in phase if str(row["base_problem_id"]) not in selected_bases]
    write_jsonl(OUT / "evidence_audit/accepted_reserve.jsonl", reserve)
    write_json(
        OUT / "evidence_audit/freeze_summary.json",
        {
            "frozen_at": frozen_at,
            "completed_correct_screened": len(drafts),
            "accepted_by_phase": counts,
            "rejected": len(exclusions),
            "selected_phase_a": len(selected_a),
            "selected_phase_b": len(selected_b),
            "selection_rule_if_above_target": "ascending base_problem_id after eligibility; no geometry, attention, or causal score",
            "phase_a_base_problem_ids": [str(row["base_problem_id"]) for row in selected_a],
            "phase_b_base_problem_ids": [str(row["base_problem_id"]) for row in selected_b],
            "causal_scores_inspected": False,
            "attention_used": False,
            "subspace_fit_inspected": False,
        },
    )
    print(json.dumps({"accepted_by_phase": counts, "selected_phase_a": len(selected_a), "selected_phase_b": len(selected_b), "rejected": len(exclusions)}, indent=2))


if __name__ == "__main__":
    main()
