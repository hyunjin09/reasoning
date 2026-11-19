"""Export a completed benchmark's native behavior, without selecting a pilot.

The completed-screen loader verifies wrappers, frozen rows, full responses,
semantic reviews and source families. Local dimensions remain separate from
final accuracy and from the mutually exclusive F screening label. These files
are inputs to the final cross-benchmark figures, not a causal certificate.
"""
import argparse
from collections import Counter
from itertools import combinations
from pathlib import Path
import re

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.completed_screen_v2 import load_completed_screen
from scripts.stage7a_bench.native_yield_v2 import indexed, paired_comparison, rate

OUT = ROOT / 'outputs/stage7a_bench_v2'


def identity(name):
    if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9_]+', name):
        raise ValueError('Safe lowercase report and benchmark identities required')
    return name


def truth(value):
    if value is None:
        return 'unknown'
    if type(value) is not bool:
        raise ValueError('Correctness requires an explicit boolean or unknown')
    return 'correct' if value else 'wrong'


def dimension_summary(reviews):
    def has_singleton(row, correct):
        values = [c['locally_correct'] for c in row['claims'] if c['demand'] == 'singleton']
        if any(v is correct for v in values):
            return True
        return None if any(v is None for v in values) else False

    binding = [None if r['binding_claim_present'] is not True or
               r['binding_claim_correctness'] is None else not r['binding_claim_correctness']
               for r in reviews]
    joint = Counter(truth(r['final_correctness'])+' / '+truth(r['local_visual_claim_correctness'])
                    for r in reviews)
    return dict(binding_error_among_adjudicated_bindings=rate(binding),
        responses_with_correct_singleton=rate([has_singleton(r, True) for r in reviews]),
        responses_with_wrong_singleton=rate([has_singleton(r, False) for r in reviews]),
        final_local_contingency=dict(joint),
        scope='Claim-existence rates can overlap within a response; a correct local read in an F1 response '
              'is retained. They do not certify source geometry, fresh demand, eligibility or causal faithfulness. '
              'Binding errors use the reviewed binding dimension, not just the F2 screen label.')


def paired_transitions(left, right):
    a, b = indexed(left, 'base_id'), indexed(right, 'base_id')
    common = sorted(set(a) & set(b))
    report = paired_comparison(left, right)
    report.update(screen_class_transitions=dict(Counter(
        (a[k]['screen_label'] or 'unknown')+' → '+(b[k]['screen_label'] or 'unknown') for k in common)),
        final_correctness_transitions=dict(Counter(
            truth(a[k]['final_correctness'])+' → '+truth(b[k]['final_correctness']) for k in common)),
        unpaired_left=len(a)-len(common), unpaired_right=len(b)-len(common))
    return report


def verify_hashes(hashes):
    for name, digest in hashes.items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT.resolve()):
            raise ValueError('Report evidence outside the project workspace')
        if sha(path) != digest:
            raise ValueError('Report evidence changed: '+name)


def remember_hash(hashes, path):
    name, digest = str(path.relative_to(ROOT)), sha(path)
    if name in hashes and hashes[name] != digest:
        raise ValueError('Report evidence changed during loading: '+name)
    hashes[name] = digest


def validate_runtime(environment, signature, mechanics, runtime, runtime_sha):
    expected = dict(model_checkpoint_resolved=runtime['model_checkpoint'],
        parameter_dtype='torch.bfloat16', architecture='Qwen3VLForConditionalGeneration',
        parameter_count=4437815808, language_layers=36, attention_heads=32,
        max_new_tokens=runtime['locked_generation_protocol']['max_new_tokens'], world_size=1,
        slurm_job_id=runtime['runtime']['slurm_allocation'])
    if (any(environment.get(k) != v for k, v in expected.items()) or
            environment.get('node', '').split('.')[0] != runtime['runtime']['node'] or
            environment.get('sys_prefix') != str(ROOT / '.venv') or
            signature.get('slurm_job_id') != environment['slurm_job_id'] or
            signature.get('dependencies', {}).get('outputs/stage7a_bench_v2/config/runtime.json') != runtime_sha):
        raise ValueError('Native model, BF16, project environment or frozen runtime differs')
    checks = mechanics.get('checks')
    if (mechanics.get('cap') != 128 or not isinstance(checks, list) or not checks or
            any(c.get('repeat_token_ids_exact') is not True or c.get('scientific_use') is not False
                for c in checks)):
        raise ValueError('Native preflight mechanics did not pass')


def build_report(benchmark, report_id, bindings, request_hashes):
    identity(benchmark)
    identity(report_id)
    receipt = load_completed_screen(benchmark, bindings)
    hashes = dict(receipt['artifact_sha256'])
    for name, digest in request_hashes.items():
        if name in hashes and hashes[name] != digest:
            raise ValueError('Request provenance conflicts with completed screen')
        hashes[name] = digest
    runtime_path = OUT / 'config/runtime.json'
    runtime = read_json(runtime_path)
    remember_hash(hashes, runtime_path)
    groups, conditions, runs = {}, {}, {}
    for condition, binding in bindings.items():
        review_path = (ROOT / binding['review_path']).resolve()
        groups[condition] = read_jsonl(review_path)
        conditions[condition] = dict(native=receipt['screen'][condition],
            dimensions=dimension_summary(groups[condition]),
            reviewed_unique_bases=len({r['base_id'] for r in groups[condition]}),
            reviewed_unique_families=len({receipt['family_map'][r['base_id']] for r in groups[condition]}))
        run = binding['native_run_id']
        if run in runs:
            continue
        base = OUT / 'native_screen/generations' / run
        records = {}
        for name in ('environment', 'signature', 'mechanics'):
            path = base / (name+'.json')
            records[name] = read_json(path)
            remember_hash(hashes, path)
        validate_runtime(records['environment'], records['signature'], records['mechanics'],
                         runtime, sha(runtime_path))
        runs[run] = dict(environment=records['environment'],
            mechanics=dict(cap=128, passed=True, scientific_use=False,
                checked_conditions=sorted({c['input']['condition'] for c in records['mechanics']['checks']})),
            scope='Native generation preflight; not the separate causal-prefix/assay mechanics certificate.')
    for condition, binding in bindings.items():
        if condition not in runs[binding['native_run_id']]['mechanics']['checked_conditions']:
            raise ValueError('Frozen condition lacks a native preflight check')
    pairs = {a+'__'+b: paired_transitions(groups[a], groups[b])
             for a, b in combinations(sorted(groups), 2)}
    for name in ('native_report_v2.py', 'completed_screen_v2.py', 'native_yield_v2.py'):
        path = ROOT / 'scripts/stage7a_bench' / name
        remember_hash(hashes, path)
    verify_hashes(hashes)
    return dict(status='COMPLETED_BENCHMARK_NATIVE_REPORT_ONLY', report_id=report_id,
        benchmark=benchmark, conditions=conditions, paired_conditions=pairs, native_runs=runs,
        artifact_sha256=hashes, verified_generated_event_ids=receipt['generated_event_ids'],
        analysis_family_map=receipt['family_map'], causal_states_assigned=False,
        pilot_selected=False, primary_benchmark_selected=False,
        scope='Completed frozen 4B-Thinking native conditions only. Final accuracy, local evidence, '
              'binding, caveats, truncation and unknown judgments remain separate. Paired comparisons '
              'use common base IDs only and retain shared source families. Behavioral agreement is not '
              'causal nonvisual correctness or PRIOR_FILL. Screening classes and correct singleton '
              'claims do not establish pilot eligibility. Annotation minutes remain unavailable. '
              'The overall sweep, causal pilots, ranking and final recommendation are separate requirements.')


def format_rate(metric):
    if metric['value'] is None:
        return f"Unknown ({metric['unknown']} unadjudicated)"
    return (f"{metric['numerator']}/{metric['denominator']} ({metric['value']:.1%}; "
            f"{metric['unknown']} unadjudicated)")


def write_report(report):
    name = identity(report['report_id'])
    identity(report['benchmark'])
    if (report.get('status') != 'COMPLETED_BENCHMARK_NATIVE_REPORT_ONLY' or
            report.get('causal_states_assigned') is not False or
            report.get('primary_benchmark_selected') is not False):
        raise ValueError('Native report cannot assign causal states or a benchmark winner')
    dest = OUT / 'native_screen/reports' / name
    if not dest.resolve().is_relative_to(OUT / 'native_screen/reports'):
        raise ValueError('Report destination resolves outside the active report directory')
    if dest.exists():
        raise FileExistsError('Preserve immutable native report: '+str(dest))
    verify_hashes(report['artifact_sha256'])
    lines = ['# '+report['benchmark']+' completed native screen', '', report['scope'], '']
    fields = [('Final accuracy', 'final_accuracy'), ('Local error, adjudicated claims', 'local_visual_error_rate'),
        ('Unsupported claims', 'unsupported_claim_rate'), ('F0 screening candidates', 'faithful_control_candidate_rate'),
        ('Later integration-error candidates', 'integration_error_candidate_rate'),
        ('Any caveat', 'abstention_or_caveat_rate'), ('Truncation', 'truncation_rate')]
    for condition, record in report['conditions'].items():
        native, dimensions = record['native'], record['dimensions']
        lines += ['## '+condition, '',
            f"Frozen: {native['frozen']}; generated/reviewed: {native['generated']}/{native['reviewed']}; "
            f"unavailable: {native['unavailable']}. Verified source families: {record['reviewed_unique_families']}.", '',
            '| Measure | Count / rate |', '|---|---:|']
        lines += [f'| {title} | {format_rate(native[key])} |' for title, key in fields]
        for title, key in [('Binding error, adjudicated bindings', 'binding_error_among_adjudicated_bindings'),
                           ('Any correct singleton claim', 'responses_with_correct_singleton'),
                           ('Any wrong singleton claim', 'responses_with_wrong_singleton')]:
            lines.append(f'| {title} | {format_rate(dimensions[key])} |')
        lines += ['', dimensions['scope'], '']
    if report['paired_conditions']:
        lines += ['## Paired behavior', '', '| Conditions | Common reviewed bases | Final-correctness disagreement |', '|---|---:|---:|']
        for name, pair in report['paired_conditions'].items():
            lines.append(f"| {name} | {pair['paired_reviewed']} | {format_rate(pair['final_correctness_disagreement'])} |")
        lines += ['', 'Unknown judgments and unmatched bases are preserved in report.json. '
            'No behavioral or causal cleaning protocol is inferred from this table.', '']
    lines += ['Exact rates, transitions, reviewed claim excerpts, provenance and qualifications: [report.json](report.json).', '']
    dest.mkdir(parents=True, exist_ok=False)
    write_json(dest / 'report.json', report)
    (dest / 'summary.md').write_text('\n'.join(lines))
    return dest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    args = parser.parse_args()
    path = (ROOT / args.request).resolve()
    if not path.is_relative_to(OUT / 'native_screen/report_requests'):
        raise ValueError('Report request must be inside the active-stage request directory')
    request = read_json(path)
    if request.get('status') != 'NATIVE_REPORT_REQUEST' or request.get('causal_or_passive_scores_used') is not False:
        raise ValueError('Explicit native-only report request required')
    report = build_report(request['benchmark'], request['report_id'], request['bindings'],
                          {str(path.relative_to(ROOT)): sha(path)})
    print('COMPLETED_BENCHMARK_NATIVE_REPORT_ONLY', write_report(report))


if __name__ == '__main__':
    main()
