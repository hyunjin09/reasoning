import pytest
from scripts.stage7a.annotation_helpers import readout_offset


def test_repeated_return_value_cannot_silently_select_first_demand():
    text = 'first is 22, second is 4, third is 22.'
    with pytest.raises(ValueError, match='Repeated'):
        readout_offset(text, '22')
    position = readout_offset(text, '22', occurrence=2)
    assert text[:position].endswith('third is ')


def test_literal_decimal_is_not_regex_wildcard():
    assert readout_offset('one is 1x2; next is 1.2', '1.2') == 20
