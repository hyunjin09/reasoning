from __future__ import annotations

import hashlib
import json

import pytest

from visual_reasoning.stage3c8.fresh import (
    apply_edit_spec_overrides,
    exact_numeric_candidate,
    infer_missing_numeric_facts,
    materialize_manual_candidate,
    numeric_surface_matches,
    propose_counterfactual_numeric_value,
    validate_frozen_screen_prefix,
)


def test_apply_edit_spec_overrides_is_score_blind_and_preserves_order() -> None:
    specs = [
        {"base_problem_id": "4", "renderer": "rectangle", "roi_xyxy": [1, 2, 3, 4]},
        {"base_problem_id": "5", "renderer": "rectangle", "roi_xyxy": [5, 6, 7, 8]},
    ]
    overrides = [{
        "base_problem_id": "4",
        "changes": {"renderer": "preserve_crossing_strokes", "text_anchor": [9, 1]},
        "reason": "geometry-only review",
        "attention_used": False,
        "carrier_scores_available": False,
    }]
    result = apply_edit_spec_overrides(specs, overrides)
    assert [row["base_problem_id"] for row in result] == ["4", "5"]
    assert result[0]["renderer"] == "preserve_crossing_strokes"
    assert result[0]["text_anchor"] == [9, 1]
    assert result[0]["edit_override_audit"]["reason"] == "geometry-only review"
    assert result[1] == specs[1]


def test_apply_edit_spec_overrides_rejects_causal_outcome_provenance() -> None:
    with pytest.raises(RuntimeError, match="score-blind"):
        apply_edit_spec_overrides(
            [{"base_problem_id": "4", "renderer": "rectangle"}],
            [{
                "base_problem_id": "4",
                "changes": {"renderer": "preserve_crossing_strokes"},
                "reason": "outcome-selected",
                "attention_used": False,
                "carrier_scores_available": True,
            }],
        )


def test_validate_frozen_screen_prefix_requires_every_earlier_outcome_and_audit() -> None:
    screen = [
        {"base_problem_id": "4", "order": 0},
        {"base_problem_id": "7", "order": 1},
        {"base_problem_id": "8", "order": 2},
    ]
    raw = [
        {"base_problem_id": "4", "status": "correct"},
        {"base_problem_id": "7", "status": "wrong"},
        {"base_problem_id": "8", "status": "correct"},
    ]
    audit = [
        {"base_problem_id": "4", "decision": "ACCEPT"},
        {"base_problem_id": "8", "decision": "ACCEPT"},
    ]
    reviewed_edits = [{"base_problem_id": "4"}, {"base_problem_id": "8"}]
    retained = [{"base_problem_id": "4", "screen_order": 0}, {"base_problem_id": "8", "screen_order": 2}]
    result = validate_frozen_screen_prefix(
        screen=screen,
        raw=raw,
        candidate_audit=audit,
        reviewed_edits=reviewed_edits,
        retained=retained,
    )
    assert result == {"cutoff_screen_order": 2, "prefix_size": 3}


def test_validate_frozen_screen_prefix_rejects_a_faster_shard_gap() -> None:
    with pytest.raises(RuntimeError, match="unattempted earlier bases"):
        validate_frozen_screen_prefix(
            screen=[{"base_problem_id": "4", "order": 0}, {"base_problem_id": "7", "order": 1}, {"base_problem_id": "8", "order": 2}],
            raw=[{"base_problem_id": "4", "status": "correct"}, {"base_problem_id": "8", "status": "correct"}],
            candidate_audit=[{"base_problem_id": "4", "decision": "ACCEPT"}, {"base_problem_id": "8", "decision": "ACCEPT"}],
            reviewed_edits=[{"base_problem_id": "4"}, {"base_problem_id": "8"}],
            retained=[{"base_problem_id": "4", "screen_order": 0}, {"base_problem_id": "8", "screen_order": 2}],
        )


def test_infer_missing_numeric_fact_from_text_dominant_variant() -> None:
    text = "As shown, AB is tangent to circle O, if angle A = 36.0, then angle C is equal to ()"
    vision = "As shown, AB is tangent to circle O, then angle C is equal to ()"
    facts = infer_missing_numeric_facts(text, vision)
    assert facts[0]["original_value"] == "36.0"
    assert "angle A" in facts[0]["context"]


def test_choice_numbers_are_not_treated_as_missing_visual_facts() -> None:
    suffix = "\nChoices:\nA:36°\nB:54°"
    facts = infer_missing_numeric_facts("The radius is 12." + suffix, "Find the radius." + suffix)
    assert [row["original_value"] for row in facts] == ["12"]


def test_numeric_surface_matches_keeps_sentence_final_mention() -> None:
    text = "The length AC is 6. Later, A is at (6, 0)."
    matches = numeric_surface_matches(text, {"6", "6.0"})
    assert min(match.start() for match in matches) == text.index("6")


def test_numeric_surface_matches_does_not_take_integer_prefix_of_decimal() -> None:
    text = "The length is 6.0."
    matches = numeric_surface_matches(text, {"6", "6.0"})
    earliest = min(matches, key=lambda match: match.start())
    assert earliest.group(0) == "6.0"


def test_counterfactual_value_does_not_classify_triangle_as_angle() -> None:
    context = "triangle ABC is inscribed in circle O with radius 1.0"
    assert propose_counterfactual_numeric_value("1.0", context) == "3"


def test_counterfactual_value_uses_angle_perturbation_for_angle_word() -> None:
    assert propose_counterfactual_numeric_value("60.0", "if angle BAC = 60.0") == "70"


def test_counterfactual_value_treats_rotation_measure_as_angular() -> None:
    context = "obtained by rotating triangle OAB clockwise around O by 30.0"
    assert propose_counterfactual_numeric_value("30.0", context) == "40"


class _ToyTokenizer:
    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        assert not add_special_tokens
        return {" 60": [60]}[text]

    def decode(self, token_ids: list[int], **_: object) -> str:
        return "".join({50: " 50", 60: " 60", 9: "."}[value] for value in token_ids)


def test_exact_numeric_candidate_preserves_generated_token_boundary() -> None:
    tokens = [
        {"token_id": 1, "decoded_token": "angle"},
        {"token_id": 2, "decoded_token": " is"},
        {"token_id": 50, "decoded_token": " 50"},
        {"token_id": 9, "decoded_token": "."},
    ]
    candidate = exact_numeric_candidate(
        tokens=tokens,
        match_start=len("angle is "),
        match_end=len("angle is 50"),
        counterfactual_value="60",
        tokenizer=_ToyTokenizer(),
    )
    assert candidate["ed_generated_index"] == 2
    assert candidate["history_before_ed_token_ids"] == [1, 2]
    assert candidate["history_before_ed_text"] == "angle is"
    assert candidate["original_divergent_suffix_ids"] == [50]
    assert candidate["original_divergent_suffix_text"] == " 50"
    assert candidate["counterfactual_divergent_suffix_ids"] == [60]
    assert candidate["history_before_ed_sha256"] == hashlib.sha256(
        json.dumps([1, 2], separators=(",", ":")).encode("ascii")
    ).hexdigest()


def test_materialize_manual_candidate_uses_only_selected_exact_fact() -> None:
    proposal = {
        "base_problem_id": "4",
        "example_id": "19",
        "screen_order": 0,
        "numeric_fact_proposals": [
            {
                "fact_index": 0,
                "proposal_status": "manual_review_required",
                "target": "angle A",
                "original_value": "36.0",
                "counterfactual_value": "46",
                "ed_generated_index_proposed": 2,
                "history_before_ed_token_ids": [1, 2],
                "history_before_ed_text": "angle A is",
                "history_before_ed_sha256": "hash",
                "original_divergent_suffix_ids": [36],
                "counterfactual_divergent_suffix_ids": [46],
                "original_divergent_suffix_text": " 36",
                "counterfactual_divergent_suffix_text": " 46",
                "original_candidate_exact_generated_tokens": True,
                "prefix_ends_at_token_boundary": True,
            }
        ],
    }
    review = {
        "base_problem_id": "4",
        "decision": "ACCEPT",
        "selected_fact_index": 0,
        "target_evidence": "angle A",
        "evidence_type": "localized_angle_label",
        "roi_xyxy": [10, 20, 40, 50],
        "font_size": 18,
        "text_anchor": [2, 1],
        "counterfactual_sham_anchor_delta": [-1, 0],
        "render_suffix": "°",
        "semantic_decision_meaningful": True,
        "pre_ed_discriminative_content_absent": True,
        "reason": "clean label",
        "attention_used": False,
        "carrier_scores_available": False,
    }
    row = materialize_manual_candidate(proposal, review)
    assert row["decision"] == "ACCEPT"
    assert row["edit_spec"]["original_value"] == "36"
    assert row["edit_spec"]["counterfactual_sham_anchor_delta"] == [-1, 0]
    assert row["event"]["ed_generated_index"] == 2
    assert row["event"]["original_fact"] == "angle A = 36"
    assert row["event"]["counterfactual_fact"] == "angle A = 46"
    assert row["event"]["manual_audit_status"] == "pass"


def test_materialize_manual_candidate_rejects_non_score_blind_review() -> None:
    proposal = {"base_problem_id": "4", "example_id": "19", "screen_order": 0, "numeric_fact_proposals": []}
    review = {
        "base_problem_id": "4",
        "decision": "REJECT",
        "reason": "not localized",
        "attention_used": True,
        "carrier_scores_available": False,
    }
    with pytest.raises(RuntimeError, match="score-blind"):
        materialize_manual_candidate(proposal, review)
