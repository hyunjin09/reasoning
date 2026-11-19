"""Deterministically parse one completed frozen split; preserve every sign."""
import argparse
import numpy as np
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl, sha
from visual_reasoning.stage7a.metrics import compile_metrics


def native_convergence(entry, native_rows):
    """Require separately reviewed emitted evidence under all three conditions."""
    from scripts.stage7a.annotation_helpers import normalized_value
    expected = normalized_value(entry['reviewed_claim']['readout'])
    ledger = {}
    for condition in ('mask', 'unrelated', 'no_image'):
        eid = entry['base_id']+'__'+condition
        path = OUT / 'annotations/native_reviews' / (eid+'.json')
        if eid not in native_rows or not path.exists():
            ledger[condition] = dict(valid=False, reason='Condition or native semantic review unavailable')
            continue
        review = read_json(path)
        selected = [c for c in review['claims'] if c['kind'] == 'primary' and c['demand'] == 'singleton']
        valid = bool(len(selected) == 1 and normalized_value(selected[0]['readout']) == expected)
        ledger[condition] = dict(valid=valid, behavior=review['behavior'],
                                 readouts=[c['readout'] for c in selected], review_sha256=sha(path))
    return dict(converges=all(r['valid'] for r in ledger.values()), conditions=ledger,
                rule='Same explicit demanded-source native evidence under mask, unrelated image and no image; abstention, hypothetical values and demand-task mismatch do not count')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--split', choices=['discovery', 'confirmation'], required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    manifest = OUT / 'config' / (args.split+'_events.jsonl')
    certificate = read_json(OUT / 'audit' / (args.split+'_events.json'))
    assert certificate['status'] == 'FROZEN' and certificate['manifest_sha256'] == sha(manifest)
    run = OUT / 'raw' / args.run_id
    summary = read_json(run / 'run_summary.json')
    signature = read_json(run / 'signature.json')
    assert summary['completed'] and summary['mechanics'] is False and summary['split'] == args.split
    assert signature['manifest_sha256'] == sha(manifest)
    if args.split == 'confirmation':
        assert sha(OUT / 'config/discovery_thresholds.json') == signature['threshold_sha256']
    native_rows = {r['event_id']: r for r in read_jsonl(OUT / 'cohort/native_manifest.jsonl')}
    rows = []
    for entry in read_jsonl(manifest):
        path = run / 'events' / (entry['id']+'.json')
        result = read_json(path)
        assert result['complete'] and result['manifest_sha256'] == sha(manifest)
        with np.load(path.with_suffix('.npz')) as distributions:
            metrics = compile_metrics(entry, result, distributions)
        metrics['native_convergence'] = native_convergence(entry, native_rows)
        metrics.update(raw_result_path=str(path.relative_to(ROOT)), raw_result_sha256=sha(path),
                       raw_distributions_sha256=sha(path.with_suffix('.npz')))
        rows.append(metrics)
    dest = OUT / 'causal' / (args.split+'_event_metrics.jsonl')
    write_jsonl(dest, rows, freeze=True)
    write_json(OUT / 'audit' / (args.split+'_causal_metrics.json'),
               dict(completed=True, rows=len(rows), raw_run=args.run_id, manifest_sha256=sha(manifest),
                    metrics_sha256=sha(dest), code_sha256=sha(__file__),
                    metric_module_sha256=sha(ROOT / 'code/visual_reasoning/stage7a/metrics.py'),
                    passive_features_used=False), freeze=True)
    print(args.split, len(rows), 'causal metric rows compiled with raw provenance; no labels inferred here.')


if __name__ == '__main__':
    main()
