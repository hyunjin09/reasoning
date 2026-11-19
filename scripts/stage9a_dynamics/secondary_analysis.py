"""Descriptive continuation, fixed local-readout and native-use summaries."""
import json
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
from scripts.stage9a_dynamics.prepare_answers import MAIN, BASE, save, sha
from scripts.stage9a_dynamics.analyze_main import load
from visual_reasoning.stage9a.protocol import ARMS
from visual_reasoning.stage9a.statistics import mean_interval

LEGACY = Path('outputs/stage9a_dynamics/v1')


def grouped_family_mean(rows, field):
    groups = defaultdict(list)
    for row in rows:
        value = row[field]
        if value is not None:
            groups[row['family_id']].append(value)
    return mean_interval([float(np.mean(v)) for _, v in sorted(groups.items())])


def continuation_summary(rows):
    groups = defaultdict(list)
    for r in rows:
        # Demand IDs are event-specific; all other IDs identify the shared schedule.
        name = 'demand_' + r['role'] if r['assay'] == 'demand' else r['condition_id']
        groups[(r['arm'], name)].append(r)
    output = []
    for (arm, condition), group in sorted(groups.items()):
        first = [r['first_divergence_token'] for r in group if r['first_divergence_token'] is not None]
        exposure = []
        for r in group:
            exposure.append(sum(max(0, min(r['tokens'], hi if hi is not None else r['tokens']) - max(1, lo))
                                for lo, hi in r['intervals']))
        output.append(dict(arm=arm, condition=condition, n_families=len(group),
                           accuracy_no_credit=float(np.mean([r['accuracy_no_credit'] for r in group])),
                           raw_accuracy_no_credit=float(np.mean([r['accuracy_raw'] for r in group])),
                           labels=dict(Counter(r['benchmark_label'] for r in group)),
                           completion=dict(Counter(r['completion'] for r in group)),
                           normal_eos=sum(r['normal_eos'] for r in group), capped=sum(r['at_length_cap'] for r in group),
                           median_tokens=float(np.median([r['tokens'] for r in group])),
                           mean_token_change=float(np.mean([r['tokens']-r['native_tokens'] for r in group])),
                           identical_native=sum(r['identical_native'] for r in group),
                           divergence_count=len(first), median_first_divergence=float(np.median(first)) if first else None,
                           exposed_trajectories=sum(v > 0 for v in exposure), total_masked_queries=sum(exposure)))
    return output


def readout_summary(main_families):
    files = sorted((LEGACY/'readouts/events').glob('*/result.json'))
    assert len(files) == 50
    rows = []; paired = []; sources = {}
    for path in files:
        event = load(path); sources[str(path)] = sha(path)
        full = next(r for r in event['rows'] if r['role'] == 'full')
        for r in event['rows']:
            if r['role'] == 'full': continue
            rows.append(dict(event_id=event['event_id'], family_id=event['family_id'], arm=event['arm'],
                             in_main_cohort=event['family_id'] in main_families, radius=r['radius'], role=r['role'],
                             original_mean_log_probability_damage=full['original']['mean_log_probability']-r['original']['mean_log_probability'],
                             original_sum_log_probability_damage=full['original']['sum_log_probability']-r['original']['sum_log_probability'],
                             preference_damage=full['original_minus_counterfactual']-r['original_minus_counterfactual'],
                             exposed_before_readout=r['masked_query_count_before_readout'],
                             exposed_during_readout=r['masked_query_count_during_original_readout']))
        for radius in (16, 32):
            pair = {r['role']: r for r in rows if r['event_id'] == event['event_id'] and r['radius'] == radius}
            if set(pair) != {'demand','control'}: continue
            d, c = pair['demand'], pair['control']
            paired.append(dict(event_id=event['event_id'], family_id=event['family_id'], arm=event['arm'], radius=radius,
                               in_main_cohort=event['family_id'] in main_families,
                               both_exposed=all(r['exposed_before_readout']+r['exposed_during_readout'] > 0 for r in (d,c)),
                               original_mean_log_probability_damage=d['original_mean_log_probability_damage']-c['original_mean_log_probability_damage'],
                               preference_damage=d['preference_damage']-c['preference_damage']))
    summaries = []
    for scope in ('frozen50', 'main64_subset'):
        for arm in ARMS:
            for radius in (16, 32):
                rr = [r for r in rows if r['arm']==arm and r['radius']==radius and (scope=='frozen50' or r['in_main_cohort'])]
                pp = [r for r in paired if r['arm']==arm and r['radius']==radius and (scope=='frozen50' or r['in_main_cohort'])]
                entry = dict(scope=scope, arm=arm, radius=radius, roles={})
                for role in ('demand','control'):
                    subset = [r for r in rr if r['role']==role]
                    entry['roles'][role] = dict(n_events=len(subset), n_families=len({r['family_id'] for r in subset}),
                        unexposed_events=sum(r['exposed_before_readout']+r['exposed_during_readout']==0 for r in subset),
                        **{k:grouped_family_mean(subset,k) for k in ('original_mean_log_probability_damage','preference_damage')})
                entry['paired'] = {name:dict(n_events=len(subset),
                    **{k:grouped_family_mean(subset,k) for k in ('original_mean_log_probability_damage','preference_damage')})
                    for name, subset in [('all_available',pp), ('both_exposed',[r for r in pp if r['both_exposed']])]}
                summaries.append(entry)
    return dict(frozen_events=50, rows=rows, paired_rows=paired, summaries=summaries, sources_sha256=sources,
                secondary_only=True, independent_unit='family; average multiple events within family before bootstrap',
                limitations='Fixed native text, not natural continuation. Shifted controls after the readout are unexposed; both-exposed sensitivity is explicit. Original50 may include reserve families, which do not enter primary inference. No CI below20 families.')


def main():
    scored = load(MAIN/'audit/scored_conditions.json')['rows']
    families = {r['family_id'] for r in scored}
    save(MAIN/'audit/continuation_secondary.json', dict(rows=continuation_summary(scored),
        limitations='Condition-level descriptive summaries; tokens and conditions are not independent observations. Divergence is not correctness or semantic damage.'))
    save(MAIN/'audit/local_readouts_secondary.json', readout_summary(families))
    native = load(BASE/'audit/trajectory_metrics.json')['rows']
    summaries = {}
    for scope in ('original128', 'main64_subset'):
        summaries[scope] = {}
        for arm in ARMS:
            rr = [r for r in native if r['arm']==arm and (scope=='original128' or r['family_id'] in families)]
            assert len({r['family_id'] for r in rr}) == len(rr)
            summaries[scope][arm] = {key:mean_interval([r['primary'][key] for r in rr])
                                      for key in ('episodes_per_1k','active_fraction','P2')}
    save(MAIN/'audit/native_usage_secondary.json', dict(summaries=summaries,
        meanings={'episodes_per_1k':'Native retrieval episodes per1000 reasoning tokens', 'active_fraction':'Native active retrieval-token fraction', 'P2':'Fraction of retrieval episode onsets in native late half; missing when no episodes'},
        source_sha256=sha(BASE/'audit/trajectory_metrics.json'),
        interpretation='Descriptive native usage and intervened necessity are different estimands. No causal effect is inferred from attention magnitude or correlation.'))
    print(json.dumps(dict(conditions=len(scored), local_events=50, native_trajectories=len(native))))


if __name__=='__main__': main()
