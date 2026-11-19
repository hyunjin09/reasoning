"""Export one completed frozen pilot using the unchanged causal definitions.

This CPU-only parser requires complete scientific and actual4B mechanics runs,
revalidates membership and every raw artifact, and preserves absent controls.
Requested fresh native controls must be reviewed before labels are exported.
No thresholds, pilot membership, or benchmark ranking are selected here.
"""
import argparse
import math
from pathlib import Path
import re

import numpy as np

from scripts.stage7a.common import ROOT, read_json, sha, write_json, write_jsonl
from scripts.stage7a_bench.causal_provenance_v2 import stage_path
from scripts.stage7a_bench.causal_metrics_v11 import compile_benchmark_metrics, classify_benchmark
from scripts.stage7a_bench.causal_run_v15 import validate_mechanics
from scripts.stage7a_bench.control_provenance_v11 import load_reviewed_controls
from scripts.stage7a_bench.pilot_freeze_v15 import load_frozen_pilot, dependency_hashes
from scripts.stage7a_bench.prior_controls_v11 import load_prior_controls, requested_native_banks

OUT = ROOT / 'outputs/stage7a_bench_v2'


def positive_seconds(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def validate_completion(signature, summary, wrapper, environment, expected_signature,
                        runtime, event_ids, *, mechanics):
    if (signature.get('execution_signature') != expected_signature or
            signature.get('mechanics') is not mechanics or signature.get('mode') is not None or
            signature.get('event_ids') != event_ids or not event_ids or
            len(set(event_ids)) != len(event_ids) or
            signature.get('passive_features_collected') is not False or
            summary.get('completed') is not True or summary.get('mechanics') is not mechanics or
            summary.get('passive_features_collected') is not False or
            not positive_seconds(summary.get('seconds')) or
            not isinstance(summary.get('events'), list) or len(summary['events']) != len(event_ids)):
        raise ValueError('Run is incomplete or differs from frozen scientific scope')
    if (wrapper.get('completed') is not True or type(wrapper.get('exit_code')) is not int or
            wrapper['exit_code'] != 0 or
            any(record.get('slurm_job_id') != runtime['slurm_allocation']
                for record in (wrapper, environment)) or
            environment.get('parameter_dtype') != 'torch.bfloat16' or
            environment.get('node', '').split('.')[0] != runtime['node']):
        raise ValueError('Run lacks successful wrapper or exact BF16 allocation provenance')


def validate_event_identity(entry, result, pilot_sha256):
    fields = ('id', 'event_id', 'base_id', 'benchmark', 'condition',
              'analysis_family_id', 'pilot_stratum')
    required_checks = {'all_finite', 'native_input_exact', 'local_control_input_geometry_exact',
                       'local_controls_all_finite', 'fixed_prior_inputs_verified',
                       'fixed_prior_scores_finite'}
    if (any(result.get(k) != entry[k] for k in fields) or
            result.get('pilot_sha256') != pilot_sha256 or result.get('complete') is not True or
            result.get('source_assay_mechanics') is not False or
            result.get('passive_features_collected') is not False or
            any(result.get('checks', {}).get(k) is not True for k in required_checks) or
            any(v is not True for v in result['checks'].values()) or
            not positive_seconds(result.get('seconds'))):
        raise ValueError('Scientific event identity, completion or elapsed time is invalid')


def checked_artifact(reference, expected):
    expected = expected.resolve()
    path = stage_path(reference['path'], 'causal_pilot/raw')
    if path != expected or sha(path) != reference['sha256']:
        raise ValueError('Raw event/distribution is swapped or changed')
    return path


def run_records(run):
    wrapper = stage_path(OUT / 'causal_pilot/wrappers' / (run.name + '.json'),
                         'causal_pilot/wrappers')
    paths = dict(signature=run / 'signature.json', summary=run / 'run_summary.json',
                 environment=run / 'environment.json', wrapper=wrapper)
    return {k: read_json(p) for k, p in paths.items()}, {
        k: dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for k, p in paths.items()}


def validate_distributions(distributions, local_names, prior_names):
    expected = {'N'} | {n for n in local_names if n.endswith('_sham')} | set(prior_names)
    if set(distributions) != expected:
        raise ValueError('Distributions do not cover exactly the frozen native/control roles')
    shape = distributions['N'].shape
    if len(shape) != 1 or shape[0] <= 50:
        raise ValueError('Expected complete one-dimensional vocabulary distributions')
    if any(a.shape != shape or not np.issubdtype(a.dtype, np.floating) or
           not np.isfinite(a).all() for a in distributions.values()):
        raise ValueError('Nonfinite, nonnumeric or differently shaped vocabulary distributions')


def compile_run(run_id, tokenizer, convergence_references=None):
    if not re.fullmatch('[a-z0-9_]+', run_id):
        raise ValueError('Unsafe run identity')
    convergence_references = {} if convergence_references is None else convergence_references
    run = stage_path(OUT / 'causal_pilot/raw' / run_id, 'causal_pilot/raw')
    records, receipt = run_records(run)
    signature = records['signature']
    pilot_ref = signature['execution_signature']['pilot']
    pilot = load_frozen_pilot(pilot_ref, tokenizer)
    entries = pilot['selected_entries']
    config_path = OUT / 'config/runtime_node02_two_gpu_v15.json'
    config = read_json(config_path)
    expected = dict(pilot=pilot_ref, dependencies=dependency_hashes(), runtime_sha256=sha(config_path))
    validate_completion(signature, records['summary'], records['wrapper'], records['environment'],
                        expected, config['runtime'], [e['id'] for e in entries], mechanics=False)
    certificate_ref = signature['mechanics_certificate']
    certificate_path = stage_path(certificate_ref['path'], 'causal_pilot/mechanics')
    if (certificate_path.name != pilot['benchmark'] + '.json' or
            sha(certificate_path) != certificate_ref['sha256']):
        raise ValueError('Actual4B mechanics certificate changed or belongs to another benchmark')
    certificate = read_json(certificate_path)
    mechanics_id = validate_mechanics(certificate, expected, entries)
    mechanics_event = stage_path(certificate['artifacts']['event']['path'], 'causal_pilot/raw')
    mechanics_run = mechanics_event.parent.parent
    mechanical, mechanics_receipt = run_records(mechanics_run)
    validate_completion(mechanical['signature'], mechanical['summary'], mechanical['wrapper'],
        mechanical['environment'], expected, config['runtime'], [mechanics_id], mechanics=True)
    if mechanical['summary']['events'] != [{k: certificate['artifacts'][k]
                                           for k in ('event', 'distributions')}]:
        raise ValueError('Completed mechanics summary differs from certificate artifacts')
    requested = requested_native_banks(entries)
    if set(convergence_references) != set(requested):
        raise ValueError('Every requested fresh native bank needs one review; unrequested banks are rejected')
    thresholds = read_json(ROOT / 'outputs/stage7a/config/discovery_thresholds.json')
    frozen = read_json(OUT / 'config/inherited_causal_definition_freeze.json')
    if (thresholds.get('frozen') is not True or
            any(thresholds.get(k) != v for k, v in frozen['numeric_thresholds'].items())):
        raise ValueError('Inherited numeric thresholds differ from the frozen definitions')
    destination = OUT / 'causal_pilot/compiled' / pilot['benchmark'] / run_id
    if destination.exists():
        raise FileExistsError('Preserve the existing compiled pilot')
    metric_rows, labels, costs, raw_receipts = [], [], [], []
    for entry, reference in zip(entries, records['summary']['events']):
        event_path = checked_artifact(reference['event'], run / 'events' / (entry['id'] + '.json'))
        array_path = checked_artifact(reference['distributions'], event_path.with_suffix('.npz'))
        result = read_json(event_path)
        validate_event_identity(entry, result, pilot_ref['sha256'])
        local, local_provenance = load_reviewed_controls(entry)
        prior, prior_provenance = load_prior_controls(entry)
        if (set(result['controls']) != set(local) | set(prior) or
                result.get('control_provenance') != local_provenance or
                result.get('fixed_prior_controls') != prior_provenance or
                result.get('semantic_controls_available') is not bool(local)):
            raise ValueError('Scored controls differ from the frozen reviewed banks')
        with np.load(array_path, allow_pickle=False) as data:
            distributions = {k: data[k] for k in data.files}
            validate_distributions(distributions, local, prior)
            metrics = compile_benchmark_metrics(entry, result, distributions)
        metrics.update(raw_result=reference['event'], raw_distributions=reference['distributions'])
        label = classify_benchmark(entry, metrics, thresholds,
                                   native_convergence_reference=convergence_references.get(entry['id']))
        label.update(**{k: entry[k] for k in ('event_id', 'base_id', 'benchmark', 'condition',
            'analysis_family_id', 'pilot_stratum', 'native_index')}, pilot=pilot_ref,
            thresholds_retuned=False, passive_features_used=False)
        metric_rows.append(metrics)
        labels.append(label)
        costs.append(dict(id=entry['id'], seconds=result['seconds'],
            peak_gpu_allocated_bytes=result.get('peak_gpu_allocated_bytes'),
            peak_host_rss_kib=result.get('peak_host_rss_kib')))
        raw_receipts.append(reference)
    # Detect changes during parsing before writing any derived scientific output.
    if expected['dependencies'] != dependency_hashes():
        raise ValueError('Implementation changed during compilation')
    for reference in [pilot_ref, certificate_ref, *receipt.values(), *mechanics_receipt.values(),
                      *convergence_references.values(), *[v for r in raw_receipts for v in r.values()]]:
        if sha(ROOT / reference['path']) != reference['sha256']:
            raise ValueError('Evidence changed during compilation')
    destination.mkdir(parents=True, exist_ok=False)
    paths = dict(metrics=destination / 'event_metrics.jsonl', states=destination / 'state_labels.jsonl',
                 resources=destination / 'event_resources.jsonl')
    for name, values in [('metrics', metric_rows), ('states', labels), ('resources', costs)]:
        write_jsonl(paths[name], values, freeze=True)
    summary = dict(status='COMPLETED_FROZEN_PILOT_COMPILED', benchmark=pilot['benchmark'],
        run_id=run_id, events=len(entries), native_bases=len({e['base_id'] for e in entries}),
        source_families=len({e['analysis_family_id'] for e in entries}), pilot=pilot_ref,
        raw_run=receipt, mechanics=mechanics_receipt, mechanics_certificate=certificate_ref,
        native_convergence_reviews=convergence_references, execution_signature=expected,
        outputs={k: dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for k, p in paths.items()},
        parser_sha256=sha(Path(__file__)), metrics_adapter_sha256=sha(Path(__file__).with_name('causal_metrics_v11.py')),
        scientific_run_seconds=records['summary']['seconds'],
        mechanics_run_seconds=mechanical['summary']['seconds'],
        event_seconds_sum=sum(c['seconds'] for c in costs),
        native_screen_and_native_control_costs_included=False, annotation_minutes=None,
        thresholds_retuned=False, passive_features_used=False, ranking_selected=False,
        scope='All frozen pilot events, including unresolved states and unavailable controls. '
              'Repeated native bases are not independent examples. No benchmark winner is chosen.')
    write_json(destination / 'compilation.json', summary, freeze=True)
    return summary


def main():
    from transformers import AutoTokenizer
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--convergence-map')
    args = parser.parse_args()
    mapping = None
    if args.convergence_map:
        mapping = read_json(stage_path(args.convergence_map, 'causal_pilot/native_control_reviews'))
    tokenizer = AutoTokenizer.from_pretrained(
        read_json(OUT / 'config/runtime_node02_two_gpu_v15.json')['model_checkpoint'], local_files_only=True)
    result = compile_run(args.run_id, tokenizer, mapping)
    print(result['status'], result['benchmark'], result['events'])


if __name__ == '__main__':
    main()
