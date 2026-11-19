from visual_reasoning.stage8b.v2_protocol import generation_parameters, completion_status
from visual_reasoning.stage8b.v2_scoring import extract_answer, score_answer


def test_capped_answer_is_scored_without_think_boundary():
    text = r'Working through the diagram. The answer is \boxed{\frac{1}{2}}'
    answer = score_answer(text, dict(options=[], answer='0.5'))
    assert answer['correct'] is True
    start, end = answer['span']
    assert text[start:end] == r'\frac{1}{2}'
    state = completion_status(text, normal_eos=False, at_length_cap=True, tokens=40960)
    assert state['completion'] == 'capped without final section'
    assert state['has_think_end'] is False


def test_final_section_overrides_earlier_answer_and_span_is_original():
    text = r'\boxed{4}</think>Final answer: \boxed{3}<|im_end|>'
    result = score_answer(text, dict(options=[], answer='3'))
    assert result['correct'] is True
    assert result['scope'] == 'post_think'
    assert text[slice(*result['span'])] == '3'


def test_no_extraction_from_arbitrary_last_number():
    result = extract_answer('We might use 17 or 23. Still checking the triangle.', [])
    assert result['extracted'] is None
    assert result['status'] == 'needs_blind_extraction'


def test_qwen_tolerance_replaces_old_two_decimal_rounding():
    row = dict(options=[], answer='1/3')
    assert score_answer(r'\boxed{0.3333}', row)['correct'] is False
    assert score_answer(r'\boxed{0.3333333333}', row)['correct'] is True


def test_unambiguous_option_and_explicit_answer_without_box():
    row = dict(options=['red', 'green', 'blue'], answer='B')
    assert score_answer('The correct answer is (B).', row)['correct'] is True
    assert score_answer('Final answer: 12', dict(options=[], answer='13'))['correct'] is False


def test_no_eval_and_no_completion_guess():
    result = score_answer(r'\boxed{__import__("os").system("false")}', dict(options=[], answer='1'))
    assert result['correct'] is None
    assert completion_status('text', normal_eos=False, at_length_cap=False, tokens=9)['completion'] == 'other abnormal stop'
    assert completion_status('</think>3', normal_eos=True, at_length_cap=False, tokens=9)['completion'] == 'normal completed'


def test_temperature_and_penalties_are_explicit():
    assert generation_parameters() == dict(do_sample=True, temperature=1.0, top_p=0.95, top_k=20, repetition_penalty=1.0)
