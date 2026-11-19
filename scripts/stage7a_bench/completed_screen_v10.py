"""Read completed MMLong v9 evidence with explicit predecessor and OOM checks.

The original v7 reader remains authoritative for the other retained benchmarks.
This adapter preserves the full document denominator and actual artifact owners.
It neither changes native evidence nor admits a causal pilot.
"""
from pathlib import Path

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha
from scripts.stage7a_bench.completed_screen_v7 import (
    RETAINED, load_completed_screen as load_original_screen)
from scripts.stage7a_bench.causal_provenance_v2 import verified_families
from scripts.stage7a_bench.native_yield_v2 import indexed, summarize_condition
from scripts.stage7a_bench.reviewed_units_v5 import ordered_owners, verify_unit

OUT = ROOT / 'outputs/stage7a_bench_v2'


def validate_oom(result, row, review_present):
    if (row.get('preflight_status', 'ready') != 'ready' or review_present or
            result.get('unavailable') is not True or result.get('complete') is not False or
            result.get('unavailable_reason') != 'cuda_oom' or
            result.get('scientific_state') is not None or result.get('token_count') != 0 or
            any(result.get(k) is not None for k in
                ('generation_sha256', 'tokens_sha256', 'truncated', 'ended_with_eos')) or
            'CUDA out of memory' not in result.get('error', '')):
        raise ValueError('Runtime OOM must remain an evidenced, unreviewed resource exclusion')


def validate_environment(env, signature, mechanics, runtime, runtime_name, digest):
    expected = dict(model_checkpoint_resolved=runtime['model_checkpoint'],
        parameter_dtype='torch.bfloat16', architecture='Qwen3VLForConditionalGeneration',
        parameter_count=4437815808, language_layers=36, attention_heads=32,
        max_new_tokens=runtime['locked_generation_protocol']['max_new_tokens'], world_size=1,
        slurm_job_id=runtime['runtime']['slurm_allocation'])
    if (any(env.get(k) != v for k, v in expected.items()) or
            env.get('sys_prefix') != str(ROOT / '.venv') or
            env.get('node', '').split('.')[0] != runtime['runtime']['node'] or
            signature.get('slurm_job_id') != env['slurm_job_id'] or
            signature.get('runtime_config') != runtime_name or
            signature.get('dependencies', {}).get(runtime_name) != digest):
        raise ValueError('Historical owner model, BF16, allocation or runtime differs')
    checks = mechanics.get('checks')
    if (mechanics.get('cap') != 128 or not checks or
            any(c.get('repeat_token_ids_exact') is not True or
                c.get('scientific_use') is not False for c in checks) or
            'image_present' not in {c['input']['condition'] for c in checks}):
        raise ValueError('Historical owner lacks passing native document mechanics')


def resolve_owner(directory, ledger, event_id, digest):
    preserved = indexed(ledger['preserved'])
    if event_id in preserved:
        item = preserved[event_id]
        source = ROOT / item['source']
        expected = OUT / 'native_screen/generations' / ledger['predecessor_run_id'] / 'examples' / event_id
        if (source != expected or not directory.is_symlink() or
                directory.resolve() != expected.resolve() or item['result_sha256'] != digest):
            raise ValueError('Imported native artifact lost its explicit original owner/hash')
        return ledger['predecessor_run_id']
    if directory.is_symlink():
        raise ValueError('Native link lacks a predecessor import record')
    return directory.parent.parent.name


def load_completed_screen(benchmark, bindings):
    if benchmark != 'mmlongbench_doc':
        return load_original_screen(benchmark, bindings)
    if set(bindings) != {'image_present'}:
        raise ValueError('MMLong requires its single complete frozen native condition')
    hashes, runtime_runs, wrappers = {}, {}, {}

    def path(name, root=OUT):
        p = ROOT / name
        if not p.resolve().is_relative_to(root.resolve()):
            raise ValueError('Evidence outside its allowed stage directory')
        return p

    def read(p, lines=False, text=False):
        p = path(p, ROOT)
        key, digest = str(p.relative_to(ROOT)), sha(p)
        if key in hashes and hashes[key] != digest:
            raise ValueError('Evidence changed during completed-screen verification')
        hashes[key] = digest
        return p.read_text() if text else read_jsonl(p) if lines else read_json(p)

    spec = read(OUT / 'cohort/sample_freeze.json')['native_screen']['mmlongbench_doc_image_present']
    manifest = path(bindings['image_present']['manifest'], OUT / 'cohort/benchmark_manifests')
    rows = read(manifest, True)
    if (manifest != ROOT / spec['manifest'] or sha(manifest) != spec['sha256'] or
            len(rows) != spec['count'] or any(r['benchmark'] != benchmark or
                r['condition'] != 'image_present' for r in rows)):
        raise ValueError('MMLong manifest differs from its historical freeze')
    runs = indexed(bindings['image_present']['runs'], 'native_run_id')
    owners = ordered_owners([r['event_id'] for r in rows],
                           {k: v['event_ids'] for k, v in runs.items()})
    execution_path = OUT / 'config/mmlongbench_doc_execution_v9.json'
    execution = read(execution_path)
    dispatch = read(OUT / 'raw/mmlongbench_doc_parallel_v9/dispatch.json')
    batches = indexed(dispatch['batches'], 'run_id')
    if (dispatch['plan_sha256'] != sha(execution_path) or set(batches) != set(runs) or
            any(b['status'] != 'succeeded' or b.get('exit_code') != 0 for b in batches.values())):
        raise ValueError('Finite MMLong dispatch must finish exactly its bound batches')
    runtime_name = 'outputs/stage7a_bench_v2/config/runtime_node02_v3.json'
    runtime = read(ROOT / runtime_name)
    original_path = OUT / 'config/runtime.json'
    original = read(original_path)
    if (any(runtime[k] != original[k] for k in ('model_checkpoint', 'locked_generation_protocol')) or
            runtime.get('original_runtime') != dict(path=str(original_path.relative_to(ROOT)),
                                                    sha256=sha(original_path))):
        raise ValueError('Operational runtime lost the unchanged scientific protocol')

    def native_runtime(run):
        if run in runtime_runs:
            return
        base = OUT / 'native_screen/generations' / run
        env, signature, mechanics = [read(base / (k+'.json'))
                                     for k in ('environment', 'signature', 'mechanics')]
        validate_environment(env, signature, mechanics, runtime, runtime_name, sha(ROOT / runtime_name))
        runtime_runs[run] = dict(environment=env, runtime_config=runtime_name,
            mechanics=dict(cap=128, passed=True, scientific_use=False, checked_conditions=['image_present']))

    summaries, labels, ledgers = {}, {}, {}
    for run, info in runs.items():
        if Path(run).name != run or run in ('.', '..'):
            raise ValueError('Unsafe native run identity')
        base = path(OUT / 'native_screen/generations' / run)
        sig = read(base / 'signature.json')
        summary = read(base / 'run_summary.json')
        wrapper = read(OUT / 'raw' / run / 'run_summary.json')
        wrappers[run] = wrapper
        ledger = ledgers[run] = read(base / 'predecessor_import.json')
        if (sig['event_ids'] != info['event_ids'] or
                sig['manifests'].get(spec['manifest']) != sha(manifest) or
                summary.get('completed') is not True or wrapper.get('completed') is not True or
                wrapper.get('exit_code') != 0 or wrapper['plan_sha256'] != sha(execution_path) or
                ledger['predecessor_run_id'] != batches[run]['predecessor_run_id'] or
                ledger['source_execution'] != execution['predecessor_execution']):
            raise ValueError('Continuation batch ownership/completion differs')
        for name, digest in sig['dependencies'].items():
            p = path(name, ROOT)
            if sha(p) != digest:
                raise ValueError('Historical native dependency changed: '+name)
            hashes[name] = digest
        pred_plan = read(path(ledger['source_execution']['path'], OUT / 'config'))
        if sha(ROOT / ledger['source_execution']['path']) != ledger['source_execution']['sha256']:
            raise ValueError('Predecessor execution hash differs')
        old = ledger['predecessor_run_id']
        if ledger['predecessor_status'] != 'pending':
            old_wrapper = read(OUT / 'raw' / old / 'run_summary.json')
            wrappers[old] = old_wrapper
            old_signature = read(OUT / 'native_screen/generations' / old / 'signature.json')
            if (old_signature['event_ids'] != info['event_ids'] or
                    old_signature['manifests'].get(spec['manifest']) != sha(manifest) or
                    old_wrapper['plan_sha256'] != ledger['source_execution']['sha256']):
                raise ValueError('Original predecessor ownership differs')
            native_runtime(old)
        elif ledger['preserved'] or ledger['runtime_oom']:
            raise ValueError('Unstarted predecessor cannot supply artifacts')
        summaries[run] = indexed(summary['results'])
        if set(summaries[run]) != set(info['event_ids']):
            raise ValueError('Completed batch result coverage differs')
        labels[run] = indexed(read(path(info['review_path'], OUT / 'native_screen/manual_reviews'), True))
        if not set(labels[run]) <= set(info['event_ids']):
            raise ValueError('Review outside its batch')
        if (base / 'environment.json').exists():
            native_runtime(run)
        elif set(indexed(ledger['preserved'])) != set(info['event_ids']):
            raise ValueError('Missing continuation runtime requires complete explicit reuse')

    results, reviews, provenance, source_owners = [], [], [], {}
    for index, (event_id, run) in enumerate(owners):
        row = rows[index]
        directory = path(OUT / 'native_screen/generations' / run / 'examples' / event_id)
        result = read(directory / 'result.json')
        if (read(directory / 'manifest_row.json') != row or result != summaries[run][event_id] or
                any(result.get(k) != row[k] for k in ('event_id', 'base_id', 'benchmark', 'condition'))):
            raise ValueError('Completed native row/result identity differs')
        owner = resolve_owner(directory, ledgers[run], event_id, sha(directory / 'result.json'))
        source_owners[event_id] = owner
        results.append(result)
        if result.get('unavailable'):
            if result.get('unavailable_reason') == 'cuda_oom':
                validate_oom(result, row, event_id in labels[run])
                failure = result.get('predecessor_failure')
                if failure:
                    if event_id not in ledgers[run]['runtime_oom']:
                        raise ValueError('Imported OOM absent from import ledger')
                    log = path(failure['log_path'], ROOT / 'runs/stage7a_bench')
                    wrapper = path(failure['wrapper_path'], OUT / 'raw')
                    if sha(log) != failure['log_sha256'] or sha(wrapper) != failure['wrapper_sha256']:
                        raise ValueError('Imported OOM evidence hash differs')
                    if 'torch.OutOfMemoryError: CUDA out of memory.' not in read(log, text=True):
                        raise ValueError('Imported OOM lacks native failure trace')
                    if read(wrapper)['exit_code'] == 0:
                        raise ValueError('Imported OOM wrapper did not fail')
                else:
                    error = directory / 'oom_error.json'
                    read(error)
                    attempts = wrappers[run]['process_attempts']
                    if (sha(error) != result.get('oom_error_sha256') or not any(
                            a['exit_code'] == 75 and event_id in set(a['terminal_events_after'])-
                            set(a['terminal_events_before']) for a in attempts)):
                        raise ValueError('Runtime OOM lacks its recorded failing process attempt')
            elif (row.get('preflight_status', 'ready') == 'ready' or
                    result.get('unavailable_reason') != row['preflight_status'] or event_id in labels[run]):
                raise ValueError('Unavailable input changed its frozen reason or gained a review')
            continue
        if event_id not in labels[run] or owner not in runtime_runs:
            raise ValueError('Generated response lacks full review or actual owner runtime')
        meta, generation = read(directory / 'input.json'), read(directory / 'generation.json')
        tokens = read(directory / 'tokens.jsonl', True)
        if (any(meta.get(k) != row[k] for k in
                ('document_path', 'document_sha256', 'renderer_version', 'render_scale')) or
                [p['physical_page'] for p in meta['visual_images']] != list(range(1, row['page_count']+1))):
            raise ValueError('Native document hash/rendering or full physical page order differs')
        review = labels[run][event_id]
        verify_unit(row=row, index=index, manifest_sha256=sha(manifest), result=result, review=review,
            meta=meta, generation=generation, tokens=tokens,
            generation_sha256=sha(directory / 'generation.json'), tokens_sha256=sha(directory / 'tokens.jsonl'))
        reviews.append(review)
        provenance.append(dict(event_id=event_id, native_run_id=run, review_path=runs[run]['review_path']))
    family = verified_families(read(OUT / 'audit/native_source_family_integrity.json'),
                              spec['manifest'], sha(manifest), benchmark)
    screen = summarize_condition(rows, results, reviews)
    if not screen['screen_complete']:
        raise ValueError('MMLong semantic/native coverage incomplete')
    return dict(screen={'image_present': screen}, frozen_counts={'image_present': len(rows)},
        family_map=family, generated_event_ids=[r['event_id'] for r in reviews],
        reviews={'image_present': reviews}, unit_provenance=provenance, artifact_sha256=hashes,
        native_runs=runtime_runs, wrappers=wrappers, artifact_owners=source_owners,
        scope='Complete native MMLong v9, explicit predecessor owners and resource exclusions; no pilot admission')
