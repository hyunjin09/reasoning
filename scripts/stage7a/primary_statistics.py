"""Five prospectively specified families, without effect-selected cohorts."""
from collections import defaultdict
import numpy as np
from scripts.stage7a.common import OUT, read_json, read_jsonl, write_json, sha
from visual_reasoning.stage7a.statistics import directional_summary, holm_within_family


def contrasts(entries, metrics, thresholds):
    rows = {str(i): defaultdict(list) for i in range(1, 6)}
    names = {'1': ['T_minus_X_VSD', 'T_minus_I_VSD', 'T_semantic'],
             '2': ['prior_JS_convergence', 'prior_margin_convergence', 'prior_top50_convergence', 'T_semantic_loss_intact_to_strong'],
             '3': ['X_EP_token', 'X_EP_margin', 'X_semantic', 'X_minus_T_EP_margin'],
             '4': ['P_EP_claim', 'P_EP_token', 'P_EP_margin'],
             '5': ['extraction_T_minus_X_EP_margin', 'integration_T_minus_X_VSD', 'integration_T_semantic']}
    for family, tests in names.items():
        for name in tests: rows[family][name] = []
    availability_semantics = defaultdict(lambda: defaultdict(list))
    representative = {}
    for entry in entries:
        claim = entry['reviewed_claim']
        if entry['readout_type'] != 'V' or claim['demand'] != 'singleton': continue
        metric = metrics[entry['id']]
        def effect(source, key):
            return metric['source_effects'].get(source+'_W2', {}).get(key)
        def semantic(source):
            return metric['semantic_effects'].get(source, {}).get('net_semantic_beyond_sham')
        def subtract(a, b):
            return None if a is None or b is None else a-b
        def add(family, name, value, reference=entry):
            if value is not None:
                rows[family][name].append(dict(id=reference['id'], base_id=reference['base_id'],
                                              group_id=reference['group_id'], value=float(value)))
        independent = entry['source_separation_valid']
        if independent and claim['locally_correct'] and claim['kind'] == 'primary' and entry['condition'] == 'intact':
            add('1', 'T_minus_X_VSD', subtract(effect('T', 'VSD'), effect('X', 'VSD')))
            add('1', 'T_minus_I_VSD', subtract(effect('T', 'VSD'), effect('I', 'VSD')))
            add('1', 'T_semantic', semantic('T'))
        if claim['kind'] == 'primary':
            if entry['condition'] in ('strong', 'mask', 'unrelated', 'no_image'):
                pairs = [p for key, p in metric['distribution_similarity'].items()
                         if set(key.split('__')) <= {'mask', 'unrelated', 'no_image'}]
                if len(pairs) == 3:
                    add('2', 'prior_JS_convergence', thresholds['prior_js_max']-max(p['JS_nats'] for p in pairs))
                    add('2', 'prior_margin_convergence', thresholds['prior_margin_max']-max(p['absolute_candidate_margin_difference'] for p in pairs))
                    add('2', 'prior_top50_convergence', min(p['top50_overlap'] for p in pairs)-thresholds['prior_top50_min'])
            if entry['condition'] in ('intact', 'strong') and semantic('T') is not None:
                availability_semantics[entry['base_id']][entry['condition']].append(semantic('T'))
                representative[entry['base_id']] = entry
        if independent and not claim['locally_correct'] and claim['kind'] != 'aba_return':
            add('3', 'X_EP_token', effect('X', 'EP_token'))
            add('3', 'X_EP_margin', effect('X', 'EP_margin'))
            add('3', 'X_semantic', semantic('X'))
            add('3', 'X_minus_T_EP_margin', subtract(effect('X', 'EP_margin'), effect('T', 'EP_margin')))
        if independent and claim['kind'] == 'aba_return' and entry['source_aliases'].get('P') == 'X':
            for key in ('EP_claim', 'EP_token', 'EP_margin'): add('4', 'P_'+key, effect('X', key))
        if independent and not claim['locally_correct'] and entry['condition'] in ('intact', 'strong', 'sham_mask'):
            add('5', 'extraction_T_minus_X_EP_margin', subtract(effect('T', 'EP_margin'), effect('X', 'EP_margin')))
        downstream = entry.get('downstream_review') or {}
        if (independent and claim['locally_correct'] and downstream.get('integration_error_eligible') is True and
                downstream.get('later_error') is True and downstream.get('error_char_start', -1) > claim['readout_char_end']):
            add('5', 'integration_T_minus_X_VSD', subtract(effect('T', 'VSD'), effect('X', 'VSD')))
            add('5', 'integration_T_semantic', semantic('T'))
    for base, conditions in availability_semantics.items():
        if 'intact' in conditions and 'strong' in conditions:
            reference = representative[base]
            rows['2']['T_semantic_loss_intact_to_strong'].append(dict(id=reference['id'], base_id=base,
                group_id=reference['group_id'], value=float(np.mean(conditions['intact'])-np.mean(conditions['strong']))))
    return {family: holm_within_family({name: directional_summary(values) for name, values in tests.items()})
            for family, tests in rows.items()}


def main():
    freeze = read_json(OUT/'labels/label_freeze.json')
    assert freeze['frozen'] and freeze['passive_features_used_for_labels'] is False
    manifest = OUT/'config/confirmation_events.jsonl'
    assert sha(manifest) == freeze['events_manifest_sha256']['confirmation']
    metric_path = OUT/'causal/confirmation_event_metrics.jsonl'
    assert sha(metric_path) == freeze['causal_metrics_sha256']['confirmation']
    entries = read_jsonl(manifest)
    metrics = {m['id']: m for m in read_jsonl(metric_path)}
    thresholds = read_json(OUT/'config/discovery_thresholds.json')
    protocol = OUT/'config/primary_contrast_operationalization.json'
    assert read_json(protocol)['frozen_before_scientific_scores']
    write_json(OUT/'analysis/primary_statistics.json', dict(split='confirmation',
               code_sha256=sha(__file__), protocol_sha256=sha(protocol), manifest_sha256=sha(manifest), metrics_sha256=sha(metric_path),
               causal_labels_used_for_selection=False, families=contrasts(entries, metrics, thresholds)), freeze=True)
    datasets = sorted({e['dataset'] for e in entries})
    write_json(OUT/'analysis/dataset_primary_contrasts.json', dict(role='secondary descriptive dataset robustness',
               primary_discoveries_are_only_the_pooled_prespecified_tests=True,
               datasets={dataset: contrasts([e for e in entries if e['dataset'] == dataset], metrics, thresholds)
                         for dataset in datasets}), freeze=True)
    print('Five confirmatory families parsed without causal-state selection; dataset stratification saved.')


if __name__ == '__main__':
    main()
