from scripts.stage6br.local_assertions import local_assertion_checks


def check(text, role, value, entity):
    a = text.index(role)
    b = text.index(value, a + len(role))
    return local_assertion_checks(text, {'role_start': a, 'role_end': a+len(role),
        'value_start': b, 'value_end': b+len(value)}, {'entity': entity})


def test_angle_between_sides_does_not_assert_a_side_length():
    assert check('The angle between the base and slanted side is 60°.', 'slanted side', '60', 'slanted side length')


def test_expression_prefix_is_not_a_literal_measurement():
    assert check('The total height is 5h = 6.', 'total height', '5', 'stack height')
    assert check('The length BC is 5 - (-4) = 9.', 'BC', '5', 'vertical BC length')


def test_unit_does_not_hide_an_arithmetic_operand():
    assert check('Top base: 10 cm × 8 cm = 80.', 'Top base', '10', 'trapezoid top base')


def test_hypothetical_examples_are_not_native_source_assertions():
    assert check("Let's say grilled steak is $14.", 'grilled steak', '14', 'grilled steak price')


def test_named_literal_assertion_is_retained_even_if_value_is_wrong():
    assert check('The length of BC is 7 cm.', 'BC', '7', 'vertical BC length') == []
    assert check('BC is 7 (vertical).', 'BC', '7', 'vertical BC length') == []


def test_coordinate_and_function_prefix_are_not_scalar_claims():
    assert check('Vector AB is (4,0).', 'AB', '4', 'length AB')
    assert check('AC = 3(3) - 1 = 8.', 'AC', '3', 'side AC expression')


def test_frequency_threshold_is_not_a_cell_lookup():
    assert check('More than 2 runs is 3 and 4.', '2 runs', '3', 'two-run frequency')


def test_last_operand_is_not_the_left_hand_quantity():
    assert check('AE = AD - ED = 4.', 'ED', '4', 'shaded lower base ED')
    assert check('sum = AB + BC = 8.', 'BC', '8', 'vertical BC length')
    assert check('s1 = AB = 16.', 'AB', '16', 'pentagon edge AB') == []
