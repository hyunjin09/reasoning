import pytest

from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement


def test_decimal_edit_is_source_only_and_preserves_literal_format():
    assert numeric_replacement('1.9', lower='0', upper='100') == '1.4'
    assert numeric_replacement('1.5', lower='0', upper='100') == '1.0'
    assert numeric_replacement('+1,000.00', lower='0', upper=None) == '+1,000.05'
    assert numeric_replacement('-2.5', lower='-3', upper='0') == '-2.0'


def test_illegal_replacement_is_unavailable_without_searching_for_another_foil():
    with pytest.raises(ValueError, match='bounds'):
        numeric_replacement('100', lower='0', upper='100')
    with pytest.raises(ValueError, match='bounds'):
        numeric_replacement('0', lower='0', upper='1')


@pytest.mark.parametrize('value', ['approximately1.9', '1.9%', '1e3', 'α', '1,00', 'NaN', ' 1.9'])
def test_nonliteral_or_unsupported_source_format_requires_separate_review(value):
    with pytest.raises(ValueError, match='literal'):
        numeric_replacement(value, lower=None, upper=None)


def test_source_truth_itself_must_satisfy_independent_bounds():
    with pytest.raises(ValueError, match='bounds'):
        numeric_replacement('1.9', lower='2', upper='3')
