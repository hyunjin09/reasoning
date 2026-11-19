from visual_reasoning.stage7a.features import purge_training_bases, task_label


def test_held_out_donor_cannot_leak_through_another_training_base():
    groups = {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D'}
    test = [dict(base_id='a')]
    train = [dict(base_id='b'), dict(base_id='b', unrelated_donor='a'), dict(base_id='c'), dict(base_id='d', unrelated_donor='b')]
    kept, audit = purge_training_bases(train, test, groups)
    assert [r['base_id'] for r in kept] == ['c', 'd']
    assert audit['purged_train_families'] == ['B']


def test_weak_tier2_and_unresolved_do_not_supply_probe_ground_truth():
    assert task_label(dict(tier=2, strong_tier2=False, state='FAITHFUL_READ', source_identity='T'), 'correct_source_vs_wrong_source') is None
    assert task_label(dict(tier=None, state='UNRESOLVED', source_identity=None), 'grounded_vs_ungrounded') is None
    assert task_label(dict(tier=1, state='WRONG_SOURCE_READ', source_identity='X'), 'grounded_vs_ungrounded') == 0
