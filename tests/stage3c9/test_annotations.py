from __future__ import annotations

import pytest

from visual_reasoning.stage3c9.annotations import (
    anchor_span_before_readout,
    canonical_event_trio,
    evidence_terms,
    freeze_semantic_review,
    numeric_fact_event_proposals,
    candidate_event_gate,
    select_matched_neighbor_span,
    sentence_segments,
)


def _tokens(pieces: list[str]) -> list[dict]:
    return [{"token_index": i, "token_id": i + 1, "decoded_token": piece} for i, piece in enumerate(pieces)]


def test_anchor_span_is_post_boundary_and_strictly_before_readout() -> None:
    tokens = _tokens(["Earlier", ".", " Now", " consider", " AB", " =", " 3", "."])
    assert anchor_span_before_readout(tokens, 6, maximum_positions=8) == (2, 5)


def test_anchor_span_truncates_to_eight_tokenizer_positions() -> None:
    tokens = _tokens([f" t{i}" for i in range(12)])
    assert anchor_span_before_readout(tokens, 11, maximum_positions=8) == (2, 10)


def test_sentence_segments_cover_trace_without_overlap() -> None:
    tokens = _tokens(["First", ".", " Then", " solve", ".", " Finally", " answer", "."])
    result = sentence_segments(tokens)
    assert [(row["start_token"], row["end_token"]) for row in result] == [(0, 2), (2, 5), (5, 8)]
    assert "Then solve" in result[1]["span_text"]


def test_candidate_event_gate_requires_three_events_and_separation() -> None:
    events = [
        {"span_start_token": 10, "span_end_token": 12, "local_use_readout": {"token_index": 13}},
        {"span_start_token": 40, "span_end_token": 42, "local_use_readout": {"token_index": 43}},
        {"span_start_token": 170, "span_end_token": 172, "local_use_readout": {"token_index": 173}},
    ]
    result = candidate_event_gate(final_readout_token=180, events=events, segment_count=4)
    assert result["eligible_before_edit_roi_validation"]
    assert result["maximum_event_separation"] == 160
    assert result["has_event_before_final_quarter"]
    assert result["all_events_support_W8"]
    assert not candidate_event_gate(final_readout_token=180, events=events[:2], segment_count=4)["eligible_before_edit_roi_validation"]


def test_candidate_event_gate_requires_w8_to_fit_before_every_event() -> None:
    events = [
        {"span_start_token": 7, "span_end_token": 9, "local_use_readout": {"token_index": 10}},
        {"span_start_token": 40, "span_end_token": 42, "local_use_readout": {"token_index": 43}},
        {"span_start_token": 170, "span_end_token": 172, "local_use_readout": {"token_index": 173}},
    ]
    result = candidate_event_gate(final_readout_token=180, events=events, segment_count=4)
    assert not result["all_events_support_W8"]
    assert not result["eligible_before_edit_roi_validation"]


def test_candidate_event_gate_requires_local_readout_within_1_to_32_tokens() -> None:
    events = [
        {"span_start_token": 10, "span_end_token": 12, "local_use_readout": {"token_index": 12}},
        {"span_start_token": 40, "span_end_token": 42, "local_use_readout": {"token_index": 75}},
        {"span_start_token": 170, "span_end_token": 172, "local_use_readout": {"token_index": 173}},
    ]
    result = candidate_event_gate(final_readout_token=180, events=events, segment_count=4)
    assert result["local_readout_distances"] == [0, 33, 1]
    assert not result["all_local_readouts_1_to_32_after_span"]
    assert not result["eligible_before_edit_roi_validation"]


def test_candidate_event_gate_uses_final_readout_not_total_generation_length() -> None:
    events = [
        {"span_start_token": 10, "span_end_token": 12, "local_use_readout": {"token_index": 13}},
        {"span_start_token": 40, "span_end_token": 42, "local_use_readout": {"token_index": 43}},
        {"span_start_token": 80, "span_end_token": 82, "local_use_readout": {"token_index": 83}},
    ]
    result = candidate_event_gate(final_readout_token=120, events=events, segment_count=3)
    assert not result["long_enough_before_final_readout"]
    assert not result["eligible_before_edit_roi_validation"]


class _ToyTokenizer:
    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        assert not add_special_tokens
        return {" 5": [50]}[text]

    def decode(self, token_ids: list[int], **_: object) -> str:
        pieces = {1: " AB", 2: " =", 3: " 3", 4: ".", 50: " 5"}
        return "".join(pieces[token] for token in token_ids)


def test_numeric_fact_events_are_exact_and_deduplicated_by_readout_token() -> None:
    tokens = [
        {"token_index": index, "token_id": token, "decoded_token": {1: " AB", 2: " =", 3: " 3", 4: "."}[token]}
        for index, token in enumerate([1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3])
    ]
    events = numeric_fact_event_proposals(
        tokens=tokens,
        original_value="3",
        counterfactual_value="5",
        tokenizer=_ToyTokenizer(),
        required_evidence_terms={"ab"},
    )
    assert [row["local_use_readout"]["token_index"] for row in events] == [2, 6, 10]
    assert all(row["span_text"] == " AB" for row in events)
    assert all(row["local_use_readout"]["counterfactual_divergent_suffix_text"] == " 5" for row in events)


def test_numeric_fact_events_require_local_semantic_alignment() -> None:
    token_ids = [1, 2, 3, 4, 9, 2, 3]
    pieces = {1: " AB", 2: " =", 3: " 3", 4: ".", 9: " CD"}
    tokens = [
        {"token_index": index, "token_id": token, "decoded_token": pieces[token]}
        for index, token in enumerate(token_ids)
    ]
    events = numeric_fact_event_proposals(
        tokens=tokens,
        original_value="3",
        counterfactual_value="5",
        tokenizer=_ToyTokenizer(),
        required_evidence_terms={"ab"},
    )
    assert [row["local_use_readout"]["token_index"] for row in events] == [2]


def test_evidence_terms_remove_numbers_and_generic_connectives() -> None:
    assert evidence_terms(target="if angle BAC =", context="the shown angle BAC is 60", original_value="60") == {"angle", "bac"}


def test_neighbor_span_is_same_length_nearby_nonoverlapping_and_deterministic() -> None:
    assert select_matched_neighbor_span(
        event_span=(10, 12),
        all_event_spans=[(10, 12)],
        readout_token=20,
    ) == (8, 10)
    assert select_matched_neighbor_span(
        event_span=(10, 12),
        all_event_spans=[(8, 10), (10, 12)],
        readout_token=20,
    ) == (12, 14)


def test_neighbor_span_returns_none_when_no_valid_span_within_eight_tokens() -> None:
    assert select_matched_neighbor_span(
        event_span=(1, 3),
        all_event_spans=[(0, 5)],
        readout_token=5,
    ) is None


def test_neighbor_span_leaves_a_downstream_bridge_before_readout() -> None:
    assert select_matched_neighbor_span(
        event_span=(3, 5),
        all_event_spans=[(0, 3), (3, 5)],
        readout_token=7,
        maximum_start_distance=2,
    ) is None


def _review_proposal() -> dict:
    events = []
    for event_id, position in enumerate((20, 60, 170)):
        events.append({
            "event_id": event_id,
            "span_start_token": position,
            "span_end_token": position + 2,
            "span_text": " AB =",
            "event_role": "VISUAL_FACT_REFERENCE",
            "evidence_relation": "SAME_TARGET_EVIDENCE",
            "local_use_readout": {"token_index": position + 3},
            "matched_neighbor_span": {"start_token": position - 2, "end_token": position},
        })
    return {
        "base_problem_id": "7",
        "example_id": "34",
        "screen_order": 5,
        "segment_proposals": [
            {"segment_id": i, "start_token": i * 60, "end_token": (i + 1) * 60, "span_text": f"part {i}"}
            for i in range(3)
        ],
        "fact_proposals": [{
            "fact_index": 0,
            "target": "AB",
            "context": "AB = 3",
            "original_value": "3",
            "counterfactual_value": "5",
            "events": events,
            "final_use_readout": events[-1]["local_use_readout"],
            "eligible_for_manual_review": True,
        }],
    }


def test_freeze_semantic_review_requires_score_blind_exact_independent_events() -> None:
    review = {
        "base_problem_id": "7",
        "decision": "ACCEPT",
        "selected_fact_index": 0,
        "accepted_event_ids": [0, 1, 2],
        "reasoning_segment_ids": [0, 1, 2],
        "target_evidence": "AB = 3",
        "evidence_type": "localized_length_label",
        "trace_is_genuinely_multisegment": True,
        "trace_is_not_pathological_repetition": True,
        "event_spans_exact": True,
        "local_use_readouts_exact": True,
        "events_semantically_independent": True,
        "edit_feasible": True,
        "roi_feasible": True,
        "attention_used": False,
        "causal_scores_available": False,
        "reason": "clean repeated uses",
    }
    frozen = freeze_semantic_review(_review_proposal(), review)
    assert frozen["decision"] == "ACCEPT"
    assert len(frozen["events"]) == 3
    assert len(frozen["reasoning_segments"]) == 3
    assert frozen["final_use_readout"]["token_index"] == 173


def test_freeze_semantic_review_rejects_effect_aware_or_repetitive_acceptance() -> None:
    review = {
        "base_problem_id": "7",
        "decision": "ACCEPT",
        "selected_fact_index": 0,
        "accepted_event_ids": [0, 1, 2],
        "reasoning_segment_ids": [0, 1, 2],
        "target_evidence": "AB = 3",
        "evidence_type": "localized_length_label",
        "trace_is_genuinely_multisegment": True,
        "trace_is_not_pathological_repetition": False,
        "event_spans_exact": True,
        "local_use_readouts_exact": True,
        "events_semantically_independent": True,
        "edit_feasible": True,
        "roi_feasible": True,
        "attention_used": False,
        "causal_scores_available": False,
    }
    with pytest.raises(RuntimeError):
        freeze_semantic_review(_review_proposal(), review)


def test_canonical_event_trio_is_first_midpoint_nearest_and_last() -> None:
    events = [
        {"event_id": index, "span_start_token": position}
        for index, position in enumerate((10, 20, 38, 70))
    ]
    assert [row["event_id"] for row in canonical_event_trio(events)] == [0, 2, 3]
    assert canonical_event_trio(events[:2]) == []
