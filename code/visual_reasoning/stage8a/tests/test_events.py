import pytest

from visual_reasoning.stage8a.events import align_literal_event, divergent_readout


def rows(pieces):
    return [dict(token_index=i, token_id=100+i, decoded_token=s) for i, s in enumerate(pieces)]


def test_repeated_value_uses_reviewed_quote_and_preserves_exact_native_prefix():
    tokens = rows(["x = ", "1", "0", ". Angle M: ", "1", "0", "x."])
    e = align_literal_event(tokens, quote="Angle M: 10x", value="10")
    assert e["prefix_length"] == 4
    assert e["prefix_token_ids"] == [100, 101, 102, 103]
    assert e["evidence_token_ids"] == [104, 105]
    assert e["char_start"] == len("x = 10. Angle M: ")
    assert e["history_text"].endswith("Angle M: ")


def test_reject_subtoken_value_and_ambiguous_quote():
    with pytest.raises(ValueError, match="token boundary"):
        align_literal_event(rows(["value ", "123"]), quote="value 123", value="12")
    with pytest.raises(ValueError, match="ambiguous"):
        align_literal_event(rows(["read ", "1", "; read ", "1"]), quote="read 1", value="1")


def test_unicode_offsets_are_characters_and_empty_pieces_do_not_shift_tokens():
    e = align_literal_event(rows(["√", "", "3", "x"]), quote="√3x", value="3")
    assert e["prefix_length"] == 2 and e["char_start"] == 1
    assert e["evidence_token_ids"] == [102]


def test_common_value_prefix_moves_into_native_history_before_divergent_readout():
    result = divergent_readout([7, 8], [1, 0], [1, 2])
    assert result == dict(prefix_token_ids=[7, 8, 1], common_bridge_ids=[1],
                          original_token_ids=[0], counterfactual_token_ids=[2])
    with pytest.raises(ValueError, match="strict prefix"):
        divergent_readout([7], [1], [1, 2])
    with pytest.raises(ValueError, match="identical"):
        divergent_readout([7], [1, 0], [1, 0])
