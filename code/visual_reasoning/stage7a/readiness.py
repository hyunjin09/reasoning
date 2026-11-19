"""Conservative, prospectively declared feasibility gates; no recommendation."""


def monitor_gate(counts, probes, minimum_events=24):
    sufficient = [name for name, value in counts.items()
                  if name != 'UNRESOLVED' and value['tier1_events']+value['strong_tier2_events'] >= minimum_events]
    primary = probes.get('correct_source_vs_wrong_source', {}).get('primary', {}).get('source_specific', {})
    matched = primary.get('matched', {})
    interval = matched.get('accuracy_interval', {}).get('interval95')
    discriminates = bool(matched.get('status') == 'ESTIMATED_FEASIBILITY_ONLY' and interval and interval[0] > .5)
    comparisons = matched.get('paired_baseline_comparisons', {})
    above = {}
    for name in ('layout_baseline', 'global_visual'):
        ci = comparisons.get(name, {}).get('interval95')
        above[name] = bool(ci and ci[0] > 0)
    return dict(ready=len(sufficient) >= 2 and discriminates and all(above.values()),
                sufficient_states=sufficient, minimum_fresh_strong_events_per_state=minimum_events,
                heldout_matched_source_identity_above_chance=discriminates,
                source_identity_above_matched_baselines=above,
                primary_feature_family='source_specific', oracle_features_used_for_gate=False,
                evaluation='Frozen discovery training / confirmation testing; conditional fitted-model bootstrap',
                limits='Probe feasibility only; low independent-family N and source-defined labels remain material limits. No deployed monitor.')
