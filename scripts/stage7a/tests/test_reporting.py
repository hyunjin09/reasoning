from visual_reasoning.stage7a.reporting import family_rate, correctness_matrix


def test_rate_weights_families_and_keeps_unknown_out_of_denominator():
    rows = [dict(base_id='a', group_id='A')] * 20 + [dict(base_id='b', group_id='B'), dict(base_id='c', group_id='C')]
    result = family_rate(rows, [1] * 20 + [0, None])
    assert result['mean'] == .5
    assert result['events'] == 21 and result['independent_families'] == 2


def test_unknown_identity_is_not_unfaithful_and_integration_is_not_final_error():
    entry = dict(id='e', event_id='native', base_id='a', group_id='A', split='confirmation', dataset='test',
                 condition='intact', readout_type='V', reviewed_claim=dict(demand='singleton', locally_correct=True),
                 downstream_review=dict(later_error=True, integration_error_eligible=True, final_correct=True))
    state = dict(tier=None, state='UNRESOLVED', source_identity=None)
    result = correctness_matrix([entry], {'e': state})
    assert result['rows'][0]['source_fidelity'] == 'unresolved'
    state.update(tier=1, state='DOWNSTREAM_INTEGRATION_ERROR', source_identity='T')
    row = correctness_matrix([entry], {'e': state})['rows'][0]
    assert row['source_fidelity'] == 'demanded_source' and row['later_error'] and row['final_correct']
