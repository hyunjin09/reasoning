"""Apply discovery rules unchanged, then close the causal-label boundary."""
from collections import Counter
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl, sha
from visual_reasoning.stage7a.classification import classify


def main():
    thresholds_path = OUT/'config/discovery_thresholds.json'
    thresholds = read_json(thresholds_path)
    assert thresholds['frozen'] and thresholds['confirmation_used'] is False
    assert thresholds['classifier_sha256'] == sha(ROOT/'code/visual_reasoning/stage7a/classification.py')
    all_states, manifests, metrics_hashes = [], {}, {}
    for split in ('discovery', 'confirmation'):
        manifest = OUT/'config'/(split+'_events.jsonl')
        certificate = read_json(OUT/'audit'/(split+'_events.json'))
        assert certificate['status'] == 'FROZEN' and certificate['manifest_sha256'] == sha(manifest)
        metric_path = OUT/'causal'/(split+'_event_metrics.jsonl')
        metric_audit = read_json(OUT/'audit'/(split+'_causal_metrics.json'))
        assert metric_audit['completed'] and metric_audit['metrics_sha256'] == sha(metric_path)
        assert metric_audit['manifest_sha256'] == sha(manifest)
        signature = read_json(OUT/'raw'/metric_audit['raw_run']/'signature.json')
        if split == 'confirmation': assert signature['threshold_sha256'] == sha(thresholds_path)
        metrics = {m['id']: m for m in read_jsonl(metric_path)}
        entries = read_jsonl(manifest)
        assert set(metrics) == {e['id'] for e in entries}
        states = []
        for entry in entries:
            m = metrics[entry['id']]
            state = classify(entry, m, thresholds,
                             native_prior_convergence=m['native_convergence']['converges'])
            state.update(**{k: entry[k] for k in ('event_id', 'base_id', 'group_id', 'split',
                         'dataset', 'cohort', 'condition', 'template_family')},
                         claim_kind=entry['reviewed_claim']['kind'],
                         demand=entry['reviewed_claim']['demand'],
                         downstream_review=entry['downstream_review'],
                         evidence_manifest=str(manifest.relative_to(ROOT)),
                         metric_path=str(metric_path.relative_to(ROOT)),
                         thresholds_sha256=sha(thresholds_path))
            states.append(state)
        write_jsonl(OUT/'labels'/(split+'_states.jsonl'), states, freeze=True)
        all_states.extend(states)
        manifests[split] = sha(manifest)
        metrics_hashes[split] = sha(metric_path)
    paths = []
    for name, selected in [('tier1_states', [s for s in all_states if s['tier'] == 1]),
                           ('tier2_states', [s for s in all_states if s['tier'] == 2]),
                           ('unresolved', [s for s in all_states if s['state'] == 'UNRESOLVED'])]:
        path = OUT/'labels'/(name+'.jsonl')
        write_jsonl(path, selected, freeze=True)
        paths.append(path)
    paths += [OUT/'labels'/(split+'_states.jsonl') for split in ('discovery', 'confirmation')]
    counts = {}
    for split in ('discovery', 'confirmation', 'all'):
        selected = [s for s in all_states if split == 'all' or s['split'] == split]
        counts[split] = {name: dict(events=sum(s['state'] == name for s in selected),
                            bases=len({s['base_id'] for s in selected if s['state'] == name}),
                            independent_families=len({s['group_id'] for s in selected if s['state'] == name}),
                            tier1_events=sum(s['state'] == name and s['tier'] == 1 for s in selected),
                            strong_tier2_events=sum(s['state'] == name and s.get('strong_tier2', False) for s in selected))
                         for name in sorted(set(read_json(OUT/'config/state_taxonomy.json')['states']) | {'UNRESOLVED'})}
    counts_path = OUT/'labels/state_counts.json'
    write_json(counts_path, dict(counts=counts, sampling='Controlled stress cohort; not natural prevalence',
               unresolved_includes_separate_binding_diagnostics=True), freeze=True)
    paths.append(counts_path)
    write_json(OUT/'labels/label_freeze.json', dict(frozen=True,
               events_manifest_sha256=manifests, causal_metrics_sha256=metrics_hashes,
               labels_sha256={str(p.relative_to(ROOT)): sha(p) for p in paths},
               thresholds_sha256=sha(thresholds_path), passive_features_used_for_labels=False,
               classifier_sha256=thresholds['classifier_sha256'], code_sha256=sha(__file__)), freeze=True)
    print('Causal labels frozen:', dict(Counter(s['state'] for s in all_states)))


if __name__ == '__main__':
    main()
