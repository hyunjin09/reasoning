from visual_reasoning.stage8b.scoring import extract_final, score_answer, safe_number


def test_only_final_section_is_graded_and_nested_box_is_balanced():
    text=r'Thinking: \boxed{A}</think>Therefore \boxed{\frac{1}{2}}<|im_end|>'
    assert extract_final(text)==r'\frac{1}{2}'
    assert extract_final(r'Thinking \boxed{B}',normal_eos=False) is None


def test_mcq_letter_and_unique_option_value_are_supported():
    row=dict(options=['2','3','4','5'],answer='C')
    assert score_answer(r'</think>\boxed{C}',row)['correct'] is True
    assert score_answer(r'</think>\boxed{4}',row)['correct'] is True
    assert score_answer(r'</think>\boxed{B}',row)['correct'] is False


def test_open_arithmetic_equivalence_and_unresolved_extraction_are_distinct():
    row=dict(options=[],answer='0.5')
    assert score_answer(r'</think>\boxed{\frac{1}{2}}',row)['correct'] is True
    assert score_answer(r'</think>\boxed{0.4}',row)['correct'] is False
    assert score_answer('I am still thinking',row,normal_eos=False)['correct'] is None


def test_numeric_parser_cannot_execute_code_or_unbounded_powers():
    assert safe_number('__import__("os").system("false")') is None
    assert safe_number('9**999999999') is None
    assert safe_number(r'\sqrt{9}/2')==1.5


def test_primary_numeric_scoring_preserves_official_two_decimal_rule():
    row=dict(options=[],answer=r'\frac{1}{3}')
    assert score_answer(r'</think>\boxed{0.3333}',row)['correct'] is True
