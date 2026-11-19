#!/usr/bin/env python3
"""Apply score-blind manual decisions and freeze the fresh atlas cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3c8.fresh import validate_frozen_screen_prefix


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    args = parse_args()
    destination = OUT / "cohort/fresh_atlas_manifest.jsonl"
    if destination.exists() and destination.stat().st_size:
        raise FileExistsError("Fresh atlas cohort is already frozen")
    decisions = {str(row["base_problem_id"]): row for row in read_jsonl(args.decisions)}
    edit_manifest = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "cohort/fresh_edit_manifest_reviewed.jsonl")}
    roi_rows = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "cohort/fresh_roi_mapping_pending.jsonl")}
    raw = read_jsonl(OUT / "prospective_generation/raw_outcome_manifest.jsonl")
    screen = read_jsonl(OUT / "cohort/prospective_screen_manifest.jsonl")
    candidate_audit = read_jsonl(OUT / "cohort/fresh_candidate_audit.jsonl")
    edit_rejections = read_jsonl(OUT / "cohort/fresh_edit_rejections.jsonl")
    if set(decisions) != set(edit_manifest) or set(decisions) != set(roi_rows):
        raise RuntimeError("Manual decisions must exactly cover all constructed edits and ROI mappings")
    reviewed_at = datetime.now(timezone.utc).isoformat()
    accepted_candidates = []
    decision_reason = {}
    for base, decision in decisions.items():
        if decision.get("carrier_scores_available") is not False or decision.get("attention_used") is not False:
            raise RuntimeError(f"Decision provenance invalid for base {base}")
        status = str(decision["decision"]).upper()
        edit_path = ROOT / edit_manifest[base]["edit_metadata"]
        edit = read_json(edit_path)
        edit["manual_validation"] = {
            "status": "pass" if status == "ACCEPT" else "fail",
            "reviewer": "primary research agent",
            "reviewed_at": reviewed_at,
            "full_image_review": bool(decision["edit_checks"]["full_image"]),
            "roi_crop_review": bool(decision["edit_checks"]["roi_crop"]),
            "target_semantics_exact": bool(decision["edit_checks"]["target_semantics_exact"]),
            "unrelated_content_unchanged": bool(decision["edit_checks"]["unrelated_content_unchanged"]),
            "all_conditions_legible": bool(decision["edit_checks"]["legible"]),
            "reason": str(decision.get("reason", "")),
            "causal_scores_available": False,
        }
        write_json(edit_path, edit)
        roi = roi_rows[base]
        roi["manual_overlay_validation"] = {
            "status": "pass" if status == "ACCEPT" else "fail",
            "reviewer": "primary research agent",
            "reviewed_at": reviewed_at,
            "target_roi_exact": bool(decision["roi_checks"]["target_roi_exact"]),
            "token_overlay_aligned": bool(decision["roi_checks"]["token_overlay_aligned"]),
            "causal_scores_available": False,
        }
        decision_reason[base] = str(decision.get("reason", ""))
        if status == "ACCEPT":
            event = decision["event"]
            if int(event["ed_generated_index"]) < 17:
                raise RuntimeError(f"Accepted base {base} lacks a valid 16-token recent window")
            if len(event["history_before_ed_token_ids"]) != int(event["ed_generated_index"]):
                raise RuntimeError(f"Strict E_d history length mismatch for base {base}")
            payload = json.dumps(
                [int(value) for value in event["history_before_ed_token_ids"]], separators=(",", ":")
            ).encode("ascii")
            if hashlib.sha256(payload).hexdigest() != event.get("history_before_ed_sha256"):
                raise RuntimeError(f"Strict E_d prefix hash mismatch for base {base}")
            if not event.get("original_candidate_exact_generated_tokens") or not event.get("prefix_ends_at_token_boundary"):
                raise RuntimeError(f"Evidence candidates are not exact generated-token continuations for base {base}")
            if event.get("manual_audit_status") != "pass" or not event.get("semantic_decision_meaningful") or not event.get("pre_ed_discriminative_content_absent"):
                raise RuntimeError(f"Strict E_d semantic audit failed for base {base}")
            accepted_candidates.append({
                **edit_manifest[base],
                "cohort_role": "fresh",
                "event": event,
                "roi_mapping": roi,
                "target_evidence": str(decision["target_evidence"]),
                "original_fact": str(event["original_fact"]),
                "counterfactual_fact": str(event["counterfactual_fact"]),
                "evidence_type": str(decision["evidence_type"]),
                "manual_semantic_relation_valid": True,
                "strict_ed_valid": True,
                "recent_window_valid": True,
                "prompt_token_annotation_valid": "pending_pre_scoring_freeze",
                "selection_used_attention": False,
                "selection_used_carrier_outcome": False,
                "causal_scores_available_at_freeze": False,
                "frozen_at": reviewed_at,
            })
    accepted_candidates.sort(key=lambda row: int(row["screen_order"]))
    retained = accepted_candidates[:64]
    if len(retained) < 56:
        raise RuntimeError(f"Fresh cohort minimum not met: {len(retained)}/56")
    prefix_validation = validate_frozen_screen_prefix(
        screen=screen,
        raw=raw,
        candidate_audit=candidate_audit,
        reviewed_edits=[*edit_manifest.values(), *edit_rejections],
        retained=retained,
    )
    retained_ids = {str(row["base_problem_id"]) for row in retained}
    raw_by_base = {str(row["base_problem_id"]): row for row in raw}
    screening_rows, exclusions = [], []
    for frozen in screen:
        base = str(frozen["base_problem_id"])
        outcome = raw_by_base.get(base)
        if base in retained_ids:
            status, reason = "retained", "all frozen inclusion criteria passed"
        elif outcome is None:
            status, reason = "not_attempted", "prospective target reached before exhausting frozen budget"
        elif outcome["status"] != "correct":
            status, reason = "excluded", f"generation_{outcome['status']}"
        elif base in decisions and str(decisions[base]["decision"]).upper() != "ACCEPT":
            status, reason = "excluded", decision_reason[base]
        elif base in {str(row["base_problem_id"]) for row in accepted_candidates[64:]}:
            status, reason = "eligible_reserve", "target 64 reached earlier in frozen screen order"
        else:
            status, reason = "excluded", "no clean localized numeric edit/evidence event qualified"
        row = {
            "base_problem_id": base,
            "example_id": str(frozen["example_id"]),
            "screen_order": int(frozen["order"]),
            "generation_status": "not_attempted" if outcome is None else outcome["status"],
            "screening_status": status,
            "reason": reason,
            "selection_used_attention": False,
            "selection_used_carrier_outcome": False,
        }
        screening_rows.append(row)
        if status == "excluded":
            exclusions.append(row)
    write_jsonl(destination, retained)
    write_jsonl(OUT / "cohort/candidate_screening.jsonl", screening_rows)
    write_jsonl(OUT / "cohort/exclusions.jsonl", exclusions)
    write_jsonl(OUT / "cohort/fresh_roi_mapping.jsonl", [row["roi_mapping"] for row in retained])
    write_json(OUT / "cohort/sample_accounting.json", {
        "screening_budget": len(screen),
        "screened": len(raw),
        "unattempted": len(screen) - len(raw),
        "generation_status_counts": dict(Counter(str(row["status"]) for row in raw)),
        "completed_correct": sum(row["status"] == "correct" for row in raw),
        "edit_valid": sum(str(row["decision"]).upper() == "ACCEPT" for row in decisions.values()),
        "strict_ed_valid": len(accepted_candidates),
        "roi_valid": len(accepted_candidates),
        "prompt_token_annotation_valid": "pending",
        "recent_window_valid": len(accepted_candidates),
        "retained": len(retained),
        "target": 64,
        "minimum": 56,
        "status": "fresh_cohort_frozen_annotation_pending",
        "selection_used_attention": False,
        "selection_used_carrier_outcome": False,
        "screen_prefix_validation": prefix_validation,
    })
    print(json.dumps({"accepted_clean": len(accepted_candidates), "retained": len(retained), "excluded": len(exclusions)}, indent=2))


if __name__ == "__main__":
    main()
