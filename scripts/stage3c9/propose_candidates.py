#!/usr/bin/env python3
"""Draft score-blind long-horizon event/evidence candidates for manual audit."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from transformers import AutoTokenizer

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3c8.fresh import infer_missing_numeric_facts, propose_counterfactual_numeric_value
from visual_reasoning.stage3c9.annotations import (
    candidate_event_gate,
    canonical_event_trio,
    evidence_terms,
    numeric_fact_event_proposals,
    select_matched_neighbor_span,
    sentence_segments,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def question(row: dict[str, Any]) -> str:
    return str(row.get("question_for_eval") or row.get("query") or "")


def repetition_diagnostic(segments: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = [" ".join(row["span_text"].lower().split()) for row in segments if row["span_text"].strip()]
    counts = Counter(normalized)
    repeated = sum(count for text, count in counts.items() if text and count > 1)
    return {
        "sentence_segment_count": len(normalized),
        "unique_normalized_sentence_fraction": len(counts) / len(normalized) if normalized else 0.0,
        "repeated_sentence_occurrence_fraction": repeated / len(normalized) if normalized else 0.0,
        "maximum_exact_sentence_repetition": max(counts.values(), default=0),
        "manual_independence_review_required": True,
    }


def main() -> None:
    target = OUT / "cohort/candidate_proposals.jsonl"
    if target.exists():
        raise FileExistsError(target)
    pool = read_jsonl(OUT / "prospective_generation/completed_correct_pool.jsonl")
    config = read_json(OUT / "config/stage3c9_config.json")
    rows = load_mathverse_rows(Path(config["dataset_root"]))
    by_example = {str(row["sample_index"]): row for row in rows}
    by_base: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_base.setdefault(str(row["problem_index"]), {})[str(row["problem_version"])] = row
    tokenizer = AutoTokenizer.from_pretrained(config["model_checkpoint"], local_files_only=True)
    proposals = []
    for item in sorted(pool, key=lambda row: int(row["screen_order"])):
        base = str(item["base_problem_id"])
        row = by_example[str(item["example_id"])]
        text_variant = by_base[base].get("Text Dominant") or by_base[base].get("Text Lite")
        facts = infer_missing_numeric_facts(question(text_variant), question(row)) if text_variant else []
        artifact = ROOT / item["artifact_dir"]
        tokens = read_jsonl(artifact / "tokens.jsonl")
        segments = sentence_segments(tokens)
        fact_rows = []
        for fact_index, fact in enumerate(facts):
            counterfactual = propose_counterfactual_numeric_value(fact["original_value"], fact["context"])
            required_terms = evidence_terms(
                target=fact["target"], context=fact["context"], original_value=fact["original_value"]
            )
            all_events = numeric_fact_event_proposals(
                tokens=tokens,
                original_value=fact["original_value"],
                counterfactual_value=counterfactual,
                tokenizer=tokenizer,
                required_evidence_terms=required_terms,
            )
            all_event_spans = [
                (int(event["span_start_token"]), int(event["span_end_token"]))
                for event in all_events
            ]
            for event in all_events:
                neighbor = select_matched_neighbor_span(
                    event_span=(int(event["span_start_token"]), int(event["span_end_token"])),
                    all_event_spans=all_event_spans,
                    readout_token=int(event["local_use_readout"]["token_index"]),
                )
                event["matched_neighbor_span"] = None if neighbor is None else {
                    "start_token": neighbor[0],
                    "end_token": neighbor[1],
                    "span_text": "".join(str(token["decoded_token"]) for token in tokens[neighbor[0]:neighbor[1]]),
                    "same_tokenizer_position_count": neighbor[1] - neighbor[0] == int(event["span_end_token"]) - int(event["span_start_token"]),
                    "selection_used_attention": False,
                }
            neighbor_eligible_events = [
                event for event in all_events
                if event["matched_neighbor_span"] is not None
            ]
            events = canonical_event_trio(neighbor_eligible_events)
            if events:
                final_readout = int(events[-1]["local_use_readout"]["token_index"])
                for event in events:
                    progress = event["span_start_token"] / max(final_readout, 1)
                    event["temporal_location"] = "EARLY" if progress < 1 / 3 else "MIDDLE" if progress < 2 / 3 else "LATE"
                gate = candidate_event_gate(
                    final_readout_token=final_readout,
                    events=events,
                    segment_count=len(segments),
                )
                final_use = events[-1]["local_use_readout"]
            else:
                gate = candidate_event_gate(final_readout_token=0, events=[], segment_count=len(segments))
                final_use = None
            neighbor_controls_available = bool(events) and all(event["matched_neighbor_span"] is not None for event in events)
            fact_rows.append({
                **fact,
                "fact_index": fact_index,
                "counterfactual_value": counterfactual,
                "required_evidence_terms": sorted(required_terms),
                "events": events,
                "all_semantically_aligned_event_count": len(all_events),
                "all_semantically_aligned_event_start_tokens": [int(event["span_start_token"]) for event in all_events],
                "neighbor_eligible_event_count": len(neighbor_eligible_events),
                "canonical_event_rule": "first, midpoint-nearest, last by annotation order",
                "final_use_readout": final_use,
                "eligibility_gate": gate,
                "neighbor_controls_available": neighbor_controls_available,
                "eligible_for_manual_review": bool(gate["eligible_before_edit_roi_validation"] and neighbor_controls_available),
                "event_source": "exact generated references to the static missing visual numeric fact",
                "attention_used": False,
                "causal_scores_available": False,
            })
        eligible = [row for row in fact_rows if row["eligible_for_manual_review"]]
        eligible.sort(
            key=lambda fact: (
                -int(fact["eligibility_gate"]["maximum_event_separation"]),
                -len(fact["events"]),
                int(fact["fact_index"]),
            )
        )
        selected = int(eligible[0]["fact_index"]) if eligible else None
        proposals.append({
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "screen_order": int(item["screen_order"]),
            "variant": str(item["variant"]),
            "source": str(item["source"]),
            "generated_token_count": int(item["generated_token_count"]),
            "generation_path": str((artifact / "generation.json").relative_to(ROOT)),
            "tokens_path": str((artifact / "tokens.jsonl").relative_to(ROOT)),
            "source_image": str(row["image"]),
            "question": question(row),
            "segment_proposals": segments,
            "repetition_diagnostic": repetition_diagnostic(segments),
            "fact_proposals": fact_rows,
            "selected_fact_index_proposed": selected,
            "proposal_status": "manual_review_required" if selected is not None else "reject_no_long_repeated_fact_candidate",
            "selection_used_attention": False,
            "causal_scores_available": False,
        })
    ensure_directory(OUT / "cohort/work")
    write_jsonl(target, proposals)
    write_json(OUT / "cohort/work/candidate_proposal_summary.json", {
        "completed_correct_reviewed": len(proposals),
        "manual_review_required": sum(row["proposal_status"] == "manual_review_required" for row in proposals),
        "no_long_repeated_fact_candidate": sum(row["proposal_status"] != "manual_review_required" for row in proposals),
        "selection_used_attention": False,
        "causal_scores_available": False,
    })
    print(json.dumps(read_json(OUT / "cohort/work/candidate_proposal_summary.json"), indent=2))


if __name__ == "__main__":
    main()
