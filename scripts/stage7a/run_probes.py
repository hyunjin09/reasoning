"""Bounded CPU feasibility work inside the existing research allocation."""
import argparse
import os
import platform
import time
import numpy as np
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl, sha
from visual_reasoning.stage7a.features import feature_families, task_label, purge_training_bases
from visual_reasoning.stage7a.matching import match_test_events
from visual_reasoning.stage7a.probes import fit_probe, score_predictions, accuracy_bootstrap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--discovery-passive', required=True)
    parser.add_argument('--confirmation-passive', required=True)
    args = parser.parse_args()
    started = time.time()
    config = read_json(OUT/'config/stage7a_config.json')
    assert os.environ['SLURM_JOB_ID'] == config['runtime']['slurm_allocation']
    assert platform.node().split('.')[0] == config['runtime']['node']
    freeze_path = OUT/'labels/label_freeze.json'
    freeze = read_json(freeze_path)
    assert freeze['frozen'] and freeze['passive_features_used_for_labels'] is False
    for path, digest in freeze['labels_sha256'].items(): assert sha(ROOT/path) == digest
    design = read_json(OUT/'config/probe_design.json')
    tolerances = read_json(OUT/'config/matching_tolerances.json')
    assert tolerances['frozen']
    dest = OUT/'raw'/args.run_id
    signature = dict(labels_freeze_sha256=sha(freeze_path), design_sha256=sha(OUT/'config/probe_design.json'),
                     primary_sha256=sha(OUT/'config/probe_primary_comparison.json'),
                     split_design_sha256=sha(OUT/'config/probe_split_operationalization.json'),
                     matching_sha256=sha(OUT/'config/matching_tolerances.json'),
                     dependencies_sha256={path: sha(ROOT/path) for path in [
                         'scripts/stage7a/run_probes.py', 'code/visual_reasoning/stage7a/features.py',
                         'code/visual_reasoning/stage7a/probes.py', 'code/visual_reasoning/stage7a/matching.py',
                         'code/visual_reasoning/stage7a/thresholds.py']},
                     slurm_job_id=os.environ['SLURM_JOB_ID'], node=platform.node(), cpu_only=True)
    write_json(dest/'signature.json', signature, freeze=True)
    entries, states, features, raw_paths = {}, {}, {}, {}
    for split, run_id in [('discovery', args.discovery_passive), ('confirmation', args.confirmation_passive)]:
        run = OUT/'raw'/run_id
        assert read_json(run/'run_summary.json')['completed']
        assert read_json(run/'signature.json')['labels_freeze_sha256'] == sha(freeze_path)
        manifest = OUT/'config'/(split+'_events.jsonl')
        assert sha(manifest) == freeze['events_manifest_sha256'][split]
        states.update({s['id']: s for s in read_jsonl(OUT/'labels'/(split+'_states.jsonl'))})
        for entry in read_jsonl(manifest):
            event_id = entry['id']
            path = run/'events'/(event_id+'.json')
            raw = read_json(path)
            assert raw['complete'] and raw['native_causal_exact']
            assert raw['manifest_sha256'] == sha(manifest)
            with np.load(path.with_suffix('.npz')) as vectors:
                features[event_id] = feature_families(entry, raw['report'], vectors)
            entries[event_id] = entry
            raw_paths[event_id] = str(path.relative_to(ROOT))
    for name, family in [('source_specific_features', 'source_specific'), ('routing_features', 'global_visual'), ('sink_features', 'sink_only')]:
        write_jsonl(OUT/'passive'/(name+'.jsonl'), [dict(id=key, features=features[key][family],
                    raw_path=raw_paths[key]) for key in entries], freeze=True)
    write_jsonl(OUT/'passive/residual_features.jsonl', [dict(id=key,
                vector_path=raw_paths[key].removesuffix('.json')+'.npz',
                features=features[key]['residual_state']) for key in entries], freeze=True)
    group_by_base = {r['base_id']: r['group_id'] for r in read_jsonl(OUT/'cohort/base_manifest.jsonl')}
    results, splits = {}, {}
    for task in design['tasks']:
        rows = []
        for key, entry in entries.items():
            label = task_label(states[key], task)
            if label is not None:
                rows.append(dict(id=key, base_id=entry['base_id'], group_id=entry['group_id'],
                                 split=entry['split'], dataset=entry['dataset'], template_family=entry['template_family'],
                                 unrelated_donor=entry['row'].get('unrelated_donor'), label=label, features=features[key]))
        fold_specs = [('primary', None, None)]
        for key in ('dataset', 'template_family'):
            fold_specs += [(key+':'+value, key, value) for value in sorted({r[key] for r in rows if r['split'] == 'confirmation'})]
        results[task], splits[task] = {}, {}
        for name, key, value in fold_specs:
            train = [r for r in rows if r['split'] == 'discovery' and (key is None or r[key] != value)]
            test = [r for r in rows if r['split'] == 'confirmation' and (key is None or r[key] == value)]
            train, purge = purge_training_bases(train, test, group_by_base)
            matched, matching = match_test_events(test, entries, tolerances)
            splits[task][name] = dict(train_ids=[r['id'] for r in train], test_ids=[r['id'] for r in test],
                                     purge=purge, matching=matching)
            fold = {}
            for family in design['feature_families']:
                result = fit_probe(train, test, family)
                if result['status'] == 'ESTIMATED_FEASIBILITY_ONLY':
                    result['accuracy_interval'] = accuracy_bootstrap(result['predictions'])
                    if all(n >= 2 for n in matching['groups_per_class'].values()):
                        lookup = {p['id']: p for p in result['predictions']}
                        predictions = [lookup[r['id']] for r in matched]
                        result['matched'] = dict(status='ESTIMATED_FEASIBILITY_ONLY',
                            metrics=score_predictions(matched, [p['probability'] for p in predictions]),
                            predictions=predictions, accuracy_interval=accuracy_bootstrap(predictions))
                    else:
                        result['matched'] = dict(status='UNAVAILABLE', reason='Fewer than two metadata-matched image families per class')
                fold[family] = result
            primary = fold['source_specific']
            for subset in ('full', 'matched'):
                target = primary if subset == 'full' else primary.get('matched', {})
                if 'predictions' not in target: continue
                comparisons = {}
                for baseline in ('layout_baseline', 'global_visual'):
                    reference = fold[baseline] if subset == 'full' else fold[baseline].get('matched', {})
                    if 'predictions' in reference:
                        comparisons[baseline] = accuracy_bootstrap(target['predictions'], paired_reference=reference['predictions'])
                target['paired_baseline_comparisons'] = comparisons
            results[task][name] = fold
            print(task, name, {f: r['status'] for f, r in fold.items()}, flush=True)
    write_json(OUT/'monitor_feasibility/grouped_splits.json', splits, freeze=True)
    write_json(OUT/'monitor_feasibility/probe_results.json', results, freeze=True)
    write_json(OUT/'monitor_feasibility/feature_ablation.json', dict(primary='source_specific',
               families=design['feature_families'], hyperparameter_search=False,
               primary_results={task: value['primary'] for task, value in results.items()},
               oracle_readout_cannot_establish_online_readiness=True), freeze=True)
    write_json(OUT/'monitor_feasibility/calibration.json', {task: {family: result.get('metrics', {}).get('calibration')
               for family, result in folds['primary'].items()} for task, folds in results.items()}, freeze=True)
    assert sha(freeze_path) == signature['labels_freeze_sha256']
    write_json(dest/'run_summary.json', dict(completed=True, seconds=time.time()-started,
               event_features=len(features), tasks=len(results), no_hyperparameter_search=True,
               labels_unchanged=True, result_sha256=sha(OUT/'monitor_feasibility/probe_results.json')))


if __name__ == '__main__':
    main()
