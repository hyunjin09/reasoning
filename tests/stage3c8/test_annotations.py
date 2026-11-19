from __future__ import annotations

from visual_reasoning.stage3c8.annotations import annotate_token_sequence, group_lexical_spans


def test_lexical_spans_join_subword_pieces_and_separate_punctuation() -> None:
    spans = group_lexical_spans(
        token_ids=[1, 2, 3, 4, 5],
        token_texts=[" AB", "C", " is", " 12", "."],
    )
    assert [(row["start_position"], row["end_position"], row["decoded_text"]) for row in spans] == [
        (0, 2, " ABC"), (2, 3, " is"), (3, 4, " 12"), (4, 5, ".")
    ]


def test_token_annotations_keep_orthogonal_labels() -> None:
    rows, spans = annotate_token_sequence(
        token_ids=[10, 11, 12, 13],
        token_texts=[" What", " is", " AB", "?"],
        stream="PROMPT_QUESTION",
        visual_entities={"AB"},
        target_entities={"AB"},
        absolute_offset=20,
        target_position=40,
    )
    assert [row["lexical_semantic_class"] for row in rows] == [
        "INTERROGATIVE", "FUNCTION_WORD", "VISUAL_ENTITY", "PUNCTUATION"
    ]
    assert rows[2]["visual_alignment"] == "TARGET_ALIGNED"
    assert rows[-1]["structural_role"] == "QUESTION_FINAL"
    assert rows[0]["absolute_sequence_position"] == 20
    assert rows[0]["distance_to_t_star"] == 20
    assert spans[-1]["decoded_text"] == "?"
