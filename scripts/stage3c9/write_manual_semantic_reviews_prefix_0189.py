#!/usr/bin/env python3
"""Persist the score-blind manual semantic review through screen order 189.

The decisions below were made from Stage 3C.9 review packets and image sheets
00--08 before any Stage 3C.9 causal score existed.  This script only converts
those recorded manual decisions into the exact review schema consumed by
``materialize_semantic_reviews.py``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"
CUTOFF = 189


ACCEPTED = {
    "3", "9", "10", "14", "23", "25", "29", "30", "31", "33", "37", "38", "45", "47",
    "51", "52", "56", "59", "61", "67", "71", "73", "78", "80", "85", "86", "97", "102",
    "104", "110", "123", "128", "129", "134", "136", "140", "142", "149", "161", "176",
    "182", "186", "187", "188", "189", "190", "192", "193", "196", "206", "208", "226",
    "243", "254", "331", "332", "350", "353", "363", "423", "425", "672", "675", "743",
    "751", "752", "753", "758", "762", "782", "787",
}


REJECTIONS = {
    "2": "proposed value is the angle index 1 rather than the localized visual value 50",
    "4": "trajectory contains a long repetitive self-correction loop",
    "12": "proposed value is an angle index rather than the displayed value and the trace is pathologically repetitive",
    "15": "proposed value is the angle index 1 rather than the localized visual value 70",
    "24": "proposed value is the angle index 1 rather than the localized visual value 50",
    "28": "source label is too degraded for reliable local edit and ROI validation",
    "36": "trajectory contains a long repetitive self-correction loop",
    "69": "proposed value is the angle index 2 rather than the localized visual value 35",
    "70": "trajectory contains a long repetitive self-correction loop",
    "77": "proposed value is the angle index 2 rather than the localized visual value 60",
    "105": "proposed events mix angle-at-E and angle-EDB semantics rather than one target fact",
    "111": "late proposed event uses angle CED=90 rather than the target angle CAB=90",
    "112": "counterfactual radius 2.7 exceeds the fixed slant length 2.5 and is geometrically invalid",
    "131": "counterfactual angle conflicts with the retained right-angle marker and is not an isolated semantic edit",
    "184": "proposed events mix DAC, OAD, and ODA angle semantics",
    "191": "trajectory is a pathological 25k-token self-correction loop",
    "195": "the value is repeated across AO, OB, and PB and cannot be isolated as one target fact",
    "197": "trajectory is pathologically long and explicitly reports contradictory geometry",
    "259": "middle event reinterprets 16 as a coordinate/segment rather than the same total-GF fact",
    "327": "trajectory contains a long repetitive bearing self-correction loop",
    "441": "changing one coordinate denominator breaks the fixed unit-circle relation",
    "442": "changing one coordinate numerator breaks the fixed unit-circle relation",
    "443": "changing one coordinate numerator breaks the fixed unit-circle relation",
    "444": "changing one coordinate numerator breaks the fixed unit-circle relation",
    "445": "changing one coordinate denominator breaks the fixed unit-circle relation",
    "446": "changing one coordinate numerator breaks the fixed unit-circle relation",
    "447": "changing one coordinate numerator breaks the fixed unit-circle relation",
    "448": "changing one coordinate numerator breaks the fixed unit-circle relation",
    "507": "the y-intercept is encoded by line geometry rather than an isolated editable numeric label",
    "524": "unit radius is distributed across circle geometry and several axis ticks rather than one localized label",
    "527": "proposed pi/5 fact is inconsistent with the visible angular annotation",
    "551": "counterfactual would relabel an axis tick and would not isolate the graph fact",
    "574": "target entity is empty and the graph maximum is not a clean localized edit",
    "622": "numeric target is malformed and does not identify a localized visual fact",
    "657": "trajectory has severe exact-sentence repetition and fails the non-pathological trace check",
    "662": "counterfactual inner radius 15 exceeds the retained outer radius 11",
    "780": "the 60-degree value is repeated and constrained by the equilateral geometry, so a one-label edit is invalid",
}


TARGET_OVERRIDES = {
    "102": "circle O radius",
    "104": "chord CD",
    "136": "tree-shadow length BC",
    "140": "segment OB",
    "161": "triangle-ruler edge length",
    "188": "segment AB",
    "208": "angle JMK",
    "226": "regular-hexagon side length",
    "243": "Phoenix-to-Atlanta additive distance term",
    "254": "right-triangle hypotenuse",
    "350": "second angle of depression",
    "353": "course angle south of east",
    "363": "left flag-post height",
    "423": "speed toward B",
    "425": "included site angle",
    "672": "composite-solid radius",
    "675": "cylinder height",
    "743": "upper-pyramid height term",
    "751": "tube height",
    "752": "prism dimension sqrt(3)x",
    "762": "segment CF",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evidence_type(target: str, context: str) -> str:
    text = f"{target} {context}".lower()
    if "angle" in text or "bearing" in text:
        return "localized_angle_label"
    if "radius" in text:
        return "localized_radius_label"
    if "speed" in text:
        return "localized_speed_label"
    if "intercept" in text or "2x" in text or "150x" in text or "sqrt" in text:
        return "localized_formula_label"
    return "localized_length_label"


def segment_ids_for_events(proposal: dict[str, Any], events: list[dict[str, Any]]) -> list[int]:
    identifiers = []
    for event in events:
        start = int(event["span_start_token"])
        matches = [
            int(segment["segment_id"])
            for segment in proposal["segment_proposals"]
            if int(segment["start_token"]) <= start < int(segment["end_token"])
        ]
        if len(matches) != 1:
            raise RuntimeError(f"Event-to-segment mapping is not unique for base {proposal['base_problem_id']}")
        identifiers.append(matches[0])
    unique = sorted(set(identifiers))
    if len(unique) < 3:
        raise RuntimeError(f"Fewer than three independent event-containing segments for base {proposal['base_problem_id']}")
    return unique


def main() -> None:
    target = OUT / "cohort/work/manual_semantic_reviews_prefix_0189.jsonl"
    if target.exists():
        raise FileExistsError(target)
    proposals = read_jsonl(OUT / "cohort/candidate_proposals.jsonl")
    candidates = [
        row for row in proposals
        if row["proposal_status"] == "manual_review_required" and int(row["screen_order"]) <= CUTOFF
    ]
    expected = {str(row["base_problem_id"]) for row in candidates}
    decisions = ACCEPTED | set(REJECTIONS)
    if expected != decisions:
        raise RuntimeError(
            f"Manual-decision coverage mismatch: missing={sorted(expected-decisions, key=int)} "
            f"extra={sorted(decisions-expected, key=int)}"
        )
    reviews = []
    for proposal in candidates:
        base = str(proposal["base_problem_id"])
        if base in REJECTIONS:
            reviews.append({
                "base_problem_id": base,
                "decision": "REJECT",
                "reason": REJECTIONS[base],
                "attention_used": False,
                "causal_scores_available": False,
            })
            continue
        fact_index = int(proposal["selected_fact_index_proposed"])
        fact = next(row for row in proposal["fact_proposals"] if int(row["fact_index"]) == fact_index)
        events = list(fact["events"])
        if len(events) != 3:
            raise RuntimeError(f"Expected one frozen event trio for base {base}")
        target_evidence = TARGET_OVERRIDES.get(base, str(fact["target"]).strip())
        reviews.append({
            "base_problem_id": base,
            "decision": "ACCEPT",
            "reason": "manual packet review confirmed a genuine multisegment trace, three exact semantically aligned uses, and a localized score-blind edit/ROI candidate",
            "selected_fact_index": fact_index,
            "accepted_event_ids": [int(event["event_id"]) for event in events],
            "reasoning_segment_ids": segment_ids_for_events(proposal, events),
            "target_evidence": target_evidence,
            "evidence_type": evidence_type(target_evidence, str(fact["context"])),
            "trace_is_genuinely_multisegment": True,
            "trace_is_not_pathological_repetition": True,
            "event_spans_exact": True,
            "local_use_readouts_exact": True,
            "events_semantically_independent": True,
            "edit_feasible": True,
            "roi_feasible": True,
            "attention_used": False,
            "causal_scores_available": False,
        })
    if len(reviews) != 108 or sum(row["decision"] == "ACCEPT" for row in reviews) != 71:
        raise RuntimeError("Frozen manual-review counts changed")
    write_jsonl(target, reviews)
    print(json.dumps({
        "cutoff_screen_order": CUTOFF,
        "reviewed": len(reviews),
        "accepted": sum(row["decision"] == "ACCEPT" for row in reviews),
        "rejected": sum(row["decision"] == "REJECT" for row in reviews),
        "attention_used": False,
        "causal_scores_available": False,
        "output": str(target.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
