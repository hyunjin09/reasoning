import pytest
from visual_reasoning.stage8a.annotations import align_reviewed_event


def rows(text):
    return [dict(token_index=i,token_id=i+100,decoded_token=c) for i,c in enumerate(text)]


def test_ambiguous_quote_requires_an_explicit_reviewed_occurrence():
    r=rows("x value7; again value7; done")
    with pytest.raises(ValueError,match="ambiguous"):
        align_reviewed_event(r,quote="value7",value="7")
    first=align_reviewed_event(r,quote="value7",value="7",occurrence=0)
    second=align_reviewed_event(r,quote="value7",value="7",occurrence=1)
    assert first["prefix_length"]==7
    assert second["prefix_length"]==21
    assert second["prefix_token_ids"]==[x["token_id"] for x in r[:21]]
    assert second["quote_match_count_in_reviewed_prefix"]==2
    with pytest.raises(ValueError,match="occurrence"):
        align_reviewed_event(r,quote="value7",value="7",occurrence=2)
