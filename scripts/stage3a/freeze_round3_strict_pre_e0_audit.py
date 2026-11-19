#!/usr/bin/env python3
"""Freeze manually audited round-3 E0 boundaries and the final primary cohort."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_jsonl
from visual_reasoning.stage3a.cohort import validate_strict_pre_e0_audit


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"


# Each boundary is manually selected from a token-indexed completed-correct
# baseline trace before any full-cohort causal score exists. E1 is inclusive.
# Candidate strings are adjusted only for grammar at the first E0 referent.
BOUNDARIES: dict[str, dict] = {
    "78": {
        "e0": 113,
        "e1": 120,
        "candidate_original": " angle at C is 70 degrees",
        "candidate_counterfactual": " angle at C is 40 degrees",
        "rationale": "first target-evidence referent is 'angle at C'; the exact prefix ends before 'angle'",
    },
    "98": {
        "e0": 50,
        "e1": 60,
        "candidate_original": " The angle at A is given as 50 degrees",
        "candidate_counterfactual": " The angle at A is given as 40 degrees",
        "rationale": "first target-evidence span begins with 'The angle at A'; the exact prefix excludes its determiner",
    },
    "106": {
        "e0": 101,
        "e1": 113,
        "candidate_original": " Then there's angle AOD given as 136 degrees",
        "candidate_counterfactual": " Then there's angle AOD given as 108 degrees",
        "rationale": "first AOD evidence span begins with 'Then'; the prefix contains no AOD entity, value, or relation",
    },
    "125": {
        "e0": 22,
        "e1": 58,
        "candidate_original": " The sector radius is 30 cm",
        "candidate_counterfactual": " The sector radius is 15 cm",
        "rationale": "first visual-sector referent begins with 'There's a diagram'; the prior radius mention is the unknown cone-base answer, not the edited sector fact",
    },
    "79": {
        "e0": 10,
        "e1": 20,
        "candidate_original": " AB + BC + CD + DA = 32",
        "candidate_counterfactual": " AB + BC + CD + DA = 20",
        "rationale": "first target entity is AB in the displayed perimeter equation; the prefix ends after the neutral phrase 'The problem says that'",
    },
    "80": {
        "e0": 177,
        "e1": 202,
        "candidate_original": " height of the cylinder is 5",
        "candidate_counterfactual": " height of the cylinder is 9",
        "rationale": "first height referent begins at token 177; earlier text names the cylinder and circumference but not the edited height relation or value",
    },
    "83": {
        "e0": 112,
        "e1": 129,
        "candidate_original": " The angle at the center, angle AOB, is given as 100 degrees",
        "candidate_counterfactual": " The angle at the center, angle AOB, is given as 120 degrees",
        "rationale": "first AOB target span begins at token 112; earlier central-angle theorem language is generic and contains neither AOB nor its value",
    },
    "93": {
        "e0": 42,
        "e1": 58,
        "candidate_original": " the marked angle OBC is 40 degrees",
        "candidate_counterfactual": " the marked angle OBC is 35 degrees",
        "rationale": "first reference to the edited 40-degree mark begins at token 42; the baseline initially misnames it as central BOC, so the frozen fact probes retain the visually correct OBC entity",
    },
    "96": {
        "e0": 125,
        "e1": 141,
        "candidate_original": " The angle at the center, angle AOB, is given as 40 degrees",
        "candidate_counterfactual": " The angle at the center, angle AOB, is given as 100 degrees",
        "rationale": "first AOB target span begins at token 125; prior theorem and diagram-description text contains no AOB value",
    },
    "101": {
        "e0": 95,
        "e1": 112,
        "candidate_original": " The angle at the center, angle AOC, is given as 126 degrees",
        "candidate_counterfactual": " The angle at the center, angle AOC, is given as 106 degrees",
        "rationale": "first AOC target span begins at token 95; the preceding diagram inventory is evidence-neutral",
    },
    "103": {
        "e0": 41,
        "e1": 54,
        "candidate_original": " the marked angle ABC is 130 degrees",
        "candidate_counterfactual": " the marked angle ABC is 125 degrees",
        "rationale": "first reference to the edited angle-at-B mark begins at token 41; the prefix contains only the circle/point inventory",
    },
    "109": {
        "e0": 74,
        "e1": 83,
        "candidate_original": " the marked exterior angle adjacent to alpha is 130 degrees",
        "candidate_counterfactual": " the marked exterior angle adjacent to alpha is 120 degrees",
        "original_fact": "the marked exterior angle adjacent to alpha is 130 degrees",
        "counterfactual_fact": "the marked exterior angle adjacent to alpha is 120 degrees",
        "rationale": "first reference to the edited numeric mark begins at token 74; manual image review corrects the screening shorthand that had called the adjacent exterior mark alpha itself",
    },
    "113": {
        "e0": 908,
        "e1": 918,
        "candidate_original": " there's a marked angle CEB of 110 degrees",
        "candidate_counterfactual": " there's a marked angle CEB of 90 degrees",
        "rationale": "first explicit target angle/value/entity span begins at token 908 after a long evidence-neutral derivation; no E or 110-degree fact appears earlier",
    },
    "120": {
        "e0": 18,
        "e1": 29,
        "candidate_original": " The cone height is 4 cm",
        "candidate_counterfactual": " The cone height is 3 cm",
        "rationale": "first cone-height evidence span begins with 'The figure shows'; the prefix states only the unknown task objective",
    },
    "128": {
        "e0": 27,
        "e1": 36,
        "candidate_original": " The angle at O is 120 degrees",
        "candidate_counterfactual": " The angle at O is 90 degrees",
        "rationale": "first edited sector-angle referent begins at token 27; the prior OA/OB length fact is unchanged and does not leak the target angle",
    },
    "100": {
        "e0": 95,
        "e1": 108,
        "candidate_original": " The angle at O, angle COE, is 30 degrees",
        "candidate_counterfactual": " The angle at O, angle COE, is 40 degrees",
        "original_fact": "central angle COE is 30 degrees",
        "counterfactual_fact": "central angle COE is 40 degrees",
        "rationale": "first COE target span begins at token 95; manual image/trace review corrects the screening shorthand COA to the marked collinear-ray entity COE",
    },
    "107": {
        "e0": 52,
        "e1": 68,
        "candidate_original": " The angle at O, which is angle BOD, is 130 degrees",
        "candidate_counterfactual": " The angle at O, which is angle BOD, is 120 degrees",
        "rationale": "first BOD target span begins at token 52; the preceding circle/point inventory contains no target relation or value",
    },
    "118": {
        "e0": 6,
        "e1": 181,
        "candidate_original": " The semicircle radius is 10",
        "candidate_counterfactual": " The semicircle radius is 8",
        "original_fact": "the semicircle sector radius is 10",
        "counterfactual_fact": "the semicircle sector radius is 8",
        "rationale": "first semicircle referent begins at token 6; manual image review corrects the screening shorthand diameter to the bracketed endpoint-to-center radius",
    },
    "126": {
        "e0": 75,
        "e1": 157,
        "candidate_original": " slant height, and its displayed value is 10",
        "candidate_counterfactual": " slant height, and its displayed value is 16",
        "rationale": "first slant-height relation begins at the tokenized word 'slant' at 75; the prefix ends after generic 'l is the' and contains no target value",
    },
}


# Populate only when a completed-correct trace fails the strict prefix audit.
REJECTIONS: dict[str, str] = {}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def generation_path(example_id: str) -> Path:
    matches = list((OUT / "cohort_expansion/round3").glob(f"**/examples/{example_id}/generation.json"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one round-3 generation for example {example_id}, found {matches}")
    return matches[0]


def token_rows(generation: Path) -> list[dict]:
    return read_jsonl(generation.with_name("tokens.jsonl"))


def main() -> None:
    provisional_path = OUT / "cohort/strict_pre_e0_audit.jsonl"
    provisional = read_jsonl(provisional_path)
    if len(provisional) != 30 or any(row["decision"] != "ACCEPT" for row in provisional):
        raise RuntimeError("Expected the frozen 30-base provisional strict audit")
    snapshot = OUT / "cohort/strict_pre_e0_audit_provisional30.jsonl"
    if snapshot.is_file() and read_jsonl(snapshot) != provisional:
        raise RuntimeError("Existing provisional-30 snapshot differs from the current audit")
    if not snapshot.is_file():
        write_jsonl(snapshot, provisional)

    outcomes = read_jsonl(OUT / "cohort_expansion/round3/raw_outcome_manifest.jsonl")
    completed = [row for row in outcomes if row["status"] == "correct" and row["complete"]]
    completed_bases = {str(row["base_problem_id"]) for row in completed}
    unannotated = sorted(completed_bases - set(BOUNDARIES) - set(REJECTIONS), key=int)
    stale = sorted((set(BOUNDARIES) | set(REJECTIONS)) - completed_bases, key=int)
    if unannotated or stale:
        raise RuntimeError(f"Manual audit table mismatch; unannotated={unannotated}, stale={stale}")

    round3_rows: list[dict] = []
    accepted: list[dict] = []
    for outcome in completed:
        base = str(outcome["base_problem_id"])
        metadata_path = OUT / f"counterfactuals/{base}/edit_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if base in REJECTIONS:
            round3_rows.append(
                {
                    "base_problem_id": base,
                    "example_id": str(outcome["example_id"]),
                    "target_evidence": metadata["original_fact"],
                    "decision": "REJECT",
                    "rejection_reason": REJECTIONS[base],
                    "audit_blinded_to_full_causal_scores": True,
                }
            )
            continue
        boundary = BOUNDARIES[base]
        generation = generation_path(str(outcome["example_id"]))
        generated = json.loads(generation.read_text(encoding="utf-8"))
        tokens = token_rows(generation)
        ids = [int(row["token_id"]) for row in tokens]
        if ids != [int(value) for value in generated["generated_token_ids"]]:
            raise RuntimeError(f"Token artifact mismatch for base {base}")
        validated = validate_strict_pre_e0_audit(
            generated_token_ids=ids,
            e0_start_token=int(boundary["e0"]),
            e1_completion_token=int(boundary["e1"]),
            evidence_neutral=True,
        )
        e0 = int(boundary["e0"])
        e1 = int(boundary["e1"])
        if "original_fact" in boundary:
            metadata["fact_label_correction"] = {
                "previous_original_fact": metadata["original_fact"],
                "previous_counterfactual_fact": metadata["counterfactual_fact"],
                "reason": "score-blind strict E0 audit corrected semantic shorthand against the manually validated image",
                "causal_scores_available": False,
            }
            metadata["original_fact"] = boundary["original_fact"]
            metadata["counterfactual_fact"] = boundary["counterfactual_fact"]
        metadata["candidate_original"] = boundary["candidate_original"]
        metadata["candidate_counterfactual"] = boundary["candidate_counterfactual"]
        metadata["event"] = {
            "e0_start_token": e0,
            "e1_completion_token": e1,
            "e2_start_token": None,
            "source": "Stage 3A strict pre-E0 manual trace audit before full scoring",
        }
        metadata["prefix_token_ids"] = validated["prefix_token_ids"]
        metadata["prefix_sha256"] = validated["prefix_sha256"]
        metadata["prefix_rule"] = "exact generated y_<E0; E0 token itself is excluded"
        metadata["strict_pre_e0_audit"] = {
            "decision": "ACCEPT",
            "strictly_evidence_neutral": True,
            "causal_scores_inspected_for_decision": False,
            "rationale": boundary["rationale"],
        }
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        span_text = "".join(row["decoded_token"] for row in tokens[e0 : e1 + 1])
        audit = {
            "base_problem_id": base,
            "example_id": str(outcome["example_id"]),
            "target_evidence": metadata["original_fact"],
            "e0": {
                "start_token": e0,
                "boundary_token_text": tokens[e0]["decoded_token"],
                "semantic_span_through_e1": span_text,
            },
            "e1_fact_completion": {"end_token_inclusive": e1, "span_text": span_text},
            "prefix_end_index_exclusive": e0,
            "prefix_sha256": validated["prefix_sha256"],
            "prefix_token_count": validated["prefix_token_count"],
            "prefix_text": "".join(row["decoded_token"] for row in tokens[:e0]),
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
            "annotation_rationale": boundary["rationale"],
        }
        round3_rows.append(audit)
        accepted.append(audit)

    # Preserve manifest order and cap additions at 20 so the final cohort is at most 50.
    order = {
        str(row["base_problem_id"]): index
        for index, row in enumerate(read_jsonl(OUT / "cohort/round3_valid_generation_manifest.jsonl"))
    }
    accepted.sort(key=lambda row: order[row["base_problem_id"]])
    if len(accepted) < 10:
        raise RuntimeError(f"Only {len(accepted)} valid round-3 additions; further expansion is required")
    selected_bases = {row["base_problem_id"] for row in accepted[:20]}
    for row in round3_rows:
        row["included_in_final_primary_cohort"] = row.get("decision") == "ACCEPT" and row["base_problem_id"] in selected_bases
        if row.get("decision") == "ACCEPT" and row["base_problem_id"] not in selected_bases:
            row["primary_exclusion_reason"] = "prospective 50-base maximum reached in frozen screen order"
    selected = [row for row in accepted if row["base_problem_id"] in selected_bases]
    final_audit = provisional + selected
    write_jsonl(OUT / "cohort/round3_strict_pre_e0_audit.jsonl", round3_rows)
    write_jsonl(provisional_path, final_audit)
    print(
        json.dumps(
            {
                "round3_completed_correct_audited": len(completed),
                "round3_accepted": len(accepted),
                "round3_rejected": len(completed) - len(accepted),
                "round3_selected": len(selected),
                "final_primary_candidate_count": len(final_audit),
                "selected_round3_bases": [row["base_problem_id"] for row in selected],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
