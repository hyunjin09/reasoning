from visual_reasoning.stage7a.readiness import monitor_gate


def test_oracle_and_unmatched_success_cannot_establish_monitor_readiness():
    counts = {s: dict(tier1_events=30, strong_tier2_events=0) for s in ('FAITHFUL_READ', 'WRONG_SOURCE_READ')}
    good = dict(status='ESTIMATED_FEASIBILITY_ONLY', accuracy_interval=dict(interval95=[.7, .9]),
                paired_baseline_comparisons={s: dict(interval95=[.1, .3]) for s in ('layout_baseline', 'global_visual')})
    probes = {'correct_source_vs_wrong_source': {'primary': {'source_specific': good, 'readout_oracle': dict(matched=good)}}}
    assert not monitor_gate(counts, probes)['ready']
    probes['correct_source_vs_wrong_source']['primary']['source_specific'] = dict(matched=good)
    assert monitor_gate(counts, probes)['ready']
    good['paired_baseline_comparisons']['layout_baseline']['interval95'] = [-.1, .3]
    assert not monitor_gate(counts, probes)['ready']
