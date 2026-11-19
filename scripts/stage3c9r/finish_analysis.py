#!/usr/bin/env python3
"""Finish lifetime, diagnostic comparisons and one plan-defined recommendation."""

from collections import Counter, defaultdict
import statistics

import numpy as np

from visual_reasoning.stage3c8.analysis import summarize_effect
from visual_reasoning.stage3c9.analysis import source_and_rescue_effects
from visual_reasoning.stage3c9r.analysis import classify_bases, summarize_bases
from visual_reasoning.stage3c9r.protocol import lifetime_summary
from scripts.stage3c9r.analyze import collect
from scripts.stage3c9r.freeze_inputs import ROOT, OUT, OLD, read_json, read_jsonl, write_json, write_jsonl


def followup_scores(role):
    tasks = read_json(OUT / f'analysis/{role}_tasks.json')['tasks']
    expected = {(t['base_problem_id'],t['event_id'],t['readout_name'],c)
                for t in tasks for c in ('O','C')}
    raw = {}
    for p in (OUT / f'{role}_raw').glob('shard_*/*/*/*.json'):
        r = read_json(p)
        key = (r['base_problem_id'],r['event_id'],r['readout_name'],r['condition'])
        if key in raw:
            raise RuntimeError('Duplicate follow-up cell')
        raw[key] = r
    if set(raw) != expected:
        raise RuntimeError(f'{role} incomplete: {len(raw)}/{len(expected)}')
    return tasks, raw


def phase_comparison(families, bases):
    old_a = {(r['base_problem_id'],r['event_id'],r['window']):r['local_use']
             for w in ('w8','w16') for r in read_jsonl(OLD / f'phase_a_source/{w}_source_sensitivity.jsonl')}
    old_b = {}
    for p in (OLD / 'phase_b_checkpoint/raw').glob('shard_*/examples/*/result.json'):
        r = read_json(p)
        for e in r['events']:
            for w in e['conditions']['O']['local_use'].get('windows',{}):
                old_b[r['base_problem_id'],e['event_id'],w] = {
                    c:source_and_rescue_effects(condition=c,
                        native_D=e['conditions'][c]['local_use']['windows'][w]['native']['D'],
                        suppressed_D=e['conditions'][c]['local_use']['windows'][w]['suppressed']['D'])
                    for c in ('O','C')}
    old_classes = {(b['base_problem_id'],e['event_id'],w):m
                   for b in read_json(OLD / 'phase_b_checkpoint/checkpoint_classification.json')['bases']
                   for e in b['events'] for w,m in e['window_classifications'].items()}
    comparisons = []
    gate_rows = []
    for b in bases:
        for e in b['events']:
            for w,new in e['windows'].items():
                key = b['base_problem_id'],e['event_id'],w
                a = old_a[key]
                gate_rows.append({'base_problem_id':key[0],'event_id':key[1],'window':w,
                    'stage3c9_phase_a_gate':a['source_sensitive'],
                    'stage3c9_phase_b_gate':old_classes[key]['source_sensitive'] if key in old_b else None,
                    'stage3c9r_gate':new['source_sensitive']})
                for c in ('O','C'):
                    n = new['condition_metrics'][c]
                    aa = a['condition_metrics'][c]
                    bb = old_b.get(key,{}).get(c)
                    comparisons.append({'base_problem_id':key[0],'event_id':key[1],'window':w,'condition':c,
                        'phase_a_source_loss':aa['source_loss'],
                        'phase_b_source_loss':bb['source_loss'] if bb else None,
                        'repair_source_loss':n['source_loss'],
                        'abs_source_loss_difference_vs_A':abs(n['source_loss']-aa['source_loss']),
                        'abs_source_loss_difference_vs_B':abs(n['source_loss']-bb['source_loss']) if bb else None,
                        'abs_native_D_difference_vs_A':abs(n['aligned_native_D']-aa['aligned_native_D']),
                        'abs_suppressed_D_difference_vs_A':abs(n['aligned_suppressed_D']-aa['aligned_suppressed_D']),
                        'abs_native_D_difference_vs_B':abs(n['aligned_native_D']-bb['aligned_native_D']) if bb else None,
                        'abs_suppressed_D_difference_vs_B':abs(n['aligned_suppressed_D']-bb['aligned_suppressed_D']) if bb else None})
    def summary(phase):
        field = f'abs_source_loss_difference_vs_{phase}'
        rows = [r for r in comparisons if r[field] is not None]
        gates = [r for r in gate_rows if r[f'stage3c9_phase_{phase.lower()}_gate'] is not None]
        return {'event_window_conditions':len(rows),'event_windows':len(gates),
            'median_absolute_source_loss_difference':statistics.median(r[field] for r in rows),
            'mean_absolute_source_loss_difference':statistics.fmean(r[field] for r in rows),
            'max_absolute_source_loss_difference':max(r[field] for r in rows),
            'sign_agreement':statistics.fmean(np.sign(r['repair_source_loss']) == np.sign(r[f'phase_{phase.lower()}_source_loss']) for r in rows),
            'gate_agreement_count':sum(r['stage3c9r_gate'] == r[f'stage3c9_phase_{phase.lower()}_gate'] for r in gates),
            'gate_agreement_fraction':statistics.fmean(r['stage3c9r_gate'] == r[f'stage3c9_phase_{phase.lower()}_gate'] for r in gates)}
    write_json(OUT / 'analysis/stage3c9_phase_comparison.json', {
        'descriptive_only':True,'primary_uses_only_stage3c9r':True,
        'phase_B_legacy_gate_used_old_Phase_A_shams':True,
        'vs_A':summary('A'),'vs_B':summary('B'),'condition_rows':comparisons,'gate_rows':gate_rows})


def main():
    manifest, families, _ = collect()
    primary_bases = read_json(OUT / 'analysis/primary_freeze.json')['primary_local_classification']
    tasks, raw = followup_scores('lifetime')
    final_gains = {}
    lifetime_rows = []
    for b in primary_bases:
        base = b['base_problem_id']
        for e in b['events']:
            if not e['qualifying_windows']:
                continue
            per_window = {}
            for w in e['qualifying_windows']:
                readouts = []
                final_mean = None
                for task in tasks:
                    if task['base_problem_id'] != base or task['event_id'] != e['event_id'] or w not in task['windows']:
                        continue
                    effects = {}
                    for c in ('O','C'):
                        row = raw[base,e['event_id'],task['readout_name'],c]['windows'][w]
                        assert row['event_rescue']['recipient_execution_id'] == row['execution_id']
                        effects[c] = source_and_rescue_effects(condition=c, native_D=row['native']['D'],
                            suppressed_D=row['suppressed']['D'], rescue_D=row['event_rescue']['D'])
                    gains = {c:m['rescue_gain'] for c,m in effects.items()}
                    mean = statistics.fmean(gains.values())
                    readouts.append({'name':task['readout_name'],'token_index':task['readout']['token_index'],
                        'distance_from_span_end':task['readout']['token_index']-e['span_end_token'],
                        'condition_metrics':effects,'rescue_gain_mean':mean})
                    if task['readout_name'] == 'final':
                        final_gains[base,e['event_id'],w] = gains
                        final_mean = mean
                local = e['windows'][w]['rescue_gain_mean']
                per_window[w] = {'local_rescue_gain_mean':local, 'final_rescue_gain_mean':final_mean,
                    'readouts':readouts, **lifetime_summary(local_gain=local,
                        downstream=[(r['distance_from_span_end'],r['rescue_gain_mean']) for r in readouts], final_gain=final_mean)}
            order = {'RIGHT-CENSORED':0,'NOT_APPLICABLE':0,'L-Short':1,'L-Medium':2,'L-Persistent':3}
            lifetime_rows.append({'base_problem_id':base,'event_id':e['event_id'],
                'span_start_token':e['span_start_token'],'span_end_token':e['span_end_token'],
                'per_window':per_window,'phenotype':max((r['phenotype'] for r in per_window.values()),key=order.get)})
    bases = classify_bases(manifest, families, final_gains=final_gains)
    summary = summarize_bases(bases)
    assert summary['checkpoint_events'] == sum(b['checkpoint_count'] for b in primary_bases)
    assert summary['repeated_checkpoint_bases'] == sum(b['repeated_checkpoint'] for b in primary_bases)
    reinstatement = []
    life_by_event = {(r['base_problem_id'],r['event_id']):r for r in lifetime_rows}
    for b in bases:
        for i,j in b['qualifying_pairs']:
            early,late = b['events'][i],b['events'][j]
            if early['evidence_relation'] != 'SAME_TARGET_EVIDENCE' or late['evidence_relation'] != 'SAME_TARGET_EVIDENCE':
                continue
            checks = []
            for w,life in life_by_event[b['base_problem_id'],early['event_id']]['per_window'].items():
                if w not in late['qualifying_windows']:
                    continue
                at_late = [r for r in life['readouts'] if r['token_index'] == late['local_use_readout']['token_index']]
                if at_late:
                    checks.append({'window':w,'early_gain_at_later_use':at_late[0]['rescue_gain_mean'],
                                   'later_local_gain':late['windows'][w]['rescue_gain_mean'],
                                   'replaced':at_late[0]['rescue_gain_mean'] < .05 <= late['windows'][w]['rescue_gain_mean']})
            reinstatement.append({'base_problem_id':b['base_problem_id'], 'earlier_event_id':early['event_id'],
                'later_event_id':late['event_id'],'comparisons':checks,
                'phenotype':'L-Replaced' if any(r['replaced'] for r in checks) else 'NOT_L_REPLACED'})
    write_json(OUT / 'analysis/checkpoint_classification.json', {'bases':bases, **summary,'final_readout_upgrades_pending':False})
    write_json(OUT / 'analysis/repeated_checkpoint_analysis.json', {'bases':bases, **summary})
    write_json(OUT / 'analysis/lifetime_analysis.json', {'rows':lifetime_rows,
        'phenotype_counts':dict(Counter(r['phenotype'] for r in lifetime_rows)),
        'reinstatement_pairs':reinstatement, 'right_censoring_explicit':True,
        'unobserved_decay_intervals_are_not_resolved':True})
    phase_comparison(families,bases)
    base38 = next(b for b in bases if b['base_problem_id']=='38')
    original38 = next(r for r in read_jsonl(OLD/'phase_c_lifetime/lifetime_readouts.jsonl')
                      if r['base_problem_id']=='38' and r['event_id']==0)['per_window']['W16']
    original_next = original38['downstream_semantic_readouts'][0]
    write_json(OUT / 'analysis/base38_reference.json', {'frozen_reference_not_tuning':True,
        'original_local_G':original38['local_rescue_gain_mean'],
        'original_downstream_G':original_next['rescue_gain_mean'],
        'original_downstream_distance':original_next['distance'],
        'original_final_G':original38['final_rescue_gain_mean'],
        'repair':base38,'lifetime':[r for r in lifetime_rows if r['base_problem_id']=='38'],
        'reference_survival_is_not_a_technical_gate':True})
    groups = defaultdict(list)
    for item,b in zip(manifest,bases):
        groups[item['evidence_type']].append(b)
    write_json(OUT / 'analysis/target_heterogeneity.json', {'grouping':'frozen evidence_type',
        'groups':{name:summarize_bases(rows) for name,rows in groups.items()},
        'base_targets':[{'base_problem_id':str(b['base_problem_id']),'target_evidence':b['target_evidence'],
                         'evidence_type':b['evidence_type'],'original_value':b['original_value'],
                         'counterfactual_value':b['counterfactual_value']} for b in manifest]})
    necessity_tasks, necessity_raw = followup_scores('necessity')
    necessity_results = []
    for task in necessity_tasks:
        for w in task['windows']:
            effects = {}
            for c in ('O','C'):
                r = necessity_raw[task['base_problem_id'],task['event_id'],'local',c]['windows'][w]
                sign = 1 if c=='O' else -1
                effects[c] = sign*(r['native']['D']-r['necessity']['D'])
            necessity_results.append({**task,'window':w,'sign_aligned_harm':effects,
                                      'mean_harm':statistics.fmean(effects.values())})
    write_jsonl(OUT / 'optional_necessity/necessity_results.jsonl',necessity_results)
    sensitivity = read_json(OUT / 'analysis/threshold_sensitivity.json')['rows']
    repeated = [r['repeated_checkpoint_bases'] for r in sensitivity]
    route = read_json(OUT / 'route/route_status.json')
    if route['run'] and route['status'] != 'COMPLETE':
        raise RuntimeError('Original route feasibility gate passed; required route work remains')
    if all(n==0 for n in repeated):
        outcome, recommendation = 'R1', 'GO — Retrieval Trigger'
        claim = 'The long-horizon sparse semantic-checkpoint hypothesis is not supported under the tested W8/W16 event-span assay.'
    elif summary['repeated_checkpoint_bases'] > 0 and min(repeated) > 0:
        outcome = 'R3'
        recommendation = 'REVIEW — Repeated checkpoints and gated route evidence'
        claim = 'Repeated sparse causal checkpoints occur on the frozen cohort; assess their prevalence and available route evidence before any expansion.'
    else:
        outcome, recommendation = 'R4', 'REVIEW — Continuous window-level causal measure'
        claim = 'The repeated-checkpoint conclusion is threshold-sensitive; the binary sparse-checkpoint assay should not carry a central paper claim.'
    write_json(OUT / 'analysis/scientific_outcome.json', {'outcome':outcome,'recommendation':recommendation,
        'claim':claim,'next_experiment_started':False,'source_rescue_profile_interpretation':
        'Source-sensitive nonrescued windows establish local visual dependence without sufficient sparse-span rescue; distributed state, direct refresh and redundant carriage remain alternatives.',
        'repeated_counts_by_floor':repeated,'no_cohort_expansion':True})
    print({'summary':summary,'lifetime_count':len(lifetime_rows),'outcome':outcome,'recommendation':recommendation})


if __name__ == '__main__':
    main()
