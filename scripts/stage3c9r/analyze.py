#!/usr/bin/env python3
"""Classify only after all frozen primary rescue conditions have been scored."""

import argparse
from collections import defaultdict
import statistics

from visual_reasoning.stage3c9.assay import CONDITIONS
from visual_reasoning.stage3c9.analysis import source_and_rescue_effects
from visual_reasoning.stage3c9.protocol import first_route_pair
from visual_reasoning.stage3c9r.analysis import classify_bases, summarize_bases
from visual_reasoning.stage3c9r.protocol import lifetime_summary
from scripts.stage3c9r.freeze_inputs import ROOT, OUT, OLD, read_json, read_jsonl, write_json, write_jsonl, sha


def collect():
    manifest = read_jsonl(OUT / 'cohort/primary_manifest.jsonl')
    expected = {(str(b['base_problem_id']),e['event_id'],c) for b in manifest for e in b['events'] for c in CONDITIONS}
    raw = {}
    for path in sorted((OUT / 'same_path_scores/raw').glob('shard_*/*/*/*_local.json')):
        r = read_json(path)
        key = (r['base_problem_id'],r['event_id'],r['condition'])
        if key in raw:
            raise RuntimeError(f'Duplicate primary raw score {key}')
        raw[key] = (r, path)
    if set(raw) != expected:
        raise RuntimeError(f'All-event precondition failed: {len(raw)}/{len(expected)}')
    families, paths = defaultdict(dict), {}
    for (base,eid,c),(r,path) in raw.items():
        paths[str(path.relative_to(ROOT))] = sha(path)
        for w,row in r['windows'].items():
            compact = {k: row[k] for k in ['execution_id','partition','readout_generated_index','prefix_sha256','source_window_generated_indices']}
            for arm in ('native','suppressed','event_rescue','neighbor_rescue'):
                compact[arm] = {k:v for k,v in row[arm].items() if k in ['D','L_o','L_c','finite','original_candidate','counterfactual_candidate','recipient_execution_id','execution_id']}
            compact['raw_artifact'] = str(path.relative_to(ROOT))
            families[base,eid,w][c] = compact
    valid = {(str(b['base_problem_id']),e['event_id'],w) for b in manifest for e in b['events'] for w in ('W8','W16') if e['span_start_token'] >= int(w[1:])}
    if set(families) != valid or any(set(c) != set(CONDITIONS) for c in families.values()):
        raise RuntimeError('Mechanically valid full-event window coverage failed')
    return manifest, dict(families), paths


def primary():
    manifest, families, paths = collect()
    bases = classify_bases(manifest, families)
    summary = summarize_bases(bases)
    frozen = {'raw_sha256':paths, 'primary_effect_floor':.05, 'summary':summary,
              'primary_local_classification':bases, 'all_rescues_scored_before_classification':True}
    freeze_path = OUT / 'analysis/primary_freeze.json'
    if freeze_path.exists():
        assert read_json(freeze_path) == frozen, 'Attempt to change a frozen primary result'
    else:
        write_json(freeze_path, frozen)
    rows = []
    for b in bases:
        for e in b['events']:
            for w,metrics in e['windows'].items():
                rows.append({'base_problem_id':b['base_problem_id'], 'event_id':e['event_id'],
                             'window':w, 'event_role':e['event_role'], 'temporal_location':e['temporal_location'],
                             **metrics, 'conditions':families[b['base_problem_id'], e['event_id'], w]})
    for w in ('W8','W16'):
        write_jsonl(OUT / f'same_path_scores/{w.lower()}_all_events.jsonl', [r for r in rows if r['window'] == w])
    write_jsonl(OUT / 'same_path_scores/event_rescue_all.jsonl', rows)
    write_jsonl(OUT / 'same_path_scores/neighbor_rescue_all.jsonl', [
        {k:r[k] for k in ['base_problem_id','event_id','window','neighbor_gain_mean','neighbor_gains','event_minus_neighbor']} for r in rows])
    write_json(OUT / 'analysis/checkpoint_classification.json', {'bases':bases, **summary, 'final_readout_upgrades_pending':True})
    write_json(OUT / 'analysis/source_sensitivity.json', {'summary':summary,
        'source_sensitive_event_windows':sum(r['source_sensitive'] for r in rows),
        'by_window':{w:{'N_event_windows':sum(r['window']==w for r in rows),
                       'source_sensitive':sum(r['window']==w and r['source_sensitive'] for r in rows)} for w in ('W8','W16')}})
    profile = [{k:v for k,v in r.items() if k != 'conditions'} for r in rows]
    for r in profile:
        high_l, high_g = r['source_loss_mean'] >= .05, r['rescue_gain_mean'] >= .05
        r['profile_type'] = 'A' if high_l and high_g else 'B' if high_l else 'C' if high_g else 'D'
    write_json(OUT / 'analysis/source_vs_rescue_2d.json', {'rows':profile,
        'profile_axes_descriptive_only':True, 'scientific_classification_requires_all_directionality_and_sham_controls':True})
    write_json(OUT / 'analysis/repeated_checkpoint_analysis.json', {'bases':bases, **summary})
    # Only now evaluate the secondary floor grid.
    sensitivities = []
    sensitivity_bases = {}
    for floor in read_json(OUT / 'config/sensitivity_grid.json')['floors']:
        classified = classify_bases(manifest, families, effect_floor=floor)
        sensitivity_bases[floor] = classified
        combined = summarize_bases(classified)
        combined.pop('class_counts')  # C2/C3 combined; final-readout upgrades are secondary.
        sensitivities.append({'effect_floor':floor, **combined})
    write_json(OUT / 'analysis/threshold_sensitivity.json', {'primary_freeze_sha256':sha(freeze_path),
        'rows':sensitivities, 'only_effect_floor_changes':True,
        'C2_C3_combined_counts':True, 'distinct_final_upgrades_do_not_change_counts':True})
    tasks = []
    for item,b in zip(manifest,bases):
        for index,e in enumerate(b['events']):
            if not e['qualifying_windows']:
                continue
            local_index = e['local_use_readout']['token_index']
            # Next independently annotated event and distinct final only, deduplicated.
            later = [x for x in item['events'][index+1:] if x['local_use_readout']['token_index'] > local_index]
            selections = []
            if later:
                selections.append(('next', later[0]['local_use_readout']))
            if item['final_use_readout']['token_index'] > local_index:
                selections.append(('final',item['final_use_readout']))
            for name,readout in selections:
                # A coincident next/final probe is computed once and reused explicitly.
                if name == 'next' and any(n == 'final' and r == readout for n,r in selections):
                    continue
                tasks.append({'base_problem_id':b['base_problem_id'],'event_id':e['event_id'],
                              'readout_name':name,'readout':readout,'windows':e['qualifying_windows']})
    write_json(OUT / 'analysis/lifetime_tasks.json', {'tasks':tasks,'selection':'confirmed primary checkpoints; next/final frozen readouts'})
    robust = [(b,e) for b in sensitivity_bases[.15] for e in b['events'] if e['qualifying_windows']]
    necessity_gate = {'run':len(robust)>=4,'robust_unique_checkpoints':len(robust),
                      'minimum':4,'robust_effect_floor':.15,'prospective_definition':read_json(OUT/'config/stage3c9r_config.json')['optional_necessity']}
    write_json(OUT / 'optional_necessity/gate.json', necessity_gate)
    write_json(OUT / 'analysis/necessity_tasks.json', {'tasks':[
        {'base_problem_id':b['base_problem_id'],'event_id':e['event_id'],'readout_name':'local',
         'readout':e['local_use_readout'],'windows':e['qualifying_windows']} for b,e in robust] if necessity_gate['run'] else []})
    if not necessity_gate['run']:
        write_jsonl(OUT / 'optional_necessity/necessity_results.jsonl', [])
    pairs = [{'base_problem_id':b['base_problem_id'],'route_pair':first_route_pair(b['events'])} for b in bases if b['repeated_checkpoint']]
    gate = {'run':len(pairs)>=16,'eligible_bases':len(pairs),'minimum':16,'pairs':pairs}
    write_json(OUT / 'route/gate.json', gate)
    write_json(OUT / 'route/route_status.json', {'status':'PENDING' if gate['run'] else 'NOT RUN',
                                              'reason':'Original >=16-base gate', **gate})
    print({'primary':summary,'lifetime_tasks':len(tasks),'necessity_gate':necessity_gate,'route_gate':gate})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['primary'], default='primary')
    parser.parse_args()
    primary()
