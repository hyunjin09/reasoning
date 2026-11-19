from scripts.stage7a.build_events import surface_value


def test_binary_foil_does_not_introduce_a_case_confound():
    assert surface_value('yes', 'No') == 'Yes'
    assert surface_value('no', 'YES') == 'NO'
    assert surface_value('yes', 'no') == 'yes'


def test_semantically_equal_value_keeps_exact_native_surface():
    assert surface_value('34400', '34,400') == '34,400'
    assert surface_value('26800', '34,400') == '26,800'
    assert surface_value('94.7680', '94.768') == '94.768'
