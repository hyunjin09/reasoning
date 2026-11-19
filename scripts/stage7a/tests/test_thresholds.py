import pytest
from visual_reasoning.stage7a.thresholds import calibrate, family_quantile


def test_confirmation_is_rejected_even_when_its_control_is_missing():
    with pytest.raises(AssertionError, match='Confirmation'):
        family_quantile([dict(split='confirmation', base_id='x', group_id='x')],
                        'value', .95, default=0.)


def test_duplicate_events_do_not_overweight_a_base_and_families_are_collapsed():
    def row(base, group, value):
        return dict(split='discovery', base_id=base, group_id=group, value=value)
    rows = [row('a', 'shared', 2.)]*10 + [row('b', 'shared', 4.), row('c', 'other', 9.)]
    result = family_quantile(rows, 'value', .5, default=0.)
    assert result['family_values'] == {'other': 9., 'shared': 3.}
    assert result['value'] == 6.


def test_similarity_caps_prevent_permissive_shams_from_defining_prior_fill():
    controls = [dict(split='discovery', base_id='a', group_id='a',
                     sham_js=.6, sham_abs_margin_change=10., sham_top50_overlap=.1,
                     irrelevant_abs_claim_effect=.3)]
    values, audit = calibrate(controls)
    assert values['prior_js_max'] == .05
    assert values['prior_margin_max'] == .5
    assert values['prior_top50_min'] == .8
    assert values['error_floor'] >= .6
    assert audit['irrelevant_abs_wrong_effect']['fallback_used']
