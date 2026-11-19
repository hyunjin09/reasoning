from scripts.stage6br.direct_claims import claim_checks


def test_year_arithmetic_is_not_a_table_cell_value():
    claim = {'source_id': 'T', 'role_start': 0, 'role_end': 4, 'value_start': 7, 'value_end': 8, 'value_text': '1'}
    source = {'entity': '2014 employee count', 'current_image_source_identity_mapped': True}
    assert 'NUMERIC_ALIAS_REQUIRES_CELL_REVIEW' in claim_checks('2014 = 1 year.', claim, source)


def test_radius_diameter_conversion_needs_a_separate_binding_review():
    claim = {'source_id': 'A', 'role_start': 0, 'role_end': 8, 'value_start': 12, 'value_end': 14, 'value_text': '12'}
    source = {'entity': 'cylinder radius', 'current_image_source_identity_mapped': True}
    assert 'ROLE_CONVERSION_REQUIRES_REVIEW' in claim_checks('diameter is 12.', claim, source)


def test_wrong_value_is_not_filtered_out_of_a_clear_source_assertion():
    claim = {'source_id': 'A', 'role_start': 0, 'role_end': 6, 'value_start': 10, 'value_end': 11, 'value_text': '7'}
    source = {'entity': 'cylinder radius', 'truth_value': '6', 'current_image_source_identity_mapped': True}
    assert claim_checks('radius is 7.', claim, source) == []


def test_hypothetical_assertion_remains_unresolved():
    claim = {'source_id': 'A', 'role_start': 10, 'role_end': 16, 'value_start': 20, 'value_end': 21, 'value_text': '7'}
    source = {'entity': 'cylinder radius', 'current_image_source_identity_mapped': True}
    assert 'HYPOTHETICAL_OR_NEGATED_CONTEXT' in claim_checks('Maybe the radius is 7.', claim, source)
