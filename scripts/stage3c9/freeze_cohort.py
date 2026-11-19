#!/usr/bin/env python3
"""Freeze disjoint Stage 3C.9 validation/primary cohorts and annotations."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3c9.protocol import long_horizon_cohort_gate


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semantic-audit", type=Path, required=True)
    parser.add_argument("--semantic-accepted", type=Path, required=True)
    return parser.parse_args()


def sha_payload(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def main() -> None:
    args = parse_args()
    final_paths = [
        OUT / "cohort/validation_manifest.jsonl",
        OUT / "cohort/primary_manifest.jsonl",
        OUT / "cohort/exclusions.jsonl",
    ]
    if any(path.exists() for path in final_paths):
        raise FileExistsError("Stage 3C.9 cohort freeze is create-once")
    raw = read_jsonl(OUT / "cohort/raw_outcome_manifest.jsonl")
    raw_by_example = {str(row["example_id"]): row for row in raw}
    accounting = read_json(OUT / "cohort/screening_accounting.json")
    semantic_audit = {str(row["base_problem_id"]): row for row in read_jsonl(args.semantic_audit)}
    semantic = {str(row["base_problem_id"]): row for row in read_jsonl(args.semantic_accepted)}
    edits = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "cohort/edit_manifest_reviewed.jsonl")}
    edit_rejections = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "cohort/edit_rejections.jsonl")}
    rois = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "cohort/roi_mapping.jsonl")}
    roi_rejections = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "cohort/roi_rejections.jsonl")}
    valid = []
    for base in sorted(set(semantic) & set(edits) & set(rois), key=lambda value: int(semantic[value]["screen_order"])):
        item = semantic[base]
        trajectory = raw_by_example.get(str(item["example_id"]))
        if trajectory is None or trajectory["status"] != "correct":
            raise RuntimeError(f"Base {base} has no matching completed-correct trajectory")
        artifact_dir = str(trajectory["artifact_dir"])
        if len(item["events"]) != 3:
            raise RuntimeError(f"Base {base} must freeze exactly three events")
        if not item["eligibility_gate"]["eligible_before_edit_roi_validation"]:
            raise RuntimeError(f"Base {base} failed semantic eligibility after review")
        valid.append({
            **item,
            "variant": str(trajectory["variant"]),
            "source": str(trajectory["source"]),
            "generated_token_count": int(trajectory["generated_token_count"]),
            "artifact_dir": artifact_dir,
            "generation_path": f"{artifact_dir}/generation.json",
            "tokens_path": f"{artifact_dir}/tokens.jsonl",
            "edit_metadata": edits[base]["edit_metadata"],
            "roi_mapping": rois[base],
            "layout_exact": bool(rois[base]["four_condition_layout_exact"]),
            "selection_used_attention": False,
            "causal_scores_available_at_freeze": False,
        })
    valid.sort(key=lambda row: int(row["screen_order"]))
    validation = valid[:8]
    primary = valid[8:56]
    gate = long_horizon_cohort_gate(
        [row["base_problem_id"] for row in primary],
        [row["base_problem_id"] for row in validation],
    )
    if not gate["run_primary"]:
        if int(accounting["attempted"]) < int(accounting["maximum_budget"]):
            raise RuntimeError(
                f"Only {len(valid)} fully valid bases; extend the prospective screen before cohort freeze"
            )
        write_json(OUT / "cohort/cohort_gate.json", {
            **gate,
            "reason": "fewer_than_40_primary_after_full_1000_trajectory_budget",
            "fully_valid_total": len(valid),
            "causal_scoring_started": False,
        })
        write_jsonl(final_paths[0], validation)
        write_jsonl(final_paths[1], [])
        write_jsonl(final_paths[2], [])
        return

    frozen_at = datetime.now(timezone.utc).isoformat()
    validation = [{**row, "cohort_role": "mechanical_validation", "frozen_at": frozen_at} for row in validation]
    primary = [{**row, "cohort_role": "primary", "frozen_at": frozen_at} for row in primary]
    selected = {str(row["base_problem_id"]) for row in validation + primary}
    valid_bases = {str(row["base_problem_id"]) for row in valid}
    exclusions = []
    for row in raw:
        base = str(row["base_problem_id"])
        if base in selected:
            continue
        if row["status"] != "correct":
            reason = f"generation_{row['status']}"
        elif base in semantic_audit and semantic_audit[base]["decision"] == "REJECT":
            reason = semantic_audit[base]["reason"]
        elif base in edit_rejections:
            reason = f"edit_rejected:{edit_rejections[base]['rejection_reason']}"
        elif base in roi_rejections:
            reason = f"roi_rejected:{roi_rejections[base]['manual_overlay_validation']['review'].get('reason','')}"
        elif base in valid_bases:
            reason = "fully_valid_after_frozen_target_reached"
        elif base not in semantic_audit:
            reason = "not_reached_by_complete_manual_review_prefix_or_no_semantic_proposal"
        elif base not in edits:
            reason = "semantic_valid_but_edit_not_valid"
        elif base not in rois:
            reason = "edit_valid_but_roi_not_valid"
        else:
            reason = "not_retained"
        exclusions.append({
            "base_problem_id": base,
            "example_id": str(row["example_id"]),
            "screen_order": int(row["screen_order"]),
            "status": row["status"],
            "reason": reason,
            "selection_used_attention": False,
            "causal_scores_available_at_exclusion": False,
        })
    write_jsonl(OUT / "cohort/validation_manifest.jsonl", validation)
    write_jsonl(OUT / "cohort/primary_manifest.jsonl", primary)
    write_jsonl(OUT / "cohort/exclusions.jsonl", exclusions)
    write_json(OUT / "cohort/cohort_gate.json", {
        **gate,
        "fully_valid_total": len(valid),
        "retained_validation": len(validation),
        "retained_primary": len(primary),
        "target_primary": 48,
        "frozen_at": frozen_at,
        "causal_scoring_started": False,
        "selection_used_attention": False,
    })

    segments, events, spans, readouts, relations = [], [], [], [], []
    for item in validation + primary:
        base, role = str(item["base_problem_id"]), item["cohort_role"]
        for segment in item["reasoning_segments"]:
            segments.append({"base_problem_id": base, "cohort_role": role, **segment, "annotation_frozen_at": frozen_at})
        for event in item["events"]:
            event_key = f"{base}:{event['event_id']}"
            common = {"base_problem_id": base, "cohort_role": role, "event_key": event_key, "event_id": int(event["event_id"]), "annotation_frozen_at": frozen_at}
            events.append({**common, "event_role": event["event_role"], "evidence_relation": event["evidence_relation"], "temporal_location": event["temporal_location"]})
            spans.append({**common, "start_token": int(event["span_start_token"]), "end_token": int(event["span_end_token"]), "span_text": event["span_text"], "span_hash": sha_payload([event["span_start_token"], event["span_end_token"], event["span_text"]]), "matched_neighbor_span": event["matched_neighbor_span"]})
            readouts.append({**common, "readout_type": "local_use", **event["local_use_readout"]})
            relations.append({**common, "evidence_relation": event["evidence_relation"], "target_evidence": item["target_evidence"], "original_value": item["original_value"], "counterfactual_value": item["counterfactual_value"]})
        readouts.append({"base_problem_id": base, "cohort_role": role, "event_key": f"{base}:final", "event_id": None, "readout_type": "final_use", **item["final_use_readout"], "annotation_frozen_at": frozen_at})
    write_jsonl(OUT / "annotations/reasoning_segments.jsonl", segments)
    write_jsonl(OUT / "annotations/events.jsonl", events)
    write_jsonl(OUT / "annotations/event_spans.jsonl", spans)
    write_jsonl(OUT / "annotations/local_use_readouts.jsonl", readouts)
    write_jsonl(OUT / "annotations/evidence_relation_labels.jsonl", relations)

    accounting.update({
        "long_enough": sum(row.get("eligibility_gate", {}).get("long_enough_before_final_readout", False) for row in semantic_audit.values()),
        "multi_segment": sum(row.get("decision") == "ACCEPT" for row in semantic_audit.values()),
        "multi_event": sum(row.get("decision") == "ACCEPT" for row in semantic_audit.values()),
        "edit_valid": len(edits),
        "ROI_valid": len(rois),
        "retained": len(primary),
        "validation_retained": len(validation),
        "status": "primary_and_validation_cohorts_frozen",
        "frozen_at": frozen_at,
        "exclusion_reason_counts": dict(Counter(row["reason"].split(":", 1)[0] for row in exclusions)),
    })
    write_json(OUT / "cohort/screening_accounting.json", accounting)
    print(json.dumps({"fully_valid": len(valid), "validation": len(validation), "primary": len(primary), "gate": gate}, indent=2))


if __name__ == "__main__":
    main()
