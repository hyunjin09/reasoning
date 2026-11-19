from scripts.stage10a.edits import variants, replace_fact, gate_b


def test_only_edit_changes_count_without_replacing_source():
    cf, sham, note = variants('So only the blue square is a square.', 1)
    assert cf == 'So only the two blue squares are squares.'
    assert sham == 'So the single blue square is the only square.'
    assert note


def test_arithmetic_changes_only_aggregate_result():
    assert variants("Let's count: 1 (red) + 1 (green) = 2.", 2)[:2] == (
        "Let's count: 1 (red) + 1 (green) = 3.",
        "Let's count: 1 (red) + 1 (green) = two.")


def test_replacement_retains_prefix_and_suffix_exactly():
    assert replace_fact('Earlier two. That is two. ', 13, 25, '') == 'Earlier two.  '


def test_gate_needs_both_directional_controls_and_uncertainty():
    yes = dict(point=.25, ci95=[.01,.5])
    no = dict(point=.25, ci95=[0,.5])
    assert gate_b(yes, yes)
    assert not gate_b(yes, no)
    assert not gate_b(dict(point=.249, ci95=[.1,.5]), yes)
