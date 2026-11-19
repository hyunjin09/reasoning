from visual_reasoning.stage7a.matching import match_test_events


def test_matching_rejects_shared_images_and_exact_metadata_mismatch():
    def entry(condition='mask'):
        return dict(condition=condition, dataset='D', cohort='C', readout_type='V',
                    event={'ed_generated_index': 100}, source_groups={'T': [1], 'G': [1]},
                    physical_demanded_source='T', physical_alternative_source='X', row={'fields': {}})
    entries = {key: entry() for key in ('a', 'b', 'c')}
    entries['d'] = entry('intact')
    rows = [dict(id='a', group_id='shared', label=0), dict(id='b', group_id='shared', label=1),
            dict(id='c', group_id='different', label=1), dict(id='d', group_id='third', label=1)]
    tolerances = dict(exact_keys=['condition', 'dataset', 'cohort', 'readout_type'],
                      continuous={key: {'tolerance': .1} for key in
                                  ('log_prefix_length', 'log_visual_tokens', 'log_T_tokens', 'log_X_tokens', 'log_I_tokens')})
    selected, audit = match_test_events(rows, entries, tolerances)
    assert {r['id'] for r in selected} == {'a', 'c'}
    assert len(audit['pairs']) == 1
    assert not audit['passive_features_used']
