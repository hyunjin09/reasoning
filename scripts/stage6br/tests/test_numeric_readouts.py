from decimal import Decimal

from scripts.stage6br.numeric_readouts import literal_decimal, select_numeric_foil


def test_expression_is_not_silently_reduced_to_its_first_number():
    assert literal_decimal('3x - 1') is None
    assert literal_decimal(None) is None


def test_equivalent_spelling_is_not_a_distinct_foil():
    assert select_numeric_foil('5', '5.0', ['5.00', '3x - 1', '8']) == '8'


def test_finite_literal_required():
    assert literal_decimal('NaN') is None
    assert literal_decimal('Infinity') is None
    assert literal_decimal('-2.5') == Decimal('-2.5')


def test_no_alternative_uses_declared_numeric_offset():
    assert select_numeric_foil('5', None, ['5.0', 's - 7']) == '7'
