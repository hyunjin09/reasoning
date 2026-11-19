from visual_reasoning.stage6a.readouts import readout_matches


def test_sentence_period_is_not_decimal_continuation():
    text = "CQ is 5, and CQ' is 15. The ratio is 3."
    matches = readout_matches(text, "15")
    assert [(m.start(), m.end()) for m in matches] == [(text.index("15"), text.index("15") + 2)]


def test_readout_does_not_match_inside_another_number():
    text = "115 15.5 .15 0.15 15 15."
    assert [m.start() for m in readout_matches(text, "15")] == [18, 21]


def test_decimal_readout_and_repeated_occurrences():
    text = "13.80, 13.8, and 13.8."
    assert [m.group() for m in readout_matches(text, "13.8")] == ["13.8", "13.8"]
