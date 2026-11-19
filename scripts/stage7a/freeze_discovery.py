"""Freeze numerical rules from a completed discovery causal run only."""
import argparse
import numpy as np
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl, sha
from visual_reasoning.stage7a.metrics import distribution_similarity
from visual_reasoning.stage7a.thresholds import calibrate, matching_tolerances


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    protocol_path = OUT/'config/threshold_calibration_protocol.json'
    protocol = read_json(protocol_path)
    assert protocol['frozen_before_scientific_scores']
    assert protocol['module_sha256'] == sha(ROOT/'code/visual_reasoning/stage7a/thresholds.py')
    manifest = OUT/'config/discovery_events.jsonl'
    certificate = read_json(OUT/'audit/discovery_events.json')
    assert certificate['status'] == 'FROZEN' and certificate['manifest_sha256'] == sha(manifest)
    run = OUT/'raw'/args.run_id
    signature, summary = read_json(run/'signature.json'), read_json(run/'run_summary.json')
    assert summary['completed'] and summary['split'] == 'discovery' and not summary['mechanics']
    assert signature['manifest_sha256'] == sha(manifest)
    metrics_path = OUT/'causal/discovery_event_metrics.jsonl'
    metrics = {m['id']: m for m in read_jsonl(metrics_path)}
    entries = read_jsonl(manifest)
    controls = []
    for entry in entries:
        assert entry['split'] == metrics[entry['id']]['split'] == 'discovery'
        if entry['readout_type'] != 'V' or entry['reviewed_claim']['demand'] != 'singleton':
            continue
        metric = metrics[entry['id']]
        record = dict(id=entry['id'], base_id=entry['base_id'], group_id=entry['group_id'], split='discovery')
        irrelevant = metric['source_effects'].get('I_W2')
        if irrelevant:
            record['irrelevant_abs_vsd'] = abs(irrelevant['VSD'])
            record['irrelevant_abs_claim_effect'] = abs(irrelevant['EP_claim'])
            wrong = [abs(irrelevant[k]) for k in ('EP_token', 'EP_margin') if irrelevant.get(k) is not None]
            if wrong: record['irrelevant_abs_wrong_effect'] = max(wrong)
        semantic = metric['semantic_effects'].get('T')
        if semantic:
            record['sham_abs_semantic_shift'] = abs(semantic['sham_shift'])
            record['sham_abs_margin_change'] = abs(semantic['sham_D_change'])
            with np.load(run/'events'/(entry['id']+'.npz')) as distributions:
                same_content = distribution_similarity(distributions['N'], distributions['T_sham'])
            record.update(sham_js=same_content['JS_nats'], sham_top50_overlap=same_content['top50_overlap'])
        controls.append(record)
    thresholds, estimates = calibrate(controls)
    controls_path = OUT/'audit/discovery_calibration_controls.jsonl'
    write_jsonl(controls_path, controls, freeze=True)
    rules_path = OUT/'config/state_rule_operationalization_v2.json'
    assert read_json(rules_path)['code_sha256'] == sha(ROOT/'code/visual_reasoning/stage7a/classification.py')
    write_json(OUT/'config/discovery_thresholds.json', dict(frozen=True, **thresholds,
               calibration_estimates=estimates, protocol_sha256=sha(protocol_path),
               control_rows_sha256=sha(controls_path), manifest_sha256=sha(manifest),
               discovery_metrics_sha256=sha(metrics_path), discovery_raw_run=args.run_id,
               classifier_sha256=sha(ROOT/'code/visual_reasoning/stage7a/classification.py'),
               qualitative_rules_sha256=sha(rules_path), confirmation_used=False, passive_features_used=False,
               limitations='Operational conservative thresholds calibrated on small discovery control families; no optimization of state yield or probe accuracy.'), freeze=True)
    write_json(OUT/'config/matching_tolerances.json', dict(frozen=True,
               exact_keys=['dataset', 'cohort', 'condition', 'readout_type'],
               continuous=matching_tolerances(entries), manifest_sha256=sha(manifest),
               matching='Deterministic opposite-class pairs within held-out data, distinct image families, all metadata calipers satisfied; no causal magnitude or passive feature matching.',
               rule='Half discovery family IQR with fixed numerical minimum; unavailable matching is reported, never relaxed on confirmation.'), freeze=True)
    print('Discovery thresholds and matching tolerances frozen; confirmation and passive data unused.')


if __name__ == '__main__':
    main()
