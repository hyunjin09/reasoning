from types import SimpleNamespace
import numpy as np
import pytest
from visual_reasoning.stage7a import passive
from visual_reasoning.stage7a.metrics import passive_control_distances
from visual_reasoning.stage7a.features import feature_families


def telemetry(mass):
    return {layer: {'groups': {'sink': {'mean_attention_mass': mass}}, 'all_values_finite': True}
            for layer in ('28', '29')}


def test_sink_release_orientation_and_missing_history():
    prior = dict(available=True, telemetry=telemetry(.6))
    assert passive.sink_release(prior, telemetry(.2))['layers']['28'] == pytest.approx(.4)
    assert passive.sink_release(prior, telemetry(.8))['layers']['29'] == pytest.approx(-.2)
    assert passive.sink_release(dict(available=False, reason='no history'), telemetry(.2)) == dict(
        available=False, reason='no history', layers={})


@pytest.mark.parametrize('current', [8, 12, 20])
def test_prior_capture_stops_at_t_minus8_without_mutating_prefill(monkeypatch, current):
    prefill = SimpleNamespace(prompt_length=100, generated_length=0)
    seen, hooked = [], []
    active = [False]
    def advance(*, state, token_ids, **kwargs):
        seen.extend(token_ids)
        if active[0]: hooked.extend(token_ids)
        state.generated_length += len(token_ids)
    def clone(state):
        return SimpleNamespace(**vars(state))
    def root(model, state, event):
        copied = clone(state)
        advance(state=copied, token_ids=event['history_before_ed_token_ids'][:event['candidate_start_token']-8])
        return copied
    class Capture:
        def __init__(self, model, query, groups, grid):
            assert query == 100+current-8 and groups == {'sink': [0]}
            self.telemetry = telemetry(.4)
            self.residual = {'28': 2., '29': 3.}
            self.output_norms = {'28': 1., '29': 1.}
        def __enter__(self):
            active[0] = True
            return self
        def __exit__(self, *args):
            active[0] = False
    monkeypatch.setattr(passive, 'advance_streaming_state', advance)
    monkeypatch.setattr(passive, 'clone_streaming_state', clone)
    monkeypatch.setattr(passive, 'make_event_root', root)
    monkeypatch.setattr(passive, 'Stage6BPassiveStep', Capture)
    result = passive.collect_prior_sink(None, prefill, dict(current_query_zero_based=current,
        candidate_start_token=current+1, history_before_ed_token_ids=list(range(current+1))))
    assert seen == list(range(current-8+1)) and hooked == [current-8]
    assert result['current_query_zero_based'] == current-8
    assert prefill.generated_length == 0 and active[0] is False


def test_missing_prior_does_not_load_or_capture_model():
    result = passive.collect_prior_sink(None, None, dict(current_query_zero_based=7))
    assert result['available'] is False


def test_oracle_distances_use_available_fixed_controls_only():
    a = np.arange(100, dtype=float)/10
    distances = passive_control_distances('strong', {'N': a, 'fixed_mask': -a})
    assert distances['mask']['JS_nats'] > 0 and distances['no_image'] == {'available': False}
    self_distance = passive_control_distances('mask', {'N': a})['mask']
    assert self_distance == dict(available=True, JS_nats=0., top50_overlap=1.)


def test_prior_and_oracle_cannot_enter_primary_source_features():
    entry = dict(source_groups={}, condition='intact', dataset='fixture', cohort='C2',
                 reviewed_claim={'kind': 'primary'}, physical_demanded_source='T',
                 physical_alternative_source='X', row={'fields': {}})
    report = dict(generated_prefix_length=20, visual_token_count=10, telemetry=telemetry(.2),
                  residual_norms={'28': 2., '29': 3.}, D=1., L_o=-1., L_c=-2., predictive_entropy=2.,
                  sink_release=dict(available=True, layers={'28': .4, '29': -.1}),
                  prior_t_minus8=dict(available=True, residual_norms={'28': 1., '29': 4.}),
                  offline_control_distances={'mask': dict(available=True, JS_nats=.3, top50_overlap=.5),
                                             'no_image': dict(available=False)})
    vectors = {'28': [1., 2.], '29': [2., 3.]}
    features = feature_families(entry, report, vectors)
    missing = dict(report, sink_release={'available': False}, prior_t_minus8={'available': False},
                   offline_control_distances={'mask': {'available': False}, 'no_image': {'available': False}})
    absent = feature_families(entry, missing, vectors)
    for family in ('source_specific', 'layout_baseline', 'global_visual', 'source_plus_residual'):
        assert features[family] == absent[family]
    assert features['sink_only']['29.sink_release'] == -.1
    assert features['recent_reasoning']['29.residual_norm_change'] == -1.
    assert features['readout_oracle']['distance.mask.JS_nats'] == .3
    assert '28.sink_release' not in absent['sink_only']
