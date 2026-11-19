import numpy as np
from visual_reasoning.stage7a.probes import group_weights, fit_probe, accuracy_bootstrap


def test_training_repetitions_get_equal_family_and_class_weight():
    rows = [dict(group_id='a', label=0)]*100 + [dict(group_id='b', label=0), dict(group_id='c', label=1)]
    w = group_weights(rows, balance_classes=True)
    assert np.isclose(w[:100].sum(), w[100])
    assert np.isclose(w[:101].sum(), w[101])


def test_test_weights_do_not_give_longer_trajectories_more_influence():
    rows = [dict(group_id='a', label=i%2) for i in range(10)] + [dict(group_id='b', label=1)]
    w = group_weights(rows)
    assert np.isclose(w[:10].sum(), w[10])


def test_probe_fits_only_training_vocabulary_and_scores_distinct_test_families():
    def row(split, i):
        label = i % 2
        features = {'signal': (2*label-1)*(2+i/10)}
        if split == 'test': features['heldout_only'] = 1e9
        return dict(id=split+str(i), group_id=split+str(i), label=label,
                    features={'source_specific': features})
    train, test = [row('train', i) for i in range(8)], [row('test', i) for i in range(8)]
    result = fit_probe(train, test, 'source_specific')
    assert result['status'] == 'ESTIMATED_FEASIBILITY_ONLY'
    assert result['feature_names'] == ['signal']
    assert result['metrics']['balanced_accuracy'] == 1.
    assert {r['id'] for r in result['predictions']} == {r['id'] for r in test}
    interval = accuracy_bootstrap(result['predictions'], samples=100)
    assert interval['interval95'] == [1., 1.]
