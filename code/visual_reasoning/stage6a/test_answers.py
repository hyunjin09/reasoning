from visual_reasoning.stage6a.answers import score_final_answer, score_condition_answer


def test_reasoning_box_cannot_supply_a_missing_final_answer():
    result=score_final_answer(r'Thought: \boxed{12}</think>Several interpretations remain possible.','12',True)
    assert result['correctness']=='UNRESOLVED'


def test_nested_fraction_and_root_are_equivalent():
    result=score_final_answer(r'</think>\boxed{\frac{\sqrt{30}}{2}}','sqrt(30)/2',True)
    assert result['correctness']=='CORRECT'


def test_cube_polynomial_uses_exact_symbolic_equivalence():
    result=score_final_answer(r'</think>\boxed{x^3+12x^2+48x+64}','(x+4)^3',True)
    assert result['correctness']=='CORRECT'


def test_small_arithmetic_difference_is_preserved():
    assert score_final_answer(r'</think>\boxed{124.87}','124.85',True)['correctness']=='INCORRECT'


def test_categorical_answer_and_abstention_remain_distinct():
    assert score_final_answer('</think>**Answer:** Green','red',True)['correctness']=='INCORRECT'
    assert score_final_answer('</think>I cannot determine the answer without the image.','12',True)['correctness']=='ABSTAINED'


def test_incomplete_trace_and_unsupported_math_are_not_incorrect_answers():
    assert score_final_answer(r'\boxed{12}','12',False)['correctness']=='INCOMPLETE'
    assert score_final_answer(r'</think>\boxed{\sin(30)}','0.5',True)['correctness']=='UNRESOLVED'


def test_only_supported_bounded_expressions_are_evaluated():
    assert score_final_answer(r'</think>\boxed{9^{999999}}','3',True)['correctness']=='UNRESOLVED'


def test_a_prose_guess_is_not_silently_accepted_as_a_categorical_answer():
    result=score_final_answer('</think>It might be green or red.','green',True)
    assert result['correctness']=='UNRESOLVED'


def condition_row(cohort,condition,answer,raw,**fields):
    return dict(cohort=cohort,condition=condition,answer=answer,
        raw_decoded_response='</think>'+raw,complete=True,**fields)


def test_counterfactual_truth_and_original_source_answer_are_distinct():
    row=condition_row('C1','counterfactual','17',r'\boxed{17}',source_answer='15')
    result=score_condition_answer(row)
    assert result['final_answer_correctness']=='CORRECT'
    assert result['source_answer_consistency']=='INCONSISTENT'


def test_no_image_source_match_does_not_establish_image_grounding():
    row=condition_row('C1','no_image','15',r'\boxed{15}')
    result=score_condition_answer(row)
    assert result['source_answer_consistency']=='CONSISTENT'
    assert result['final_answer_correctness']=='UNRESOLVED'
    assert result['local_visual_correctness']=='UNRESOLVED'


def test_unrelated_object_donor_uses_its_reviewed_absence_truth():
    row=condition_row('C3','unrelated','no','yes',source_answer='yes',present=True)
    result=score_condition_answer(row)
    assert result['final_answer_correctness']=='INCORRECT'
    assert result['source_answer_consistency']=='CONSISTENT'
    assert result['object_hallucination_presence']=='REQUIRES_ASSERTION_REVIEW'


def test_occlusion_match_does_not_certify_visible_object_presence():
    row=condition_row('C3','mask','yes','yes',present=True)
    result=score_condition_answer(row)
    assert result['source_answer_consistency']=='CONSISTENT'
    assert result['final_answer_correctness']=='UNRESOLVED'
    assert result['object_hallucination_presence']=='UNRESOLVED_VISIBILITY_AND_ASSERTION'


def test_no_image_abstention_is_preserved_separately_from_source_consistency():
    row=condition_row('C3','no_image','yes','I cannot determine the answer without the image.',present=True)
    result=score_condition_answer(row)
    assert result['final_answer_correctness']=='ABSTAINED'
    assert result['source_answer_consistency']=='ABSTAINED'


def test_document_phone_numbers_are_not_subtraction_expressions():
    result=score_condition_answer(condition_row('C2','AR','212-555-100','202-545-100'))
    assert result['final_answer_correctness']=='UNRESOLVED'


def test_document_dates_are_not_division_expressions():
    result=score_condition_answer(condition_row('C2','AR','1/2/2000','2/4/2000'))
    assert result['final_answer_correctness']=='UNRESOLVED'


def test_document_ranges_are_not_subtraction_expressions():
    result=score_condition_answer(condition_row('C2','AR','3-5','4-6'))
    assert result['final_answer_correctness']=='UNRESOLVED'


def test_literal_document_fields_and_plain_numeric_values_can_be_compared():
    for truth,predicted in [('336-741-1781','336-741-1781'),('3-19-01','3-19-01'),('Senior R&D Chemist','Senior R&D Chemist'),('465.00','465')]:
        assert score_condition_answer(condition_row('C2','AR',truth,predicted))['final_answer_correctness']=='CORRECT'
    assert score_condition_answer(condition_row('C2','AR','15.00','16.00'))['final_answer_correctness']=='INCORRECT'
