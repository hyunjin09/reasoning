"""Compose retained native reports across preserved and completed worker runs.

The original report formatting and semantic statistics stay unchanged. Each
worker is checked against its recorded allocation, including the protected
pre-migration MathWild prefix. This module cannot release or select a pilot.
"""
import argparse
from itertools import combinations

from scripts.stage7a.common import ROOT, read_json, sha
from scripts.stage7a_bench.completed_screen_v7 import load_completed_screen
from scripts.stage7a_bench.mmmu_behavioral_partitions_v6 import summarize_pairs
from scripts.stage7a_bench.native_report_v2 import (
    dimension_summary, identity, paired_transitions, write_report)

OUT = ROOT / 'outputs/stage7a_bench_v2'
REPORT_DEPENDENCIES = ('native_report_v6.py', 'native_report_v2.py',
    'completed_screen_v7.py', 'reviewed_units_v5.py', 'native_yield_v2.py',
    'mmmu_behavioral_partitions_v6.py')


def mmmu_behavior(receipt, bindings, compatibility):
    """Use the pre-native paired universe; never select pairs by their answers."""
    groups = receipt['reviews']
    specs = compatibility['frozen_conditions']
    if (compatibility.get('status') != 'PRE_NATIVE_PROTOCOL_COMPATIBILITY_AUDIT' or
            compatibility.get('benchmark') != 'mmmu_pro' or set(specs) != set(groups)):
        raise ValueError('MMMU requires its separate pre-native protocol audit')
    for condition, spec in specs.items():
        if (spec['manifest'] != bindings[condition]['manifest'] or
                receipt['artifact_sha256'].get(spec['manifest']) != spec['sha256']):
            raise ValueError('Behavioral protocol does not bind the completed frozen manifests')
    expected = set(compatibility['paired_base_ids'])
    if any({r['base_id'] for r in groups[c]} != expected
           for c in ('silent_no_image', 'explicit_guess')):
        raise ValueError('Completed no-image conditions differ from the pre-native paired universe')
    return summarize_pairs(groups, compatibility['paired_base_ids'], receipt['family_map'])


def build_report(benchmark, report_id, bindings, request_hashes):
    identity(benchmark)
    identity(report_id)
    receipt = load_completed_screen(benchmark, bindings)
    hashes = dict(receipt['artifact_sha256'])
    for name, digest in request_hashes.items():
        if name in hashes and hashes[name] != digest:
            raise ValueError('Request provenance conflicts with completed screen')
        hashes[name] = digest

    def read(path):
        path = (ROOT / path).resolve()
        if not path.is_relative_to(OUT):
            raise ValueError('Native report evidence outside active stage')
        name, digest = str(path.relative_to(ROOT)), sha(path)
        if name in hashes and hashes[name] != digest:
            raise ValueError('Native evidence changed during report assembly')
        hashes[name] = digest
        return read_json(path)

    original_path = OUT / 'config/runtime.json'
    original = read(original_path)
    groups, conditions, runs = receipt['reviews'], {}, {}
    for condition, binding in bindings.items():
        reviews = groups[condition]
        conditions[condition] = dict(native=receipt['screen'][condition],
            dimensions=dimension_summary(reviews),
            reviewed_unique_bases=len({r['base_id'] for r in reviews}),
            reviewed_unique_families=len({receipt['family_map'][r['base_id']] for r in reviews}))
        for owner in binding['runs']:
            run = owner['native_run_id']
            if run not in runs:
                base = OUT / 'native_screen/generations' / run
                env, signature, mechanics = [read(base / (name+'.json'))
                    for name in ('environment', 'signature', 'mechanics')]
                preserved = bool(owner.get('preserved_prefix'))
                runtime_path = original_path if preserved else OUT / 'config/runtime_node02_v3.json'
                runtime_name = str(runtime_path.relative_to(ROOT))
                if (not preserved and signature.get('runtime_config') != runtime_name or
                        signature.get('dependencies', {}).get(runtime_name) != sha(runtime_path)):
                    raise ValueError('Worker must bind its actual historical runtime')
                runtime = read(runtime_path)
                if any(runtime.get(k) != original[k] for k in
                       ('model_checkpoint', 'locked_generation_protocol')):
                    raise ValueError('Migration cannot change the frozen model or generation protocol')
                if not preserved and runtime.get('original_runtime') != dict(
                        path=str(original_path.relative_to(ROOT)), sha256=sha(original_path)):
                    raise ValueError('Operational runtime lost the original configuration binding')
                expected = dict(model_checkpoint_resolved=runtime['model_checkpoint'],
                    parameter_dtype='torch.bfloat16', architecture='Qwen3VLForConditionalGeneration',
                    parameter_count=4437815808, language_layers=36, attention_heads=32,
                    max_new_tokens=runtime['locked_generation_protocol']['max_new_tokens'], world_size=1,
                    slurm_job_id=runtime['runtime']['slurm_allocation'])
                if (any(env.get(k) != v for k, v in expected.items()) or
                        env.get('node', '').split('.')[0] != runtime['runtime']['node'] or
                        env.get('sys_prefix') != str(ROOT / '.venv') or
                        signature.get('slurm_job_id') != env['slurm_job_id']):
                    raise ValueError('Native model, BF16, environment or recorded allocation differs')
                checks = mechanics.get('checks')
                if (mechanics.get('cap') != 128 or not isinstance(checks, list) or not checks or
                        any(c.get('repeat_token_ids_exact') is not True or
                            c.get('scientific_use') is not False for c in checks)):
                    raise ValueError('Native preflight mechanics did not pass')
                runs[run] = dict(environment=env, runtime_config=runtime_name,
                    preserved_prefix=preserved,
                    mechanics=dict(cap=128, passed=True, scientific_use=False,
                        checked_conditions=sorted({c['input']['condition'] for c in checks})),
                    scope='Native preflight only; causal-prefix mechanics remain separate.')
            if condition not in runs[run]['mechanics']['checked_conditions']:
                raise ValueError('Worker condition lacks a native preflight check')
    pairs = {a+'__'+b:paired_transitions(groups[a], groups[b])
             for a, b in combinations(sorted(groups), 2)}
    behavioral = {}
    if benchmark == 'mmmu_pro':
        protocol = read(OUT / 'audit/mmmu_bclean_frozen_protocol_compatibility_v1.json')
        official = protocol['official_protocol']
        source = (ROOT / official['path']).resolve()
        if (not source.is_relative_to(OUT / 'cohort/provenance') or
                sha(source) != official['sha256'] or
                hashes.get(str(source.relative_to(ROOT)), official['sha256']) != official['sha256']):
            raise ValueError('Pinned original MMMU protocol changed')
        hashes[str(source.relative_to(ROOT))] = official['sha256']
        behavioral['local_mmmu_behavior'] = mmmu_behavior(receipt, bindings, protocol)
    for name in REPORT_DEPENDENCIES:
        path = ROOT / 'scripts/stage7a_bench' / name
        hashes[str(path.relative_to(ROOT))] = sha(path)
    for name, digest in hashes.items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or sha(path) != digest:
            raise ValueError('Report evidence changed or is outside workspace')
    return dict(status='COMPLETED_BENCHMARK_NATIVE_REPORT_ONLY', report_id=report_id,
        benchmark=benchmark, conditions=conditions, paired_conditions=pairs, native_runs=runs,
        **behavioral,
        artifact_sha256=hashes, verified_generated_event_ids=receipt['generated_event_ids'],
        analysis_family_map=receipt['family_map'], unit_provenance=receipt['unit_provenance'],
        causal_states_assigned=False, pilot_selected=False, primary_benchmark_selected=False,
        scope='Complete retained frozen 4B-Thinking native conditions across verified original runs. '
            'Final accuracy, local errors, binding, caveats, truncation and unknown judgments stay separate. '
            'Paired comparisons use common bases and preserve source families. No-image correctness is '
            'neither PRIOR_FILL nor causal nonvisual reasoning. F0 and correct singleton claims are '
            'screening candidates, not causal certificates. Annotation minutes remain unavailable. '
            'Pilot admission, causal scores and final benchmark recommendation remain separate.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    args = parser.parse_args()
    path = (ROOT / args.request).resolve()
    if not path.is_relative_to(OUT / 'native_screen/report_requests'):
        raise ValueError('Report request outside the active stage request directory')
    request = read_json(path)
    if (request.get('status') != 'NATIVE_REPORT_REQUEST' or
            request.get('causal_or_passive_scores_used') is not False):
        raise ValueError('Explicit native-only report request required')
    report = build_report(request['benchmark'], request['report_id'], request['bindings'],
                          {str(path.relative_to(ROOT)):sha(path)})
    print(write_report(report))


if __name__ == '__main__':
    main()
