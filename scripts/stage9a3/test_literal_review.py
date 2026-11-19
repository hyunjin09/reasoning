from scripts.stage9a3.literal_review import terminal_option


def test_explicit_final_label_with_value_is_format_only():
    assert terminal_option('I counted two. Therefore {D: 1}.')=='D'


def test_internal_answer_does_not_hide_terminal_ambiguity():
    assert terminal_option('Could be {A}; however my answer is unclear.') is None
    assert terminal_option('Answer: {A} or {B}') is None


def test_regular_final_option():
    assert terminal_option('Count steps.\n\n{E}')=='E'
    assert terminal_option('Option A:2. Option B:1.\n\n{B}.')=='B'


def test_no_option_is_not_solved_from_prose():
    assert terminal_option('There are two objects.') is None
