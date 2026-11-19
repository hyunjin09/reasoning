"""Assess the plan gates after completed causal and passive evidence exists."""
from scripts.stage7a.common import ROOT, OUT, read_json, write_json, sha
from scripts.stage7a.export_analysis import load_completed
from visual_reasoning.stage7a.reporting import certified
from visual_reasoning.stage7a.matching import match_test_events
from visual_reasoning.stage7a.statistics import directional_summary
from visual_reasoning.stage7a.readiness import monitor_gate


def main():
    entries, metrics, states, _ = load_completed()
    counts = read_json(OUT/'labels/state_counts.json')['counts']['all']
    thresholds = read_json(OUT/'config/discovery_thresholds.json')
    tolerances = read_json(OUT/'config/matching_tolerances.json')
    statistics = read_json(OUT/'analysis/primary_statistics.json')['families']
    config = read_json(OUT/'config/stage7a_config.json')
    probes = read_json(OUT/'monitor_feasibility/probe_results.json')
    protocol = read_json(OUT/'config/readiness_operationalization.json')
    assert protocol['frozen_before_scientific_scores']
    assert protocol['monitor_gate_sha256'] == sha(ROOT/'code/visual_reasoning/stage7a/readiness.py')
    minimum = config['state_claim_minimum_fresh_strong_events']
    monitor = monitor_gate(counts, probes, minimum)
    lookup = {e['id']: e for e in entries}
    specs = {
        'PRIOR_FILL': ('2', ['prior_JS_convergence', 'prior_margin_convergence', 'prior_top50_convergence', 'T_semantic_loss_intact_to_strong'],
                       'Force visual verification or abstain when evidence is unavailable.'),
        'WRONG_SOURCE_READ': ('3', ['X_EP_token', 'X_EP_margin', 'X_semantic', 'X_minus_T_EP_margin'],
                              'Suppress the causally identified wrong source and favor demanded-source evidence.'),
        'STALE_SOURCE_READ': ('4', ['P_EP_token', 'P_EP_margin'],
                             'Suppress the causally identified stale source and refresh current demand.'),
        'SOURCE_COUPLED_EXTRACTION_ERROR': ('5', ['extraction_T_minus_X_EP_margin'],
                                          'Investigate content decoding; stronger retrieval has no established corrective prediction.'),
        'DOWNSTREAM_INTEGRATION_ERROR': ('5', ['integration_T_minus_X_VSD', 'integration_T_semantic'],
                                        'Local retrieval is already faithful; no visual retrieval correction is established.'),
    }
    assessments = {}
    for name, (family, tests, prediction) in specs.items():
        selected = [e for e in entries if states[e['id']]['state'] == name and certified(states[e['id']])]
        evidence = {test: statistics[family][test] for test in tests}
        coherent = (all(r['directionally_robust'] for r in evidence.values())
                    if all(r['status'] == 'ESTIMATED' for r in evidence.values()) else None)
        matched = dict(status='UNAVAILABLE', reason='No mechanically equivalent corrective action was tested for this state; predicted faithful-control response remains unverified.')
        matched_pass = None
        if name in ('WRONG_SOURCE_READ', 'STALE_SOURCE_READ'):
            rows = [dict(id=e['id'], base_id=e['base_id'], group_id=e['group_id'], label=int(states[e['id']]['state'] == name))
                    for e in entries if e['split'] == 'confirmation' and certified(states[e['id']])
                    and states[e['id']]['state'] in ('FAITHFUL_READ', name)]
            _, matching = match_test_events(rows, lookup, tolerances)
            controls = []
            for pair in matching['pairs']:
                e = lookup[pair['negative_id']]
                effect = metrics[e['id']]['source_effects'].get('X_W2')
                if effect is None: continue
                controls.append(dict(id=e['id'], base_id=e['base_id'], group_id=e['group_id'],
                    value=1-max(effect['VSD']/thresholds['vsd_floor'], effect['EP_claim']/thresholds['error_floor'])))
            summary = directional_summary(controls)
            ci = summary.get('mean_ci95')
            matched_pass = bool(summary['n_groups'] >= 5 and ci and ci[0] > 0 and
                                summary['median'] > 0 and summary['positive_group_fraction'] >= .75)
            matched = dict(status='ASSESSED' if controls else 'UNAVAILABLE', matching=matching, summary=summary,
                           meaning='On metadata-matched faithful controls, wrong-source suppression should have little or opposite effect on correct evidence.',
                           scope='Descriptive readiness diagnostic, state-selected; not an additional confirmatory discovery.')
        checks = dict(sufficient_fresh_events=len(selected) >= minimum,
                      causal_direction_coherent=coherent,
                      failure_readout_oriented=bool(selected),
                      clear_corrective_prediction=name in ('PRIOR_FILL', 'WRONG_SOURCE_READ', 'STALE_SOURCE_READ'),
                      matched_faithful_controls=matched_pass)
        assessments[name] = dict(ready=all(value is True for value in checks.values()), checks=checks,
            fresh_strong_events=len(selected), bases=len({e['base_id'] for e in selected}),
            independent_families=len({e['group_id'] for e in selected}),
            confirmation_events=sum(e['split'] == 'confirmation' for e in selected),
            predicted_action=prediction, confirmatory_direction_evidence=evidence, matched_controls=matched,
            online_detectability_established=monitor['ready'] and name == 'WRONG_SOURCE_READ')
    write_json(OUT/'analysis/monitor_readiness.json', monitor, freeze=True)
    write_json(OUT/'analysis/intervention_readiness.json', dict(states=assessments,
               intervention_run=False, stage7c_automatic_authorization=False,
               minimum_fresh_strong_events=minimum, code_sha256=sha(__file__),
               protocol_sha256=sha(OUT/'config/readiness_operationalization.json')), freeze=True)
    print('Monitor and intervention gates assessed; next research direction has not been selected here.')


if __name__ == '__main__':
    main()
