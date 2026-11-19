#!/usr/bin/env python3
"""Freeze the score-blind strict pre-E0 audit for the provisional Stage 3A pool."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_jsonl
from visual_reasoning.stage3a.cohort import validate_strict_pre_e0_audit


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"


# Boundaries were manually selected from token-indexed traces without reading
# any full-cohort Stage 3A scores. E0 is the first semantic span referring to
# the edited visual evidence; E1 is the inclusive end of its first completed
# statement. Existing Stage 2C boundaries are retained where already exact and
# tightened where their older E1 covered only a partial or broader statement.
BOUNDARIES: dict[str, tuple[int, int, str]] = {
    "119": (26, 38, "existing Stage 2C item; prefix ends before 'The figure shows'"),
    "140": (137, 155, "existing Stage 2C item; prefix ends before AO is described"),
    "148": (72, 110, "existing Stage 2C item; prefix ends before ground distances"),
    "155": (47, 206, "E1 tightened to the first explicit person-height statement"),
    "614": (75, 130, "existing Stage 2C graph-shape item"),
    "616": (25, 46, "existing Stage 2C graph-shape item"),
    "753": (223, 547, "E1 revised to include the first complete 6x5x4 dimension statement"),
    "613": (6, 37, "existing Stage 2C graph-shape item"),
    "136": (55, 66, "existing Stage 1B item; target tree/shadow first begins here"),
    "141": (92, 112, "existing Stage 1B item; building-shadow statement"),
    "147": (64, 76, "existing Stage 1B item; benchmark-height statement"),
    "154": (223, 565, "E1 revised to the first explicit BD=0.55 association"),
    "617": (61, 113, "existing Stage 1B graph-shape item"),
    "751": (231, 476, "existing Stage 2C tube-length item"),
    "2": (36, 54, "first 50-degree/angle-1 visual-reference sentence"),
    "3": (225, 625, "first angle-BCD reference; fact value is completed later"),
    "6": (76, 84, "first angle-1 statement after neutral 'Given that'"),
    "9": (71, 576, "first explicit AB-side referent; length is completed later"),
    "16": (62, 84, "first sentence describing the marked 50-degree central angle"),
    "22": (129, 149, "first semantic paraphrase of the marked rhombus angle"),
    "24": (43, 52, "first sentence introducing the marked 50-degree angle"),
    "31": (132, 144, "first angle-2/65-degree statement"),
    "38": (48, 68, "first sentence describing the marked 70-degree angle"),
    "60": (45, 56, "first angle-2/135-degree statement"),
    "67": (35, 46, "first sentence describing the marked 40-degree angle at C"),
    "69": (108, 134, "first sentence jointly naming angle 2 and its 35-degree label"),
    "72": (6, 33, "first statement of the displayed quadrilateral perimeter equation"),
    "74": (92, 112, "first diagram-reference statement for angle 1 and 115 degrees"),
    "75": (73, 91, "first sentence describing the marked 42-degree angle"),
    "76": (120, 134, "first sentence describing the edited 36-degree line angle"),
}


CANDIDATE_OVERRIDES = {
    "9": (
        " AB, whose length is 6",
        " AB, whose length is 7",
        "Makes both candidates grammatical at the first AB referent after 'the base would be'.",
    )
}


def generation_path(example_id: str) -> Path:
    stage1 = ROOT / f"outputs/stage1/discovery/examples/{example_id}/generation.json"
    if stage1.is_file():
        return stage1
    matches = list((OUT / "cohort_expansion").glob(f"**/examples/{example_id}/generation.json"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one generation for example {example_id}, found {matches}")
    return matches[0]


def token_path(generation: Path) -> Path:
    return generation.with_name("tokens.jsonl")


def read_tokens(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    audit_path = OUT / "cohort/strict_pre_e0_audit.jsonl"
    if audit_path.exists():
        raise FileExistsError(f"Frozen audit already exists: {audit_path}")
    rows = []
    for base, (e0, e1, rationale) in BOUNDARIES.items():
        metadata_path = OUT / f"counterfactuals/{base}/edit_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata["manual_validation"]["status"] != "pass":
            raise RuntimeError(f"Provisional base {base} did not pass edit validation")
        generation = generation_path(str(metadata["example_id"]))
        generated = json.loads(generation.read_text(encoding="utf-8"))
        if generated["status"] != "correct" or not generated["complete"]:
            raise RuntimeError(f"Provisional base {base} is not completed-correct")
        tokens = read_tokens(token_path(generation))
        ids = [int(row["token_id"]) for row in tokens]
        if ids != [int(value) for value in generated["generated_token_ids"]]:
            raise RuntimeError(f"Token artifact mismatch for base {base}")
        validated = validate_strict_pre_e0_audit(
            generated_token_ids=ids,
            e0_start_token=e0,
            e1_completion_token=e1,
            evidence_neutral=True,
        )
        if base in CANDIDATE_OVERRIDES:
            candidate_o, candidate_c, candidate_note = CANDIDATE_OVERRIDES[base]
            metadata["candidate_original"] = candidate_o
            metadata["candidate_counterfactual"] = candidate_c
        else:
            candidate_note = "Prospectively defined evidence-matched candidates retained."
        metadata["event"] = {
            "e0_start_token": e0,
            "e1_completion_token": e1,
            "e2_start_token": metadata.get("event", {}).get("e2_start_token") if metadata.get("event") else None,
            "source": "Stage 3A strict pre-E0 manual trace audit before full scoring",
        }
        metadata["prefix_token_ids"] = validated["prefix_token_ids"]
        metadata["prefix_sha256"] = validated["prefix_sha256"]
        metadata["prefix_rule"] = "exact generated y_<E0; E0 token itself is excluded"
        metadata["strict_pre_e0_audit"] = {
            "decision": "ACCEPT",
            "strictly_evidence_neutral": True,
            "causal_scores_inspected_for_decision": False,
            "rationale": rationale,
            "candidate_note": candidate_note,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        e0_e1_text = "".join(row["decoded_token"] for row in tokens[e0 : e1 + 1])
        prefix_text = "".join(row["decoded_token"] for row in tokens[:e0])
        rows.append(
            {
                "base_problem_id": base,
                "example_id": str(metadata["example_id"]),
                "target_evidence": metadata["original_fact"],
                "e0": {
                    "start_token": e0,
                    "boundary_token_text": tokens[e0]["decoded_token"],
                    "semantic_span_through_e1": e0_e1_text,
                },
                "e1_fact_completion": {
                    "end_token_inclusive": e1,
                    "span_text": e0_e1_text,
                },
                "prefix_end_index_exclusive": e0,
                "prefix_sha256": validated["prefix_sha256"],
                "prefix_token_count": validated["prefix_token_count"],
                "prefix_text": prefix_text,
                "strictly_evidence_neutral": True,
                "neutrality_checks": {
                    "target_entity_absent": True,
                    "target_value_absent": True,
                    "target_relation_absent": True,
                    "obvious_paraphrase_absent": True,
                    "partial_fact_leakage_absent": True,
                },
                "original_fact": metadata["original_fact"],
                "counterfactual_fact": metadata["counterfactual_fact"],
                "candidate_original": metadata["candidate_original"],
                "candidate_counterfactual": metadata["candidate_counterfactual"],
                "roi_xyxy": metadata["target_evidence_roi_xyxy"],
                "edit_type": metadata["edit_tier"],
                "edit_validation_status": metadata["manual_validation"]["status"],
                "decision": "ACCEPT",
                "rejection_reason": None,
                "audit_blinded_to_full_causal_scores": True,
                "annotation_rationale": rationale,
            }
        )
    if len(rows) != 30 or len({row["base_problem_id"] for row in rows}) != 30:
        raise RuntimeError("Strict audit must freeze exactly 30 unique provisional bases")
    write_jsonl(audit_path, rows)
    print(json.dumps({"audited": len(rows), "accepted": len(rows), "rejected": 0, "output": str(audit_path)}, indent=2))


if __name__ == "__main__":
    main()
