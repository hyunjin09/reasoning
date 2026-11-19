import copy

import pytest

from visual_reasoning.stage3c9r.protocol import classify_family, lifetime_summary, shared_partition


def family():
    rows = {}
    for condition in ('O', 'C', 'O_sham', 'C_sham'):
        sign = -1 if condition.startswith('C') else 1
        suppressed = sign * 1.0
        rows[condition] = {
            'execution_id': condition, 'partition': [[0, 10], [10, 11]],
            'native': {'D': sign * (1.02 if 'sham' in condition else 1.4)},
            'suppressed': {'D': suppressed},
            'event_rescue': {'D': sign * 1.2, 'recipient_execution_id': condition},
            'neighbor_rescue': {'D': sign * 1.01, 'recipient_execution_id': condition},
        }
    return rows


def test_every_semantic_and_sham_condition_is_required():
    rows = family()
    del rows['C_sham']
    with pytest.raises(ValueError):
        classify_family(rows)


def test_rejects_mixed_sham_partition_even_when_scores_look_positive():
    rows = family()
    rows['O_sham']['partition'] = [[0, 11]]
    with pytest.raises(ValueError, match='partition'):
        classify_family(rows)


def test_rejects_rescue_from_a_different_recipient_execution():
    rows = family()
    rows['C']['event_rescue']['recipient_execution_id'] = 'old_phase_a'
    with pytest.raises(ValueError, match='recipient'):
        classify_family(rows)


def test_all_gains_share_the_persisted_suppressed_score_and_are_unclipped():
    result = classify_family(family())
    assert result['classification'] == 'C2'
    assert result['source_loss_mean'] == pytest.approx(.4)
    assert result['rescue_gain_mean'] == pytest.approx(.2)
    assert result['median_unclipped_rescue_ratio'] == pytest.approx(.5)
    rows = family()
    rows['O']['event_rescue']['D'] = 2.0
    assert classify_family(rows)['condition_metrics']['O']['rescue_ratio'] == pytest.approx(2.5)


def test_threshold_sensitivity_does_not_change_the_source_sham_rule():
    rows = family()
    rows['O_sham']['native']['D'] = 1.5
    rows['C_sham']['native']['D'] = -1.5
    assert classify_family(rows, effect_floor=.025)['classification'] == 'C0'


def test_right_censored_is_not_short_lived():
    result = lifetime_summary(local_gain=.1, downstream=[], final_gain=None)
    assert result['phenotype'] == 'RIGHT-CENSORED'


def test_distant_negative_readout_does_not_identify_32_token_decay():
    result = lifetime_summary(local_gain=.2, downstream=[(2342, .03)], final_gain=-.09)
    assert result['phenotype'] == 'L-Short'
    assert result['decay_time_resolved_at_16_to_32'] is False
    assert result['first_observed_downstream_distance'] == 2342


def test_native_and_all_rescues_use_union_of_frozen_patch_boundaries():
    event = {'span_start_token': 2052, 'span_end_token': 2055,
             'matched_neighbor_span': {'start_token': 2049, 'end_token': 2052}}
    result = shared_partition(event, end=2056)
    assert result == [(0, 2048), (2048, 2050), (2050, 2051), (2051, 2052),
                      (2052, 2053), (2053, 2054), (2054, 2055), (2055, 2056)]


def test_patch_must_leave_a_downstream_bridge():
    event = {'span_start_token': 10, 'span_end_token': 12,
             'matched_neighbor_span': {'start_token': 8, 'end_token': 10}}
    with pytest.raises(ValueError):
        shared_partition(event, end=12)
